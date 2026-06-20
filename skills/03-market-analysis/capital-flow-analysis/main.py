#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capital-flow-analysis: 资金流向分析"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_market_fund_flow() -> Dict:
    """大盘资金流"""
    try:
        import akshare as ak
        df = ak.stock_market_fund_flow()
    except Exception as e:
        print(f"获取大盘资金流失败: {e}", file=sys.stderr)
        return {}
    if df.empty:
        return {}
    rm = {"主力净流入-净额": "main_net", "主力净流入-净占比": "main_ratio",
          "超大单净流入-净额": "super_net", "大单净流入-净额": "big_net",
          "中单净流入-净额": "mid_net", "小单净流入-净额": "small_net"}
    df = df.rename(columns={k: v for k, v in rm.items() if k in df.columns})
    result = {}
    if "市场" in df.columns:
        for m in df["市场"].unique():
            sub = df[df["市场"] == m]
            if not sub.empty:
                result[m] = sub.iloc[-1].to_dict()
    return result


def get_north_bound_today() -> Dict:
    """北向资金今日"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_north_net_flow_in_em()
    except Exception as e:
        print(f"获取北向资金失败: {e}", file=sys.stderr)
        return {}
    if df.empty:
        return {}
    return df.iloc[-1].to_dict()


def get_north_bound_flow(days: int = 30) -> pd.DataFrame:
    """北向资金历史"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_fund_flow_summary_em()
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    rm = {"日期": "date", "资金净流入": "net_inflow", "成交总额": "total_amount"}
    df = df.rename(columns={k: v for k, v in rm.items() if k in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date", ascending=False).head(days).reset_index(drop=True)
    return df


def get_stock_fund_flow(code: str, days: int = 10) -> pd.DataFrame:
    """个股资金流"""
    try:
        import akshare as ak
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        df = ak.stock_individual_fund_flow(stock=str(code).zfill(6), market=market)
    except Exception as e:
        print(f"获取个股资金流失败: {e}", file=sys.stderr)
        return pd.DataFrame()
    if df.empty:
        return df
    if "日期" in df.columns:
        df = df.sort_values("日期", ascending=False).head(days).reset_index(drop=True)
    return df


def analyze_fund_signal(flow_df: pd.DataFrame) -> Dict:
    """资金信号"""
    if flow_df.empty:
        return {"signal": "unknown"}
    last = flow_df.iloc[-1]
    main_net = last.get("main_net", last.get("主力净流入-净额", 0)) or 0
    super_net = last.get("super_net", last.get("超大单净流入-净额", 0)) or 0
    if main_net > 0 and super_net > 0:
        return {"signal": "主力大幅流入", "score": 2, "main_net": float(main_net)}
    elif main_net > 0:
        return {"signal": "主力净流入", "score": 1, "main_net": float(main_net)}
    elif main_net < 0 and super_net < 0:
        return {"signal": "主力大幅流出", "score": -2, "main_net": float(main_net)}
    elif main_net < 0:
        return {"signal": "主力净流出", "score": -1, "main_net": float(main_net)}
    return {"signal": "持平", "score": 0, "main_net": 0}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="capital-flow-analysis")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("market", help="大盘资金流")
    sub.add_parser("north-today", help="北向今日")
    p = sub.add_parser("north-hist", help="北向历史")
    p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("stock", help="个股资金")
    p.add_argument("code")
    p.add_argument("--days", type=int, default=10)
    p = sub.add_parser("signal", help="资金信号")
    p.add_argument("code")
    p.add_argument("--days", type=int, default=10)

    args = parser.parse_args()

    if args.cmd == "market":
        mf = get_market_fund_flow()
        for m, d in mf.items():
            print(f"\n【{m}】")
            for k, v in d.items():
                if v is not None and pd.notna(v) if hasattr(pd, 'notna') else v is not None:
                    print(f"  {k}: {v}")

    elif args.cmd == "north-today":
        nb = get_north_bound_today()
        for k, v in nb.items():
            if v is not None:
                print(f"  {k}: {v}")

    elif args.cmd == "north-hist":
        df = get_north_bound_flow(args.days)
        if not df.empty:
            print(df.to_string())

    elif args.cmd == "stock":
        df = get_stock_fund_flow(args.code, args.days)
        if not df.empty:
            print(df.to_string())

    elif args.cmd == "signal":
        df = get_stock_fund_flow(args.code, args.days)
        s = analyze_fund_signal(df)
        print(f"信号: {s['signal']} (分数: {s.get('score', 0)})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
