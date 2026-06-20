#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dragon-tiger-analysis: 龙虎榜分析"""

import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict


KNOWN_HOT_MONEY = [
    "方新侠", "作手新一", "赵老哥", "孙哥", "章盟主", "炒股养家",
    "欢乐海", "佛山系", "成都系", "上海溧阳路", "深圳益田路",
    "荣超商务中心", "杭州延安路", "南京中山东路", "宁波桑田路",
    "财通杭州", "华鑫上海分公司", "东方上海源深路", "东财拉萨",
    "华泰证券", "中信证券", "国泰君安", "海通证券", "招商证券",
    "银河证券", "广发证券", "国信证券", "申万宏源", "中金公司",
    "瑞鹤仙", "小鳄鱼", "赵老哥", "孙哥", "杭州帮", "上海帮",
    "北京帮", "深圳帮", "成都帮", "南京帮", "宁波帮",
]


def is_hot_money(branch: str) -> bool:
    if not branch:
        return False
    for name in KNOWN_HOT_MONEY:
        if name in branch:
            return True
    return False


def get_lhb_detail(date: str = None) -> pd.DataFrame:
    """龙虎榜明细"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        import akshare as ak
        df = ak.stock_lhb_detail_em(start_date=date, end_date=date)
    except Exception as e:
        print(f"获取龙虎榜失败: {e}", file=sys.stderr)
        return pd.DataFrame()
    return df


def get_institution_summary(date: str = None) -> pd.DataFrame:
    """机构买卖汇总"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        import akshare as ak
        df = ak.stock_lhb_jgmmtj_em(start_date=date, end_date=date)
    except Exception:
        return pd.DataFrame()
    return df


def get_zt_hot_money(date: str = None) -> pd.DataFrame:
    """涨停板中游资参与的股票"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    try:
        import akshare as ak
        return ak.stock_zt_pool_em(date=date)
    except Exception:
        return pd.DataFrame()


def track_hot_money(date: str = None) -> pd.DataFrame:
    """知名游资操作"""
    df = get_lhb_detail(date)
    if df.empty:
        return df
    branch_cols = [c for c in df.columns if "营业部" in c]
    if not branch_cols:
        return pd.DataFrame()
    hot_records = []
    for _, row in df.iterrows():
        for col in branch_cols:
            branch = str(row.get(col, ""))
            if is_hot_money(branch):
                hot_records.append(row)
                break
    return pd.DataFrame(hot_records)


def lhb_daily_report(date: str = None) -> Dict:
    """每日龙虎榜报告"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    detail = get_lhb_detail(date)
    hot = track_hot_money(date)
    inst = get_institution_summary(date)
    zt = get_zt_hot_money()
    return {
        "date": date,
        "summary": {
            "lhb_stocks": len(detail["代码"].unique()) if not detail.empty and "代码" in detail.columns else 0,
            "hot_money_count": len(hot),
            "institution_count": len(inst),
            "zt_stocks": len(zt),
        },
        "detail": detail,
        "hot_money": hot,
        "institution": inst,
        "zt_pool": zt,
    }


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="dragon-tiger-analysis")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("detail", help="龙虎榜明细")
    p.add_argument("date", nargs="?")

    p = sub.add_parser("hot", help="游资动向")
    p.add_argument("date", nargs="?")

    p = sub.add_parser("inst", help="机构席位")
    p.add_argument("date", nargs="?")

    p = sub.add_parser("zt", help="涨停中游资参与的")
    p.add_argument("date", nargs="?")

    sub.add_parser("report", help="每日报告")
    p = sub.add_parser("check", help="检查是否游资")
    p.add_argument("branch")

    args = parser.parse_args()

    if args.cmd == "detail":
        df = get_lhb_detail(args.date)
        if not df.empty:
            print(df.head(20).to_string())

    elif args.cmd == "hot":
        df = track_hot_money(args.date)
        if not df.empty:
            print(df.head(20).to_string())
        else:
            print("无游资上榜记录")

    elif args.cmd == "inst":
        df = get_institution_summary(args.date)
        if not df.empty:
            print(df.head(20).to_string())

    elif args.cmd == "zt":
        df = get_zt_hot_money(args.date)
        if not df.empty:
            print(df.head(20).to_string())

    elif args.cmd == "report":
        r = lhb_daily_report(args.date if hasattr(args, "date") else None)
        print(f"日期: {r['date']}")
        print(f"\n汇总:")
        for k, v in r["summary"].items():
            print(f"  {k}: {v}")

    elif args.cmd == "check":
        print(f"{args.branch}: {'是知名游资' if is_hot_money(args.branch) else '普通席位'}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
