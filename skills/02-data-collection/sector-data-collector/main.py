#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sector-data-collector: 板块数据采集"""

import sys
import argparse
import pandas as pd
from typing import Optional


def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    """标准化列名"""
    if df.empty:
        return df
    rename_map = {
        "板块名称": "name", "板块代码": "code", "最新价": "price",
        "涨跌幅": "pct_change", "涨跌额": "change",
        "总市值": "total_mv", "流通市值": "circ_mv",
        "换手率": "turnover", "上涨家数": "up_count",
        "下跌家数": "down_count", "领涨股": "leader",
        "领涨股涨跌幅": "leader_pct",
    }
    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


def get_industry_sectors() -> pd.DataFrame:
    """行业板块行情"""
    try:
        import akshare as ak
        return _standardize(ak.stock_board_industry_name_em())
    except Exception as e:
        print(f"获取行业板块失败: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_concept_sectors() -> pd.DataFrame:
    """概念板块行情"""
    try:
        import akshare as ak
        return _standardize(ak.stock_board_concept_name_em())
    except Exception as e:
        print(f"获取概念板块失败: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_sector_fund_flow(period: str = "今日") -> pd.DataFrame:
    """行业板块资金流"""
    try:
        import akshare as ak
        df = ak.stock_sector_fund_flow_rank(indicator=period)
    except Exception as e:
        print(f"获取板块资金流失败: {e}", file=sys.stderr)
        return pd.DataFrame()

    if df.empty:
        return df
    rename_map = {
        "名称": "name", "今日涨跌幅": "pct_change",
        "主力净流入-净额": "main_net", "主力净流入-净占比": "main_ratio",
        "超大单净流入-净额": "super_net", "大单净流入-净额": "big_net",
        "中单净流入-净额": "mid_net", "小单净流入-净额": "small_net",
    }
    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


def get_concept_fund_flow(period: str = "今日") -> pd.DataFrame:
    """概念板块资金流"""
    try:
        import akshare as ak
        df = ak.stock_concept_fund_flow_rank(indicator=period)
    except Exception as e:
        return pd.DataFrame()

    if df.empty:
        return df
    rename_map = {
        "名称": "name", "今日涨跌幅": "pct_change",
        "主力净流入-净额": "main_net", "主力净流入-净占比": "main_ratio",
    }
    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


def get_sector_stocks(code: str, sector_type: str = "industry") -> pd.DataFrame:
    """板块成分股"""
    try:
        import akshare as ak
        if sector_type == "industry":
            return ak.stock_board_industry_cons_em(symbol=code)
        else:
            return ak.stock_board_concept_cons_em(symbol=code)
    except Exception as e:
        print(f"获取成分股失败: {e}", file=sys.stderr)
        return pd.DataFrame()


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="sector-data-collector")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("industry", help="行业板块")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("concept", help="概念板块")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("industry-flow", help="行业资金流")
    p.add_argument("--period", default="今日")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("concept-flow", help="概念资金流")
    p.add_argument("--period", default="今日")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("stocks", help="成分股")
    p.add_argument("code")
    p.add_argument("--type", default="industry", choices=["industry", "concept"])

    args = parser.parse_args()

    if args.cmd == "industry":
        df = get_industry_sectors()
        if not df.empty:
            cols = [c for c in ["name", "pct_change", "leader", "leader_pct", "up_count", "down_count"] if c in df.columns]
            print(df.nlargest(args.top, "pct_change")[cols].to_string())

    elif args.cmd == "concept":
        df = get_concept_sectors()
        if not df.empty:
            cols = [c for c in ["name", "pct_change", "leader", "leader_pct"] if c in df.columns]
            print(df.nlargest(args.top, "pct_change")[cols].to_string())

    elif args.cmd == "industry-flow":
        df = get_sector_fund_flow(args.period)
        if not df.empty and "main_net" in df.columns:
            cols = [c for c in ["name", "pct_change", "main_net", "main_ratio"] if c in df.columns]
            print(df.nlargest(args.top, "main_net")[cols].to_string())

    elif args.cmd == "concept-flow":
        df = get_concept_fund_flow(args.period)
        if not df.empty and "main_net" in df.columns:
            cols = [c for c in ["name", "pct_change", "main_net"] if c in df.columns]
            print(df.nlargest(args.top, "main_net")[cols].to_string())

    elif args.cmd == "stocks":
        df = get_sector_stocks(args.code, args.type)
        if not df.empty:
            print(df.head(30).to_string())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
