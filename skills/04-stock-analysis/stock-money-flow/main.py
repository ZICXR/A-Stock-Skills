#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-money-flow: 个股资金流分析"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_money_flow(code: str, days: int = 10) -> pd.DataFrame:
    """个股资金流历史"""
    try:
        import akshare as ak
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        df = ak.stock_individual_fund_flow(stock=str(code).zfill(6), market=market)
    except Exception as e:
        print(f"获取资金流失败: {e}", file=sys.stderr)
        return pd.DataFrame()
    if df.empty:
        return df
    if "日期" in df.columns:
        df = df.sort_values("日期", ascending=False).head(days).reset_index(drop=True)
    return df


def analyze_main_force(code: str) -> Dict:
    """主力动向"""
    df = get_money_flow(code, days=10)
    if df.empty:
        return {}
    main_col = None
    super_col = None
    big_col = None
    for c in df.columns:
        if "主力" in str(c) and "净额" in str(c):
            main_col = c
        elif "超大单" in str(c) and "净额" in str(c):
            super_col = c
        elif "大单" in str(c) and "净额" in str(c):
            big_col = c
    if not main_col:
        return {"trend": "数据不足"}
    main_5d = float(df[main_col].head(5).sum()) if main_col in df.columns else 0
    main_10d = float(df[main_col].sum()) if main_col in df.columns else 0
    super_5d = float(df[super_col].head(5).sum()) if super_col and super_col in df.columns else 0

    trend = "流入" if main_5d > 0 else "流出"
    return {
        "main_net_5d": main_5d,
        "main_net_10d": main_10d,
        "super_net_5d": super_5d,
        "trend": trend,
    }


def get_buy_sell(code: str) -> Dict:
    """买卖盘口"""
    try:
        import akshare as ak
        df = ak.stock_bid_ask_em(symbol=str(code).zfill(6))
        if df.empty:
            return {}
        return {"data": df.to_dict("records")}
    except Exception:
        return {}


def money_flow_signal(code: str) -> Dict:
    """资金信号"""
    main = analyze_main_force(code)
    if not main or "main_net_5d" not in main:
        return {"signal": "数据不足", "score": 0}
    main_5d = main["main_net_5d"]
    super_5d = main.get("super_net_5d", 0)
    if main_5d > 0 and super_5d > 0:
        return {"signal": "主力大幅流入", "score": 2, "main_net_5d": main_5d}
    elif main_5d > 0:
        return {"signal": "主力净流入", "score": 1, "main_net_5d": main_5d}
    elif main_5d < 0 and super_5d < 0:
        return {"signal": "主力大幅流出", "score": -2, "main_net_5d": main_5d}
    elif main_5d < 0:
        return {"signal": "主力净流出", "score": -1, "main_net_5d": main_5d}
    return {"signal": "持平", "score": 0, "main_net_5d": 0}


def main():
    parser = argparse.ArgumentParser(description="stock-money-flow")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("flow", help="资金流历史")
    p.add_argument("code")
    p.add_argument("--days", type=int, default=10)
    sub.add_parser("main", help="主力动向").add_argument("code")
    sub.add_parser("buy-sell", help="买卖盘口").add_argument("code")
    sub.add_parser("signal", help="资金信号").add_argument("code")
    args = parser.parse_args()

    if args.cmd == "flow":
        df = get_money_flow(args.code, args.days)
        if not df.empty:
            print(df.to_string())
    elif args.cmd == "main":
        r = analyze_main_force(args.code)
        for k, v in r.items():
            if isinstance(v, (int, float)) and abs(v) > 1e4:
                print(f"  {k}: {v/1e8:+.2f}亿")
            else:
                print(f"  {k}: {v}")
    elif args.cmd == "buy-sell":
        r = get_buy_sell(args.code)
        for item in r.get("data", [])[:10]:
            print(f"  {item}")
    elif args.cmd == "signal":
        r = money_flow_signal(args.code)
        print(f"信号: {r.get('signal')} (分数: {r.get('score')})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
