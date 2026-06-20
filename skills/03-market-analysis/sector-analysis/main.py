#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sector-analysis: 板块轮动分析"""

import sys
import argparse
import pandas as pd
from typing import Dict


def _get_industries() -> pd.DataFrame:
    try:
        import akshare as ak
        df = ak.stock_board_industry_name_em()
    except Exception as e:
        print(f"获取行业板块失败: {e}", file=sys.stderr)
        return pd.DataFrame()
    if df.empty:
        return df
    rm = {"板块名称": "name", "板块代码": "code", "最新价": "price",
          "涨跌幅": "pct_change", "涨跌额": "change",
          "总市值": "total_mv", "上涨家数": "up_count",
          "下跌家数": "down_count", "领涨股": "leader",
          "领涨股涨跌幅": "leader_pct"}
    return df.rename(columns={k: v for k, v in rm.items() if k in df.columns})


def _get_concepts() -> pd.DataFrame:
    try:
        import akshare as ak
        df = ak.stock_board_concept_name_em()
    except Exception as e:
        return pd.DataFrame()
    if df.empty:
        return df
    rm = {"板块名称": "name", "板块代码": "code", "最新价": "price",
          "涨跌幅": "pct_change", "领涨股": "leader", "领涨股涨跌幅": "leader_pct"}
    return df.rename(columns={k: v for k, v in rm.items() if k in df.columns})


def _get_industry_flow(period: str = "今日") -> pd.DataFrame:
    try:
        import akshare as ak
        df = ak.stock_sector_fund_flow_rank(indicator=period)
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    rm = {"名称": "name", "主力净流入-净额": "main_net", "主力净流入-净占比": "main_ratio"}
    return df.rename(columns={k: v for k, v in rm.items() if k in df.columns})


def _get_concept_flow(period: str = "今日") -> pd.DataFrame:
    try:
        import akshare as ak
        df = ak.stock_concept_fund_flow_rank(indicator=period)
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    rm = {"名称": "name", "主力净流入-净额": "main_net", "主力净流入-净占比": "main_ratio"}
    return df.rename(columns={k: v for k, v in rm.items() if k in df.columns})


def rank_sectors(sector_type: str = "industry", top_n: int = 20) -> pd.DataFrame:
    """板块涨跌幅排名"""
    df = _get_industries() if sector_type == "industry" else _get_concepts()
    if df.empty or "pct_change" not in df.columns:
        return df
    return df.sort_values("pct_change", ascending=False).head(top_n).reset_index(drop=True)


def top_fund_inflow(period: str = "今日", sector_type: str = "industry", top_n: int = 10) -> pd.DataFrame:
    df = _get_industry_flow(period) if sector_type == "industry" else _get_concept_flow(period)
    if df.empty or "main_net" not in df.columns:
        return df
    return df.sort_values("main_net", ascending=False).head(top_n).reset_index(drop=True)


def top_fund_outflow(period: str = "今日", sector_type: str = "industry", top_n: int = 10) -> pd.DataFrame:
    df = _get_industry_flow(period) if sector_type == "industry" else _get_concept_flow(period)
    if df.empty or "main_net" not in df.columns:
        return df
    return df.sort_values("main_net", ascending=True).head(top_n).reset_index(drop=True)


def calc_sector_score(sector_df: pd.DataFrame, flow_df: pd.DataFrame) -> pd.DataFrame:
    """综合强度评分"""
    if sector_df.empty or flow_df.empty:
        return sector_df
    df = sector_df.merge(flow_df[["name", "main_net"]], on="name", how="left")
    if df.empty:
        return sector_df

    max_change = df["pct_change"].abs().max() if "pct_change" in df.columns else 1
    df["score_change"] = df["pct_change"] / max_change * 40 if "pct_change" in df.columns else 0
    max_flow = df["main_net"].abs().max() if "main_net" in df.columns else 1
    df["score_flow"] = df["main_net"] / max_flow * 40 if "main_net" in df.columns else 0
    if "up_count" in df.columns and "down_count" in df.columns:
        total = df["up_count"] + df["down_count"]
        df["up_ratio"] = df["up_count"] / total.replace(0, 1)
        df["score_up"] = (df["up_ratio"] - 0.5) * 40
    else:
        df["score_up"] = 0
    df["total_score"] = df["score_change"] + df["score_flow"] + df["score_up"]
    return df.sort_values("total_score", ascending=False).reset_index(drop=True)


def identify_main_themes(top_n: int = 5) -> Dict:
    """识别主线板块"""
    industry_df = _get_industries()
    concept_df = _get_concepts()
    flow_df = _get_industry_flow("今日")

    main_themes = []
    if not industry_df.empty:
        scored = calc_sector_score(industry_df, flow_df)
        for _, row in scored.head(top_n).iterrows():
            main_themes.append({
                "type": "行业", "name": row.get("name", ""),
                "pct_change": row.get("pct_change", 0),
                "main_net": row.get("main_net", 0),
                "score": row.get("total_score", 0),
                "leader": row.get("leader", ""),
            })
    if not concept_df.empty:
        scored = calc_sector_score(concept_df, flow_df)
        for _, row in scored.head(top_n).iterrows():
            main_themes.append({
                "type": "概念", "name": row.get("name", ""),
                "pct_change": row.get("pct_change", 0),
                "main_net": row.get("main_net", 0),
                "score": row.get("total_score", 0),
                "leader": row.get("leader", ""),
            })
    main_themes.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"main_themes": main_themes[:top_n * 2]}


def detect_rotation_signal(df: pd.DataFrame) -> Dict:
    """轮动信号"""
    if df.empty or "pct_change" not in df.columns:
        return {"signal": "unknown", "info": "数据不足"}
    up = int((df["pct_change"] > 0).sum())
    total = len(df)
    ratio = up / total if total else 0
    if ratio > 0.8:
        signal, desc = "普涨", "市场普涨, 风险偏好高, 注意后续分化"
    elif ratio < 0.2:
        signal, desc = "普跌", "市场普跌, 风险偏好低, 关注政策/护盘信号"
    elif ratio > 0.6:
        signal, desc = "结构性上涨", "结构性行情, 抓主线"
    elif ratio < 0.4:
        signal, desc = "结构性下跌", "多数板块下跌, 谨慎"
    else:
        signal, desc = "分化", "板块分化, 精选个股"
    return {"signal": signal, "desc": desc, "up_ratio": round(ratio * 100, 2), "up": up, "total": total}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="sector-analysis")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("rank", help="板块排名")
    p.add_argument("type", nargs="?", default="industry")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("inflow", help="资金流入榜")
    p.add_argument("period", nargs="?", default="今日")
    p.add_argument("--type", default="industry")
    p.add_argument("--top", type=int, default=10)

    p = sub.add_parser("outflow", help="资金流出榜")
    p.add_argument("period", nargs="?", default="今日")
    p.add_argument("--type", default="industry")
    p.add_argument("--top", type=int, default=10)

    p = sub.add_parser("themes", help="主线板块")
    p.add_argument("--top", type=int, default=5)

    sub.add_parser("rotation", help="轮动信号")

    args = parser.parse_args()

    if args.cmd == "rank":
        df = rank_sectors(args.type, args.top)
        if not df.empty:
            cols = [c for c in ["name", "pct_change", "leader"] if c in df.columns]
            print(df[cols].to_string())

    elif args.cmd == "inflow":
        df = top_fund_inflow(args.period, args.type, args.top)
        if not df.empty:
            cols = [c for c in ["name", "main_net", "main_ratio"] if c in df.columns]
            print(df[cols].to_string())

    elif args.cmd == "outflow":
        df = top_fund_outflow(args.period, args.type, args.top)
        if not df.empty:
            cols = [c for c in ["name", "main_net", "main_ratio"] if c in df.columns]
            print(df[cols].to_string())

    elif args.cmd == "themes":
        r = identify_main_themes(args.top)
        for t in r.get("main_themes", []):
            print(f"  [{t['type']}] {t['name']}: 涨幅{t['pct_change']:.2f}%, 资金{t.get('main_net', 0)/1e8:+.2f}亿, 龙头{t['leader']}")

    elif args.cmd == "rotation":
        df = _get_industries()
        s = detect_rotation_signal(df)
        for k, v in s.items():
            print(f"  {k}: {v}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
