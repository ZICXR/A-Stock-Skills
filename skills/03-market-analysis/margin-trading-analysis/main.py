#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""margin-trading-analysis: 两融分析"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_margin_summary() -> Dict:
    """两融总览"""
    try:
        import akshare as ak
        df = ak.stock_margin_underlying_info_szse()
        if df.empty:
            return {}
        last = df.iloc[-1].to_dict()
        return last
    except Exception:
        try:
            import akshare as ak
            df = ak.stock_margin_underlying_info_sse()
            if df.empty:
                return {}
            return df.iloc[-1].to_dict()
        except Exception as e:
            print(f"获取两融数据失败: {e}", file=sys.stderr)
            return {}


def get_margin_history(days: int = 30) -> pd.DataFrame:
    """两融历史"""
    try:
        import akshare as ak
        df = ak.stock_margin_underlying_info_szse()
        if df.empty:
            return df
        if "date" in df.columns or "日期" in df.columns:
            col = "date" if "date" in df.columns else "日期"
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.sort_values(col, ascending=False).head(days).reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()


def get_margin_individual(code: str) -> pd.DataFrame:
    """个股两融"""
    try:
        import akshare as ak
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        df = ak.stock_margin_underlying_info_szse(symbol=str(code).zfill(6)) if market == "sz" else ak.stock_margin_underlying_info_sse(symbol=str(code).zfill(6))
        return df
    except Exception:
        return pd.DataFrame()


def analyze_margin_sentiment() -> Dict:
    """两融情绪"""
    hist = get_margin_history(days=10)
    if hist.empty:
        return {"level": "unknown"}
    margin_col = None
    for c in ["融资余额", "margin_balance", "余额"]:
        if c in hist.columns:
            margin_col = c
            break
    if not margin_col:
        return {"level": "unknown"}
    try:
        latest = float(hist[margin_col].iloc[0])
        prev = float(hist[margin_col].iloc[min(4, len(hist) - 1)])
        change = (latest - prev) / prev * 100
    except Exception:
        return {"level": "unknown"}

    if change > 3:
        return {"level": "过热", "change_pct": round(change, 2), "signal": "警惕过热, 谨防回调"}
    elif change > 1:
        return {"level": "偏多", "change_pct": round(change, 2), "signal": "杠杆资金流入"}
    elif change < -3:
        return {"level": "恐慌", "change_pct": round(change, 2), "signal": "警惕恐慌抛售"}
    elif change < -1:
        return {"level": "偏空", "change_pct": round(change, 2), "signal": "杠杆资金流出"}
    else:
        return {"level": "中性", "change_pct": round(change, 2), "signal": "杠杆资金稳定"}


def main():
    parser = argparse.ArgumentParser(description="margin-trading-analysis")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("summary", help="总览")
    p = sub.add_parser("history", help="历史")
    p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("stock", help="个股两融")
    p.add_argument("code")
    sub.add_parser("sentiment", help="情绪分析")
    args = parser.parse_args()

    if args.cmd == "summary":
        s = get_margin_summary()
        for k, v in list(s.items())[:10]:
            print(f"  {k}: {v}")
    elif args.cmd == "history":
        df = get_margin_history(args.days)
        if not df.empty:
            print(df.head(args.days).to_string())
    elif args.cmd == "stock":
        df = get_margin_individual(args.code)
        if not df.empty:
            print(df.to_string())
    elif args.cmd == "sentiment":
        s = analyze_margin_sentiment()
        print(f"等级: {s.get('level')} (变化: {s.get('change_pct')}%)")
        print(f"信号: {s.get('signal')}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
