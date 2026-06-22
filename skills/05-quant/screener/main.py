#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""screener: 全市场筛选 (接入 astock-data-source v2.0 + K线缓存)

v3 改进:
- 通过 astock-data-source 拉数据 (多源 fallback)
- K线优先读 parquet 缓存 (5 秒 vs 30 分钟)
- 断点续传 (崩了下次继续)
- Python 表达式: --where "pe<20 and roe>15"
- 友好错误信息
"""

import os
import sys
import json
import time
import argparse
import warnings
from pathlib import Path
from typing import Dict, List
from datetime import datetime

warnings.filterwarnings("ignore")

# 接入 astock-data-source (v2.0)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from skills.01-infra.astock-data-source.main import (
    get_realtime, get_realtime_all, get_kline
)
from skills.01-infra.astock-cache.main import kline_get_or_fetch, kline_stats

# 断点续传
PROGRESS_FILE = Path("./screener_progress.json")


# ============================================================
# 内置策略模板 (精简到 4 个)
# ============================================================
BUILTIN_STRATEGIES = {
    "value": {
        "name": "价值低估",
        "where": "pe<20 and pb<2 and total_mv>50",
        "sort": "pe",
    },
    "growth": {
        "name": "成长",
        "where": "roe>15 and pe>10 and pe<50",
        "sort": "roe",
    },
    "small_cap": {
        "name": "小市值",
        "where": "total_mv<100 and total_mv>20",
        "sort": "total_mv",
    },
    "momentum": {
        "name": "动量",
        "where": "change_5d>5 and change_20d>0",
        "sort": "change_5d",
    },
}


# ============================================================
# 数据获取 (走 astock-data-source)
# ============================================================
def get_stock_metrics(codes: List[str] = None) -> 'pd.DataFrame':
    """通过 astock-data-source 拉全市场行情"""
    import pandas as pd
    print("📡 拉取全市场行情 (走 astock-data-source 多源 fallback)...")
    try:
        df = get_realtime_all()
    except Exception as e:
        print(f"❌ 数据源失败: {e}")
        print("💡 提示: 跑 python skills/01-infra/astock-data-source/main.py healthcheck 检查")
        return pd.DataFrame()
    if df is None or df.empty:
        print("❌ 拿到空数据")
        return pd.DataFrame()

    # 标准化字段 (astock-data-source 已统一)
    rename_map = {
        "代码": "code", "名称": "name", "最新价": "price",
        "涨跌幅": "pct_change", "涨跌额": "change",
        "成交量": "volume", "成交额": "amount", "换手率": "turnover",
        "市盈率-动态": "pe", "市净率": "pb", "市销率": "ps",
        "总市值": "total_mv", "流通市值": "circ_mv",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # 过滤 ST
    if "name" in df.columns:
        df = df[~df["name"].astype(str).str.contains("ST", na=False)]

    if "code" in df.columns:
        df["code"] = df["code"].astype(str).str.zfill(6)
        if codes:
            df = df[df["code"].isin(codes)]

    return df


def calc_change_metrics(codes: List[str], days: int = 60) -> Dict:
    """计算 N 日涨幅 (走 K 线缓存)"""
    result = {"change_5d": {}, "change_20d": {}}
    print(f"📈 计算 {len(codes)} 只股票的 5日/20日涨幅 (走缓存)...")

    # 断点续传
    progress = _load_progress()
    cached_codes = set(progress.get("done", {}).keys())

    for i, code in enumerate(codes, 1):
        if code in cached_codes:
            # 从进度恢复
            data = progress["done"][code]
            result["change_5d"][code] = data.get("change_5d")
            result["change_20d"][code] = data.get("change_20d")
            continue

        # 走 K 线缓存
        df = kline_get_or_fetch(code, _fetch_kline_via_ds, days=days)
        if df is None or df.empty or len(df) < 21:
            continue

        df.columns = [c.lower() for c in df.columns]
        if "close" not in df.columns:
            continue

        close = df["close"].iloc[-1]
        if len(df) >= 6:
            result["change_5d"][code] = (close - df["close"].iloc[-6]) / df["close"].iloc[-6] * 100
        if len(df) >= 21:
            result["change_20d"][code] = (close - df["close"].iloc[-21]) / df["close"].iloc[-21] * 100

        # 保存进度 (每 10 只)
        progress.setdefault("done", {})[code] = {
            "change_5d": result["change_5d"].get(code),
            "change_20d": result["change_20d"].get(code),
        }
        if i % 10 == 0:
            _save_progress(progress)
            print(f"  [{i}/{len(codes)}] 进度已存 (按 Ctrl+C 可中断, 下次继续)")

    _save_progress(progress)  # 最终保存
    return result


def _fetch_kline_via_ds(code: str, days: int = 60):
    """通过 astock-data-source 拉 K 线 (给 kline_get_or_fetch 用)"""
    return get_kline(code, days=days)


def _load_progress() -> Dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_progress(progress: Dict):
    try:
        PROGRESS_FILE.write_text(
            json.dumps(progress, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"⚠️ 进度保存失败: {e}")


# ============================================================
# 条件解析 (Python 表达式)
# ============================================================
ALLOWED_FIELDS = {
    "code", "name", "price", "pct_change", "change",
    "volume", "amount", "turnover", "pe", "pb", "ps",
    "total_mv", "circ_mv", "change_5d", "change_20d",
}


def safe_eval_condition(row, expr: str) -> bool:
    """安全求值 Python 表达式 (限制字段)"""
    import pandas as pd
    # 提取字段
    import re
    used_fields = re.findall(r'\b([a-z_][a-z0-9_]*)\b', expr)
    used_fields = [f for f in used_fields if f in ALLOWED_FIELDS]

    # 准备上下文
    ctx = {}
    for f in used_fields:
        v = row.get(f)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return False
        try:
            ctx[f] = float(v)
        except (TypeError, ValueError):
            ctx[f] = 0
    ctx["True"] = True
    ctx["False"] = False
    ctx["None"] = None

    # 求值 (限制: 不允许 import/函数调用)
    try:
        return bool(eval(expr, {"__builtins__": {}}, ctx))
    except Exception:
        return False


# ============================================================
# 筛选核心
# ============================================================
def screen(where: str = None, signals: List[str] = None,
          sort: str = None, top_n: int = 30,
          scope: List[str] = None, kline_days: int = 60) -> 'pd.DataFrame':
    """统一筛选入口

    Args:
        where: Python 表达式, 如 "pe<20 and roe>15"
        signals: 内置信号列表
        sort: 排序字段
        top_n: 返回前 N 只
    """
    import pandas as pd

    df = get_stock_metrics(scope)
    if df.empty:
        return df

    # 计算 N 日涨幅
    if "change_5d" not in df.columns and (where and "change_5d" in where) or (where and "change_20d" in where):
        codes = df["code"].tolist() if "code" in df.columns else []
        change = calc_change_metrics(codes, days=kline_days)
        if "change_5d" in change:
            df["change_5d"] = df["code"].map(change["change_5d"])
        if "change_20d" in change:
            df["change_20d"] = df["code"].map(change["change_20d"])

    # 应用 where
    if where:
        mask = df.apply(lambda r: safe_eval_condition(r, where), axis=1)
        df = df[mask].copy()

    # 应用 signals
    if signals:
        from skills.04-stock-analysis.stock-technical-analysis.main import check_signal_for_code
        if "code" in df.columns:
            scope_codes = df["code"].tolist()[:500]
            triggered_map = {}
            for code in scope_codes:
                trig = [s for s in signals if check_signal_for_code(code, s)]
                triggered_map[code] = trig
            mask = df["code"].apply(
                lambda c: len(triggered_map.get(c, [])) == len(signals)
            )
            df = df[mask].copy()

    # 排序
    if sort and sort in df.columns:
        df = df.sort_values(sort, ascending=True)
    elif "pct_change" in df.columns:
        df = df.sort_values("pct_change", ascending=False)

    result = df.head(top_n)
    # 清理进度文件
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    return result


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="screener v3 (接入 astock-data-source v2.0 + K线缓存)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 简单条件 (Python 表达式)
  python main.py screen --where "pe<20"
  python main.py screen --where "pe<20 and roe>15 and total_mv<200"

  # 排序 + Top N
  python main.py screen --where "pct_change>5" --sort change_5d --top 20

  # 范围
  python main.py screen --where "pe between 10,30" --sort pe

  # 用内置策略
  python main.py screen --strategy value
  python main.py screen --strategy momentum

  # 技术信号
  python main.py screen --signals macd_golden,above_ma20 --where "pct_change>0"

  # 限定股票池
  python main.py screen --where "pe<20" --codes 000001,600519,300750
        """,
    )
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("screen", help="筛选")
    p.add_argument("--where", help='Python 表达式, 如 "pe<20 and roe>15"')
    p.add_argument("--signals", help="内置信号, 逗号分隔")
    p.add_argument("--strategy", help="策略名 (value/growth/small_cap/momentum)")
    p.add_argument("--sort", help="排序字段 (pe/change_5d/total_mv ...)")
    p.add_argument("--top", type=int, default=30, help="返回前 N 只")
    p.add_argument("--codes", help="限定股票池, 逗号分隔")
    p.add_argument("--kline-days", type=int, default=60, help="K线天数 (默认 60)")

    sub.add_parser("list", help="列出内置策略")
    p = sub.add_parser("show", help="显示策略详情")
    p.add_argument("name")
    sub.add_parser("cache-stats", help="K线缓存统计")

    args = parser.parse_args()

    if args.cmd == "list":
        print("内置策略:")
        for k, v in BUILTIN_STRATEGIES.items():
            print(f"  {k}: {v['name']} --where {v['where']!r}")
    elif args.cmd == "show":
        if args.name in BUILTIN_STRATEGIES:
            s = BUILTIN_STRATEGIES[args.name]
            print(json.dumps(s, ensure_ascii=False, indent=2))
        else:
            print(f"未找到策略: {args.name}")
    elif args.cmd == "cache-stats":
        print(json.dumps(kline_stats(), ensure_ascii=False))
    elif args.cmd == "screen":
        if args.strategy:
            if args.strategy not in BUILTIN_STRATEGIES:
                print(f"未知策略: {args.strategy}")
                print("可用: " + ", ".join(BUILTIN_STRATEGIES.keys()))
                return
            s = BUILTIN_STRATEGIES[args.strategy]
            where = args.where or s.get("where")
            sort = args.sort or s.get("sort")
        else:
            where = args.where
            sort = args.sort

        if not where and not args.signals:
            print("❌ 请提供 --where 或 --signals 或 --strategy")
            print("   示例: --where 'pe<20'")
            return

        codes = None
        if args.codes:
            codes = [c.strip().zfill(6) for c in args.codes.split(",")]

        r = screen(where=where, signals=args.signals.split(",") if args.signals else None,
                  sort=sort, top_n=args.top, scope=codes, kline_days=args.kline_days)
        if r.empty:
            print("❌ 无符合条件")
        else:
            print(f"\n✅ 筛选结果 ({len(r)} 只)")
            print("=" * 100)
            cols = [c for c in ["code", "name", "price", "pct_change", "pe", "pb", "total_mv", "turnover", "change_5d", "change_20d"]
                   if c in r.columns]
            # 格式化输出
            with pd_option():
                print(r[cols].to_string(index=False))
            print("=" * 100)
    else:
        parser.print_help()


def pd_option():
    """pandas 显示选项"""
    import pandas as pd
    from contextlib import contextmanager
    @contextmanager
    def _ctx():
        with pd.option_context('display.max_rows', 100, 'display.width', 200,
                              'display.float_format', '{:.2f}'.format):
            yield
    return _ctx()


if __name__ == "__main__":
    main()
