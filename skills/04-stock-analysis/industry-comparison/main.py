#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""industry-comparison: 同业对比"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


def get_basic_metrics(codes: List[str]) -> pd.DataFrame:
    """获取基础指标"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
    except Exception as e:
        print(f"获取数据失败: {e}", file=sys.stderr)
        return pd.DataFrame()
    if df.empty:
        return df
    rename_map = {
        "代码": "code", "名称": "name", "最新价": "price",
        "涨跌幅": "pct_change", "换手率": "turnover",
        "市盈率-动态": "pe", "市净率": "pb", "市销率": "ps",
        "总市值": "total_mv", "流通市值": "circ_mv", "所属行业": "industry",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if "code" in df.columns:
        df["code"] = df["code"].astype(str)
    return df


def get_financial_metrics(code: str) -> Dict:
    """获取财务指标"""
    try:
        import akshare as ak
        df = ak.stock_financial_abstract_ths(symbol=code)
        if df.empty:
            return {}
        result = {}
        for _, row in df.iterrows():
            for col in df.columns:
                val = row[col]
                if val is None or (hasattr(pd, 'isna') and pd.isna(val)):
                    continue
                col_str = str(col)
                if "ROE" in col_str or "净资产收益率" in col_str:
                    result["roe"] = float(val) if val else None
                elif "毛利率" in col_str:
                    result["gross_margin"] = float(val) if val else None
                elif "净利率" in col_str:
                    result["net_margin"] = float(val) if val else None
                elif "营业总收入" in col_str and "增长" in col_str:
                    result["revenue_growth"] = float(val) if val else None
                elif "净利润" in col_str and "增长" in col_str:
                    result["profit_growth"] = float(val) if val else None
                break
        return result
    except Exception:
        return {}


def get_momentum_metrics(code: str) -> Dict:
    """获取动量指标"""
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=str(code).zfill(6), period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if df.empty or len(df) < 20:
            return {}
        df.columns = [c.lower() for c in df.columns]
        close = df["close"]
        return {
            "change_5d": round((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100, 2) if len(df) >= 6 else 0,
            "change_20d": round((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21] * 100, 2) if len(df) >= 21 else 0,
            "change_60d": round((close.iloc[-1] - close.iloc[-61]) / close.iloc[-61] * 100, 2) if len(df) >= 61 else 0,
        }
    except Exception:
        return {}


def get_capital_flow_metric(code: str) -> float:
    """获取主力净流入"""
    try:
        import akshare as ak
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        df = ak.stock_individual_fund_flow(stock=str(code).zfill(6), market=market)
        if df.empty:
            return 0
        for col in df.columns:
            if "主力" in str(col) and "净额" in str(col):
                val = float(df[col].head(5).sum()) if df[col].iloc[0] else 0
                return val
        return 0
    except Exception:
        return 0


# ============================================================
# 核心对比
# ============================================================
def build_comparison(codes: List[str]) -> pd.DataFrame:
    """构建对比表"""
    basic = get_basic_metrics(codes)
    if basic.empty:
        return pd.DataFrame()

    basic["code"] = basic["code"].astype(str)
    target = basic[basic["code"].isin([str(c).zfill(6) for c in codes])].copy()

    if target.empty:
        return target

    # 添加财务指标
    for code in codes:
        fin = get_financial_metrics(code)
        idx = target[target["code"] == str(code).zfill(6)].index
        for k, v in fin.items():
            if idx.any():
                target.loc[idx, k] = v

    # 动量
    for code in codes:
        mom = get_momentum_metrics(code)
        idx = target[target["code"] == str(code).zfill(6)].index
        for k, v in mom.items():
            if idx.any():
                target.loc[idx, k] = v

    # 主力资金
    for code in codes:
        flow = get_capital_flow_metric(code)
        idx = target[target["code"] == str(code).zfill(6)].index
        if idx.any():
            target.loc[idx, "main_net_5d"] = flow

    return target.reset_index(drop=True)


def calc_score(df: pd.DataFrame) -> pd.DataFrame:
    """计算综合得分"""
    if df.empty:
        return df
    df = df.copy()
    df["score"] = 50.0

    # 估值分 (PE/PB 越低越好)
    if "pe" in df.columns:
        df["score_pe"] = df["pe"].apply(lambda x: 100 if pd.isna(x) or x <= 0 else max(0, 100 - x * 3))
    else:
        df["score_pe"] = 50

    if "pb" in df.columns:
        df["score_pb"] = df["pb"].apply(lambda x: 100 if pd.isna(x) or x <= 0 else max(0, 100 - x * 20))
    else:
        df["score_pb"] = 50

    # 盈利分
    if "roe" in df.columns:
        df["score_roe"] = df["roe"].apply(lambda x: 50 if pd.isna(x) else max(0, min(100, x * 4)))
    else:
        df["score_roe"] = 50

    # 成长分
    if "profit_growth" in df.columns:
        df["score_growth"] = df["profit_growth"].apply(lambda x: 50 if pd.isna(x) else max(0, min(100, 50 + x)))
    else:
        df["score_growth"] = 50

    # 技术分 (动量)
    if "change_20d" in df.columns:
        df["score_tech"] = df["change_20d"].apply(lambda x: 50 if pd.isna(x) else max(0, min(100, 50 + x)))
    else:
        df["score_tech"] = 50

    # 资金分
    if "main_net_5d" in df.columns:
        df["score_capital"] = df["main_net_5d"].apply(lambda x: 50 if pd.isna(x) else max(0, min(100, 50 + x / 1e8)))
    else:
        df["score_capital"] = 50

    # 综合
    df["score"] = (
        df["score_pe"] * 0.1
        + df["score_pb"] * 0.1
        + df["score_roe"] * 0.25
        + df["score_growth"] * 0.2
        + df["score_tech"] * 0.2
        + df["score_capital"] * 0.15
    )
    df["score"] = df["score"].round(2)
    return df.sort_values("score", ascending=False).reset_index(drop=True)


def compare_stocks(codes: List[str], name: str = "") -> pd.DataFrame:
    """对比多只股票"""
    df = build_comparison(codes)
    if df.empty:
        return df
    df = calc_score(df)
    df["rank"] = range(1, len(df) + 1)
    return df


def rank_by_metric(codes: List[str], metric: str) -> pd.DataFrame:
    """按指标排名"""
    df = build_comparison(codes)
    if df.empty or metric not in df.columns:
        return df
    return df.sort_values(metric, ascending=False).reset_index(drop=True)


def find_leader(industry: str, top_n: int = 5) -> pd.DataFrame:
    """找行业龙头 (按市值)"""
    df = get_basic_metrics([])
    if df.empty or "industry" not in df.columns:
        return df
    industry_df = df[df["industry"].astype(str).str.contains(industry, na=False)]
    if "total_mv" in industry_df.columns:
        industry_df = industry_df.sort_values("total_mv", ascending=False)
    return industry_df.head(top_n).reset_index(drop=True)


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="industry-comparison")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("compare", help="对比")
    p.add_argument("--codes", required=True)
    p.add_argument("--name", default="")
    p = sub.add_parser("rank", help="按指标排名")
    p.add_argument("--codes", required=True)
    p.add_argument("--metric", required=True)
    p = sub.add_parser("leader", help="找行业龙头")
    p.add_argument("--industry", required=True)
    p.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    if args.cmd == "compare":
        codes = [c.strip() for c in args.codes.split(",")]
        df = compare_stocks(codes, args.name)
        if df.empty:
            print("无数据")
            return
        cols = [c for c in ["rank", "code", "name", "price", "pct_change", "pe", "pb", "roe", "change_20d", "score"] if c in df.columns]
        print(f"\n=== {args.name or '同业对比'} ===")
        print(df[cols].to_string())
    elif args.cmd == "rank":
        codes = [c.strip() for c in args.codes.split(",")]
        df = rank_by_metric(codes, args.metric)
        if df.empty:
            print("无数据")
        else:
            print(df[["code", "name", args.metric]].to_string())
    elif args.cmd == "leader":
        df = find_leader(args.industry, args.top)
        if df.empty:
            print(f"未找到 {args.industry} 行业")
        else:
            cols = [c for c in ["code", "name", "price", "pct_change", "total_mv", "pe", "pb"] if c in df.columns]
            print(f"\n=== {args.industry} 行业龙头 ===")
            print(df[cols].to_string())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
