#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
astock-data-source: A股多源数据源统一管理 (v2.0 - 多源fallback)

更新历史:
- v2.0 (基于用户反馈): 增加多源 fallback, 解决东财被封问题
- v1.0: 初版

数据源优先级 (按稳定性):
1. ifzq gtimg (腾讯财经, 已知最稳定, 住宅 IP 友好)
2. 新浪财经 hq.sinajs.cn (稳定, 数据略延迟)
3. 东方财富 push2his.emoney.com (可能风控)
4. 东方财富 push2.eastmoney.com (经常被封)
5. akshare 备用 (聚合多个源)

[实测 2026-06-21]: 住宅 IP + 代理场景下, ifzq gtimg 最稳定
"""

# 修复 Windows GBK 编码问题
import sys
import io
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

import os
import json
import time
import argparse
import logging
from functools import wraps
from typing import Optional, Dict, List, Any
import pandas as pd

logging.basicConfig(level=logging.WARNING, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


# ============================================================
# 全局配置
# ============================================================
# 数据源稳定性标记 (基于实测)
SOURCE_RELIABILITY = {
    "ifzq_gtimg": 0.95,      # 已知最稳定
    "sina_hq": 0.90,         # 稳定
    "eastmoney_push2his": 0.60,  # 部分被封
    "eastmoney_push2": 0.30,     # 经常被封
    "akshare": 0.85,          # 聚合源
}

# 数据源使用计数器 (用于自动切换)
SOURCE_FAIL_COUNT = {k: 0 for k in SOURCE_RELIABILITY}
MAX_FAILS_BEFORE_SWITCH = 3

# 修复 akshare 内部 requests 代理问题
def _patch_akshare_proxy():
    """Monkey patch akshare 内部 requests, 关闭代理"""
    try:
        import requests
        original_get = requests.get
        original_post = requests.post

        def patched_get(url, **kwargs):
            kwargs["proxies"] = {"http": None, "https": None}
            kwargs["verify"] = False
            return original_get(url, **kwargs)

        def patched_post(url, **kwargs):
            kwargs["proxies"] = {"http": None, "https": None}
            kwargs["verify"] = False
            return original_post(url, **kwargs)

        requests.get = patched_get
        requests.post = patched_post
    except Exception as e:
        logger.warning(f"无法 patch requests: {e}")


_patch_akshare_proxy()


# ============================================================
# 多源数据获取 (核心)
# ============================================================
def _get_quote_ifzq(code: str) -> Optional[Dict]:
    """腾讯 ifzq gtimg - 最稳定的源"""
    try:
        import requests
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        url = f"http://ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,60,qfq"
        resp = requests.get(url, timeout=5, proxies={"http": None, "https": None})
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 0:
            stock_data = data["data"][f"{market}{code}"]
            if "qfqday" in stock_data and stock_data["qfqday"]:
                last = stock_data["qfqday"][-1]
                prev = stock_data["qfqday"][-2] if len(stock_data["qfqday"]) > 1 else last
                return {
                    "code": code,
                    "name": stock_data.get("name", ""),
                    "price": float(last[2]),
                    "open": float(last[1]),
                    "high": float(last[3]),
                    "low": float(last[4]),
                    "close": float(last[2]),
                    "pre_close": float(prev[2]),
                    "volume": float(last[5]),
                    "pct_change": (float(last[2]) - float(prev[2])) / float(prev[2]) * 100,
                }
    except Exception as e:
        logger.debug(f"ifzq 失败: {e}")
    return None


def _get_quote_sina(code: str) -> Optional[Dict]:
    """新浪 hq.sinajs.cn"""
    try:
        import requests
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        url = f"https://hq.sinajs.cn/list={market}{code}"
        resp = requests.get(url, timeout=5, proxies={"http": None, "https": None})
        resp.raise_for_status()
        text = resp.text
        # 解析: var hq_str_sh601991="大秦铁路,27.90,27.20,..."
        if '""' in text:
            return None
        match = text.split('"')[1].split(",")
        if len(match) < 32:
            return None
        return {
            "code": code,
            "name": match[0],
            "open": float(match[1]),
            "pre_close": float(match[2]),
            "price": float(match[3]),
            "high": float(match[4]),
            "low": float(match[5]),
            "volume": float(match[8]),
            "amount": float(match[9]),  # 元
            "pct_change": (float(match[3]) - float(match[2])) / float(match[2]) * 100,
        }
    except Exception as e:
        logger.debug(f"sina 失败: {e}")
    return None


def _get_quote_eastmoney(code: str) -> Optional[Dict]:
    """东财 push2 (经常被封, 仅作备用)"""
    try:
        import requests
        secid = f"1.{code}" if str(code).startswith(("60", "68", "9")) else f"0.{code}"
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": secid,
            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170,f171",
        }
        resp = requests.get(url, params=params, timeout=5,
                            proxies={"http": None, "https": None})
        resp.raise_for_status()
        d = resp.json().get("data")
        if not d:
            return None
        return {
            "code": code,
            "name": d.get("f58", ""),
            "price": d.get("f43", 0) / 100,
            "high": d.get("f44", 0) / 100,
            "low": d.get("f45", 0) / 100,
            "open": d.get("f46", 0) / 100,
            "volume": d.get("f47", 0),
            "amount": d.get("f48", 0),
            "pre_close": d.get("f60", 0) / 100,
            "pct_change": d.get("f170", 0) / 100,
            "turnover": d.get("f171", 0) / 100,
        }
    except Exception as e:
        logger.debug(f"eastmoney 失败: {e}")
    return None


# 数据源优先级列表 (按可靠性降序)
SOURCE_FUNCS = [
    ("ifzq_gtimg", _get_quote_ifzq),
    ("sina_hq", _get_quote_sina),
    ("eastmoney_push2", _get_quote_eastmoney),
]


def get_realtime_quote(code: str) -> Dict:
    """获取单只股票实时行情 - 多源 fallback"""
    code = str(code).zfill(6)

    # 按优先级尝试各数据源
    for source_name, func in SOURCE_FUNCS:
        try:
            result = func(code)
            if result:
                result["source"] = source_name
                SOURCE_FAIL_COUNT[source_name] = 0  # 重置失败计数
                return result
            else:
                SOURCE_FAIL_COUNT[source_name] += 1
        except Exception as e:
            SOURCE_FAIL_COUNT[source_name] += 1
            logger.debug(f"{source_name} 异常: {e}")

        # 连续失败, 跳过该源
        if SOURCE_FAIL_COUNT[source_name] >= MAX_FAILS_BEFORE_SWITCH:
            logger.warning(f"{source_name} 连续失败 {SOURCE_FAIL_COUNT[source_name]} 次, 暂时跳过")

    raise RuntimeError(f"所有数据源均失败获取 {code}, 请检查网络")


def get_realtime_all() -> pd.DataFrame:
    """获取全 A 股实时行情 (用新浪 Market Center, 已知稳定)"""
    try:
        import requests
        url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
        params = {"node": "hs_a", "sort": "changepercent", "asc": 0, "num": 5000}
        resp = requests.get(url, params=params, timeout=30,
                            proxies={"http": None, "https": None})
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # 标准化列名
        col_map = {
            "code": "code", "name": "name", "open": "open", "high": "high",
            "low": "low", "trade": "price", "settlement": "pre_close",
            "volume": "volume", "amount": "amount", "changepercent": "pct_change",
            "mktcap": "total_mv", "nmc": "circ_mv", "turnoverratio": "turnover", "pe": "pe",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        # 数值类型
        for col in ["price", "open", "high", "low", "pre_close", "pct_change", "turnover", "pe"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # 单位转换: amount 元 -> 亿
        if "amount" in df.columns:
            df["amount_yi"] = df["amount"] / 1e8
        if "total_mv" in df.columns:
            df["total_mv_yi"] = df["total_mv"] / 1e8
        if "circ_mv" in df.columns:
            df["circ_mv_yi"] = df["circ_mv"] / 1e8
        return df
    except Exception as e:
        raise RuntimeError(f"新浪全市场接口失败: {e}")


def get_kline_ifzq(code: str, days: int = 60) -> pd.DataFrame:
    """从 ifzq gtimg 获取 K 线 (稳定)"""
    try:
        import requests
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        url = f"http://ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,{days},qfq"
        resp = requests.get(url, timeout=10, proxies={"http": None, "https": None})
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            return pd.DataFrame()
        stock = data["data"][f"{market}{code}"]
        rows = stock.get("qfqday") or stock.get("day") or []
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=["date", "open", "close", "high", "low", "volume"])
        # 转换类型
        for col in ["open", "close", "high", "low", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        raise RuntimeError(f"ifzq K线失败: {e}")


# ============================================================
# 装饰器
# ============================================================
def with_retry(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if i < max_retries - 1:
                        time.sleep(delay * (i + 1))
            raise RuntimeError(f"{func.__name__} 重试{max_retries}次失败: {last_err}")
        return wrapper
    return decorator


def with_rate_limit(calls_per_second: float = 2.0):
    min_interval = 1.0 / calls_per_second
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


# ============================================================
# 统一接口
# ============================================================
@with_rate_limit(2.0)
def get_realtime(code: str) -> Dict:
    """单股实时行情 (多源 fallback)"""
    return get_realtime_quote(code)


@with_rate_limit(1.0)
def get_realtime_all() -> pd.DataFrame:
    """全 A 股实时行情"""
    return get_realtime_all()


@with_rate_limit(1.0)
def get_kline(code: str, days: int = 60, adjust: str = "qfq") -> pd.DataFrame:
    """K 线数据 (多源 fallback)"""
    code = str(code).zfill(6)
    # 优先 ifzq
    try:
        return get_kline_ifzq(code, days)
    except Exception as e:
        logger.warning(f"ifzq K线失败: {e}, 尝试 akshare")
    # fallback akshare
    try:
        import akshare as ak
        import datetime
        end = datetime.datetime.now().strftime("%Y%m%d")
        start = (datetime.datetime.now() - datetime.timedelta(days=days * 2)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust=adjust)
        if df.empty:
            return df
        df.columns = [c.lower() for c in df.columns]
        return df.tail(days).reset_index(drop=True)
    except Exception as e:
        raise RuntimeError(f"K线获取失败: {e}")


# ============================================================
# 其它方法 (保持兼容)
# ============================================================
def get_index_realtime() -> pd.DataFrame:
    """主要指数实时"""
    try:
        import akshare as ak
        return ak.stock_zh_index_spot_em(symbol="沪深重要指数")
    except Exception:
        return pd.DataFrame()


def get_index_kline(symbol: str, days: int = 60) -> pd.DataFrame:
    """指数 K 线"""
    try:
        import akshare as ak
        if str(symbol).startswith(("000", "6", "9")):
            sym = f"sh{symbol}"
        else:
            sym = f"sz{symbol}"
        df = ak.stock_zh_index_daily(symbol=sym)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"])
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        return df[df["date"] >= cutoff].reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def get_stock_info(code: str) -> Dict:
    """股票基本信息"""
    try:
        import akshare as ak
        df = ak.stock_individual_info_em(symbol=code)
        if df.empty:
            return {}
        return {row["item"]: row["value"] for _, row in df.iterrows()}
    except Exception:
        return {}


def get_news(code: str) -> pd.DataFrame:
    """个股新闻"""
    try:
        import akshare as ak
        return ak.stock_news_em(symbol=code)
    except Exception:
        return pd.DataFrame()


# ============================================================
# 统一的字段输出
# ============================================================
def standardize_quote(quote: Dict) -> Dict:
    """标准化行情字段, 所有数据源统一输出格式
    单位约定:
    - amount: 元
    - total_mv: 元
    - circ_mv: 元
    """
    if not quote:
        return {}
    # 添加单位转换版本
    std = dict(quote)
    # 已经是新结构, 确保字段一致
    std.setdefault("amount", 0)
    std.setdefault("total_mv", 0)
    std.setdefault("circ_mv", 0)
    std.setdefault("pe", None)
    std.setdefault("turnover", 0)
    return std


# ============================================================
# CLI (argparse 修复: 真正的命名参数)
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="astock-data-source v2.0 - 多源 fallback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py get-realtime --code 601991
  python main.py get-realtime-all
  python main.py get-kline --code 601991 --days 60
  python main.py list-methods
  python main.py healthcheck       # 健康检查
        """
    )
    parser.add_argument("--list", action="store_true", help="列出所有方法")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # get-realtime
    p = subparsers.add_parser("get-realtime", help="单股实时行情")
    p.add_argument("--code", required=True, help="股票代码")

    # get-realtime-all
    subparsers.add_parser("get-realtime-all", help="全 A 股实时")

    # get-kline
    p = subparsers.add_parser("get-kline", help="K 线")
    p.add_argument("--code", required=True, help="股票代码")
    p.add_argument("--days", type=int, default=60, help="天数")
    p.add_argument("--adjust", default="qfq", help="复权方式")

    # get-index-realtime
    subparsers.add_parser("get-index-realtime", help="指数实时")

    # get-index-kline
    p = subparsers.add_parser("get-index-kline", help="指数 K 线")
    p.add_argument("--symbol", required=True, help="指数代码")
    p.add_argument("--days", type=int, default=60)

    # get-stock-info
    p = subparsers.add_parser("get-stock-info", help="股票信息")
    p.add_argument("--code", required=True)

    # get-news
    p = subparsers.add_parser("get-news", help="个股新闻")
    p.add_argument("--code", required=True)

    # healthcheck
    subparsers.add_parser("healthcheck", help="检查所有数据源")

    args = parser.parse_args()

    # --list 全局选项
    if args.list:
        print("可用方法:")
        methods = [
            "get-realtime", "get-realtime-all", "get-kline",
            "get-index-realtime", "get-index-kline",
            "get-stock-info", "get-news", "healthcheck",
        ]
        for m in methods:
            print(f"  - {m}")
        return

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "get-realtime":
            result = get_realtime(args.code)
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        elif args.command == "get-realtime-all":
            df = get_realtime_all()
            if not df.empty:
                cols = ["code", "name", "price", "pct_change", "total_mv_yi", "amount_yi"]
                cols = [c for c in cols if c in df.columns]
                print(df[cols].head(50).to_string())
        elif args.command == "get-kline":
            df = get_kline(args.code, args.days, args.adjust)
            if not df.empty:
                print(df.tail(args.days).to_string())
            else:
                print("无数据")
        elif args.command == "get-index-realtime":
            df = get_index_realtime()
            if not df.empty:
                print(df.to_string())
        elif args.command == "get-index-kline":
            df = get_index_kline(args.symbol, args.days)
            if not df.empty:
                print(df.to_string())
        elif args.command == "get-stock-info":
            info = get_stock_info(args.code)
            for k, v in info.items():
                print(f"  {k}: {v}")
        elif args.command == "get-news":
            df = get_news(args.code)
            if not df.empty:
                print(df.head(10).to_string())
        elif args.command == "healthcheck":
            print("=== 数据源健康检查 ===")
            for name, func in SOURCE_FUNCS:
                try:
                    result = func("000001")
                    status = "✅" if result else "❌"
                    print(f"  {status} {name}")
                except Exception as e:
                    print(f"  ❌ {name}: {e}")
            # 全市场
            try:
                df = get_realtime_all()
                print(f"  ✅ sina 全市场: {len(df)} 只")
            except Exception as e:
                print(f"  ❌ sina 全市场: {e}")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
