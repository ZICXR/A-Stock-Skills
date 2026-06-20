#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
astock-data-source: A股多源数据源统一管理
主入口脚本 - Claude Agent 可通过命令行调用
"""

import sys
import os
import json
import argparse
import logging
from functools import wraps
from typing import Optional, Dict, List, Any
import time
import pandas as pd

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


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
# 数据源实现
# ============================================================
class AkshareSource:
    """akshare 数据源 (主)"""

    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
        except ImportError:
            self.available = False
            logger.warning("akshare 未安装: pip install akshare")

    @with_retry()
    @with_rate_limit(2.0)
    def get_realtime_all(self) -> pd.DataFrame:
        return self.ak.stock_zh_a_spot_em()

    @with_retry()
    @with_rate_limit(1.0)
    def get_realtime(self, code: str) -> Dict:
        df = self.ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return {}
        return target.iloc[0].to_dict()

    @with_retry()
    @with_rate_limit(2.0)
    def get_kline(self, code: str, days: int = 60, adjust: str = "qfq") -> pd.DataFrame:
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        df = self.ak.stock_zh_a_hist(
            symbol=str(code).zfill(6),
            period="daily",
            start_date=start,
            end_date=end,
            adjust=adjust
        )
        if df.empty:
            return df
        df.columns = [c.lower() for c in df.columns]
        return df.tail(days).reset_index(drop=True)

    @with_retry()
    @with_rate_limit(2.0)
    def get_index_realtime(self) -> pd.DataFrame:
        return self.ak.stock_zh_index_spot_em(symbol="沪深重要指数")

    @with_retry()
    @with_rate_limit(1.0)
    def get_index_kline(self, symbol: str, days: int = 60) -> pd.DataFrame:
        from datetime import datetime
        if str(symbol).startswith(("000", "6")):
            sym = f"sh{symbol}"
        else:
            sym = f"sz{symbol}"
        df = self.ak.stock_zh_index_daily(symbol=sym)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"])
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        return df[df["date"] >= cutoff].reset_index(drop=True)

    @with_retry()
    @with_rate_limit(1.0)
    def get_stock_info(self, code: str) -> Dict:
        df = self.ak.stock_individual_info_em(symbol=str(code).zfill(6))
        if df.empty:
            return {}
        return {row["item"]: row["value"] for _, row in df.iterrows()}

    @with_retry()
    @with_rate_limit(1.0)
    def get_financial(self, code: str) -> pd.DataFrame:
        try:
            return self.ak.stock_financial_abstract_ths(symbol=code)
        except Exception:
            return self.ak.stock_financial_analysis_indicator(symbol=code)

    @with_retry()
    @with_rate_limit(1.0)
    def get_holders(self, code: str) -> pd.DataFrame:
        return self.ak.stock_main_holders_em(symbol=code)

    @with_retry()
    @with_rate_limit(1.0)
    def get_news(self, code: str) -> pd.DataFrame:
        return self.ak.stock_news_em(symbol=code)

    @with_retry()
    @with_rate_limit(1.0)
    def get_announcement(self, code: str) -> pd.DataFrame:
        return self.ak.stock_announcement_report(symbol=code)

    @with_retry()
    @with_rate_limit(1.0)
    def get_fund_flow(self, code: str) -> pd.DataFrame:
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        return self.ak.stock_individual_fund_flow(stock=code, market=market)

    @with_retry()
    @with_rate_limit(1.0)
    def get_sector_flow(self) -> pd.DataFrame:
        return self.ak.stock_sector_fund_flow_rank()

    @with_retry()
    @with_rate_limit(1.0)
    def get_zt_pool(self, date: Optional[str] = None) -> pd.DataFrame:
        if not date:
            from datetime import datetime
            date = datetime.now().strftime("%Y%m%d")
        return self.ak.stock_zt_pool_em(date=date)

    @with_retry()
    @with_rate_limit(1.0)
    def get_lhb(self, date: Optional[str] = None) -> pd.DataFrame:
        if not date:
            from datetime import datetime, timedelta
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return self.ak.stock_lhb_detail_em(start_date=date, end_date=date)

    @with_retry()
    @with_rate_limit(1.0)
    def get_north_bound(self) -> pd.DataFrame:
        return self.ak.stock_hsgt_fund_flow_summary_em()


class TushareSource:
    """tushare 数据源 (辅)"""

    def __init__(self):
        self.token = os.environ.get("TUSHARE_TOKEN")
        if not self.token:
            self.available = False
            return
        try:
            import tushare as ts
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            self.available = True
        except ImportError:
            self.available = False

    def get_realtime(self, code: str) -> Dict:
        if not self.available:
            return {}
        # tushare 实时数据需用其他接口
        return {}

    def get_kline(self, code: str, days: int = 60, adjust: str = "qfq") -> pd.DataFrame:
        if not self.available:
            return pd.DataFrame()
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        return self.pro.daily(ts_code=f"{code}.SH" if str(code).startswith("6") else f"{code}.SZ",
                              start_date=start, end_date=end)


# ============================================================
# 统一管理器
# ============================================================
class DataSourceManager:
    """数据源统一管理器"""

    def __init__(self):
        self.akshare = AkshareSource()
        self.tushare = TushareSource()
        self._cache = {}
        self._cache_ttl = 300  # 5 分钟

    def _cache_key(self, method, *args, **kwargs):
        return f"{method}:{args}:{sorted(kwargs.items())}"

    def _cache_get(self, key):
        if key in self._cache:
            value, ts = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return value
        return None

    def _cache_set(self, key, value):
        self._cache[key] = (value, time.time())

    def call(self, method_name: str, *args, **kwargs):
        """统一调用入口"""
        key = self._cache_key(method_name, *args, **kwargs)
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        # 优先 akshare
        if self.akshare.available and hasattr(self.akshare, method_name):
            try:
                method = getattr(self.akshare, method_name)
                result = method(*args, **kwargs)
                if result is not None and (not hasattr(result, "empty") or not result.empty):
                    self._cache_set(key, result)
                    return result
            except Exception as e:
                logger.warning(f"akshare {method_name} 失败: {e}")

        # 降级 tushare
        if self.tushare.available and hasattr(self.tushare, method_name):
            try:
                method = getattr(self.tushare, method_name)
                result = method(*args, **kwargs)
                if result is not None and (not hasattr(result, "empty") or not result.empty):
                    self._cache_set(key, result)
                    return result
            except Exception as e:
                logger.warning(f"tushare {method_name} 失败: {e}")

        raise RuntimeError(f"所有数据源 {method_name} 调用失败")

    # 便捷方法
    def get_realtime_all(self):
        return self.call("get_realtime_all")

    def get_realtime(self, code: str):
        return self.call("get_realtime", code)

    def get_kline(self, code: str, days: int = 60, adjust: str = "qfq"):
        return self.call("get_kline", code, days, adjust)

    def get_index_realtime(self):
        return self.call("get_index_realtime")

    def get_index_kline(self, symbol: str, days: int = 60):
        return self.call("get_index_kline", symbol, days)

    def get_stock_info(self, code: str):
        return self.call("get_stock_info", code)

    def get_financial(self, code: str):
        return self.call("get_financial", code)

    def get_holders(self, code: str):
        return self.call("get_holders", code)

    def get_news(self, code: str):
        return self.call("get_news", code)

    def get_announcement(self, code: str):
        return self.call("get_announcement", code)

    def get_fund_flow(self, code: str):
        return self.call("get_fund_flow", code)

    def get_sector_flow(self):
        return self.call("get_sector_flow")

    def get_zt_pool(self, date: Optional[str] = None):
        return self.call("get_zt_pool", date)

    def get_lhb(self, date: Optional[str] = None):
        return self.call("get_lhb", date)

    def get_north_bound(self):
        return self.call("get_north_bound")


# 全局单例
_manager = None


def get_source() -> DataSourceManager:
    """获取数据源管理器(单例)"""
    global _manager
    if _manager is None:
        _manager = DataSourceManager()
    return _manager


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="astock-data-source CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 列出所有方法
    subparsers.add_parser("--list", help="列出所有方法")

    # 通用方法调用
    subparsers.add_parser("get_realtime_all", help="全A股实时行情")
    p = subparsers.add_parser("get_realtime", help="单股实时")
    p.add_argument("code")
    p = subparsers.add_parser("get_kline", help="K线")
    p.add_argument("code")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--adjust", default="qfq", choices=["qfq", "hfq", ""])
    subparsers.add_parser("get_index_realtime", help="指数实时")
    p = subparsers.add_parser("get_index_kline", help="指数K线")
    p.add_argument("symbol")
    p.add_argument("--days", type=int, default=60)
    p = subparsers.add_parser("get_stock_info", help="股票信息")
    p.add_argument("code")
    p = subparsers.add_parser("get_financial", help="财务指标")
    p.add_argument("code")
    p = subparsers.add_parser("get_news", help="新闻")
    p.add_argument("code")
    p = subparsers.add_parser("get_announcement", help="公告")
    p.add_argument("code")
    subparsers.add_parser("get_zt_pool", help="涨停板")
    subparsers.add_parser("get_north_bound", help="北向资金")

    args = parser.parse_args()

    if args.command == "--list":
        methods = [
            "get_realtime_all", "get_realtime", "get_kline",
            "get_index_realtime", "get_index_kline",
            "get_stock_info", "get_financial", "get_holders",
            "get_news", "get_announcement", "get_fund_flow",
            "get_sector_flow", "get_zt_pool", "get_lhb", "get_north_bound"
        ]
        print("可用方法:")
        for m in methods:
            print(f"  - {m}")
        return

    if not args.command:
        parser.print_help()
        return

    # 调用方法
    source = get_source()
    method = getattr(source, args.command)
    if args.command in ("get_realtime", "get_kline", "get_index_kline",
                        "get_stock_info", "get_financial", "get_news",
                        "get_announcement", "get_fund_flow", "get_holders"):
        kwargs = {k: v for k, v in vars(args).items() if k not in ("command", "code", "symbol") and v is not None}
        if hasattr(args, "code") and args.code:
            result = method(args.code, **kwargs)
        elif hasattr(args, "symbol") and args.symbol:
            result = method(args.symbol, **kwargs)
    else:
        result = method()

    # 输出结果
    if isinstance(result, pd.DataFrame):
        if result.empty:
            print("(空数据)")
        else:
            print(result.to_string())
    elif isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(result)


if __name__ == "__main__":
    main()
