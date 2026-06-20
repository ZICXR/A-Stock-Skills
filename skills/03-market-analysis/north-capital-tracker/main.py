#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""north-capital-tracker: 北向资金追踪"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_north_realtime() -> Dict:
    """北向资金实时"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_north_net_flow_in_em()
        if df.empty:
            return {}
        last = df.iloc[-1].to_dict()
        return {
            "date": str(last.get("date", "")),
            "沪股通": last.get("hgt", 0),
            "深股通": last.get("sgt", 0),
            "北向资金": last.get("north_money", 0),
            "南向资金": last.get("south_money", 0),
        }
    except Exception as e:
        print(f"获取北向资金失败: {e}", file=sys.stderr)
        return {}


def get_north_history(days: int = 30) -> pd.DataFrame:
    """北向资金历史"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df.empty:
            return df
        rm = {"日期": "date", "资金净流入": "net_inflow", "成交总额": "total_amount"}
        df = df.rename(columns={k: v for k, v in rm.items() if k in df.columns})
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.sort_values("date", ascending=False).head(days).reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()


def get_north_holdings(top_n: int = 20) -> pd.DataFrame:
    """北向重仓股"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_hold_stock_em()
        if df.empty:
            return df
        if "持股数" in df.columns:
            df = df.sort_values("持股数", ascending=False).head(top_n)
        return df
    except Exception:
        return pd.DataFrame()


def detect_north_signal() -> Dict:
    """北向资金异动信号"""
    nb = get_north_realtime()
    if not nb:
        return {"signal": "unknown"}
    net = nb.get("北向资金", 0)
    try:
        net = float(net)
    except:
        return {"signal": "unknown"}
    if net > 5e9:
        return {"signal": "大幅流入", "amount": net, "level": "strong_bull"}
    elif net > 2e9:
        return {"signal": "明显流入", "amount": net, "level": "bull"}
    elif net > 0:
        return {"signal": "小幅流入", "amount": net, "level": "weak_bull"}
    elif net > -2e9:
        return {"signal": "小幅流出", "amount": net, "level": "weak_bear"}
    elif net > -5e9:
        return {"signal": "明显流出", "amount": net, "level": "bear"}
    else:
        return {"signal": "大幅流出", "amount": net, "level": "strong_bear"}


def main():
    parser = argparse.ArgumentParser(description="north-capital-tracker")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("realtime", help="实时")
    p = sub.add_parser("history", help="历史")
    p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("holdings", help="重仓股")
    p.add_argument("--top", type=int, default=20)
    sub.add_parser("signal", help="异动信号")
    args = parser.parse_args()

    if args.cmd == "realtime":
        nb = get_north_realtime()
        for k, v in nb.items():
            if isinstance(v, (int, float)) and abs(v) > 1e4:
                print(f"  {k}: {v/1e8:+.2f}亿")
            else:
                print(f"  {k}: {v}")
    elif args.cmd == "history":
        df = get_north_history(args.days)
        if not df.empty:
            print(df.to_string())
    elif args.cmd == "holdings":
        df = get_north_holdings(args.top)
        if not df.empty:
            print(df.head(args.top).to_string())
    elif args.cmd == "signal":
        s = detect_north_signal()
        print(f"信号: {s.get('signal')} (净额: {s.get('amount', 0)/1e8:+.2f}亿)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
