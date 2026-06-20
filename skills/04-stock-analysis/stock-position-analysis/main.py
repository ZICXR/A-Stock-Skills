#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-position-analysis: 股东分析"""

import sys
import argparse
import pandas as pd
from typing import Dict, List


def get_top_holders(code: str, top_n: int = 10) -> pd.DataFrame:
    """前十大股东"""
    try:
        import akshare as ak
        df = ak.stock_main_holders_em(symbol=code)
    except Exception:
        try:
            import akshare as ak
            df = ak.stock_main_stock_holder(stock=code)
        except Exception as e:
            print(f"获取股东失败: {e}", file=sys.stderr)
            return pd.DataFrame()
    if not df.empty and len(df) > top_n:
        df = df.head(top_n)
    return df


def get_holder_count_change(code: str) -> Dict:
    """股东户数变化"""
    try:
        import akshare as ak
        df = ak.stock_holder_count_change_em(symbol=code)
        if df.empty:
            return {}
        latest = float(df.iloc[0].get("股东户数", 0)) if "股东户数" in df.columns else 0
        if len(df) > 1:
            prev = float(df.iloc[1].get("股东户数", 0)) if "股东户数" in df.columns else 0
        else:
            prev = latest
        change_pct = (latest - prev) / prev * 100 if prev else 0
        return {
            "latest_count": latest,
            "prev_count": prev,
            "change_pct": round(change_pct, 2),
            "signal": "筹码集中" if change_pct < -2 else "筹码分散" if change_pct > 2 else "稳定",
        }
    except Exception:
        return {}


def analyze_holder_changes(code: str) -> Dict:
    """股东增减持变化"""
    try:
        import akshare as ak
        df = ak.stock_hold_management_person_em(symbol=code)
        if df.empty:
            return {"增持": [], "减持": []}
        increases, decreases = [], []
        for _, row in df.iterrows():
            change = float(row.get("变动数量", 0)) if row.get("变动数量") else 0
            item = {
                "name": row.get("名称", ""),
                "change": change,
                "date": str(row.get("日期", "")),
            }
            if change > 0:
                increases.append(item)
            elif change < 0:
                decreases.append(item)
        return {"增持": increases[:10], "减持": decreases[:10]}
    except Exception:
        return {"增持": [], "减持": []}


def get_institutional_holders(code: str) -> pd.DataFrame:
    """机构持仓"""
    try:
        import akshare as ak
        return ak.stock_institute_holding_detail_em(symbol=code)
    except Exception:
        return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="stock-position-analysis")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("top", help="十大股东")
    p.add_argument("code")
    p.add_argument("--top", type=int, default=10)
    sub.add_parser("count", help="股东户数变化").add_argument("code")
    sub.add_parser("changes", help="增减持变化").add_argument("code")
    sub.add_parser("institutional", help="机构持仓").add_argument("code")
    args = parser.parse_args()

    if args.cmd == "top":
        df = get_top_holders(args.code, args.top)
        if not df.empty:
            print(df.to_string())
    elif args.cmd == "count":
        r = get_holder_count_change(args.code)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "changes":
        r = analyze_holder_changes(args.code)
        print("增持:")
        for item in r.get("增持", []):
            print(f"  {item['name']}: {item['change']:+.0f}")
        print("减持:")
        for item in r.get("减持", []):
            print(f"  {item['name']}: {item['change']:+.0f}")
    elif args.cmd == "institutional":
        df = get_institutional_holders(args.code)
        if not df.empty:
            print(df.head(20).to_string())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
