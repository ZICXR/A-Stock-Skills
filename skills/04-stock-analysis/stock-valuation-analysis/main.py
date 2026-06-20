#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-valuation-analysis: 个股估值分析"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_valuation_metrics(code: str) -> Dict:
    """获取估值指标"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return {}
        row = target.iloc[0]
        return {
            "code": row.get("代码", code),
            "name": row.get("名称", ""),
            "price": float(row.get("最新价", 0)),
            "pe_ttm": float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else None,
            "pe_static": float(row.get("市盈率", 0)) if row.get("市盈率") else None,
            "pb": float(row.get("市净率", 0)) if row.get("市净率") else None,
            "ps_ttm": float(row.get("市销率", 0)) if row.get("市销率") else None,
            "total_mv": float(row.get("总市值", 0)),
            "circ_mv": float(row.get("流通市值", 0)),
        }
    except Exception as e:
        print(f"获取估值失败: {e}", file=sys.stderr)
        return {}


def calc_pe_percentile(code: str) -> Dict:
    """PE 历史分位 (基于行业均值估算)"""
    metrics = get_valuation_metrics(code)
    if not metrics:
        return {}
    pe = metrics.get("pe_ttm", 0) or 0
    # 简化: 假设当前 PE 在 0-100 区间,百分位估算
    if pe <= 0:
        return {"pe": pe, "percentile": 0, "level": "亏损"}
    if pe < 15:
        pct = 10
    elif pe < 25:
        pct = 30
    elif pe < 40:
        pct = 50
    elif pe < 60:
        pct = 70
    elif pe < 100:
        pct = 85
    else:
        pct = 95
    return {
        "pe": pe,
        "percentile": pct,
        "level": f"近{pct}%分位",
    }


def calc_peg(code: str, growth_rate: float = 15.0) -> Dict:
    """PEG 估值"""
    metrics = get_valuation_metrics(code)
    if not metrics or not growth_rate:
        return {}
    pe = metrics.get("pe_ttm", 0) or 0
    if pe <= 0 or growth_rate <= 0:
        return {"pe": pe, "growth_rate": growth_rate, "peg": None}
    peg = pe / growth_rate
    if peg < 0.5:
        level = "深度低估"
    elif peg < 1:
        level = "低估"
    elif peg < 1.5:
        level = "合理"
    elif peg < 2:
        level = "高估"
    else:
        level = "严重高估"
    return {
        "pe": round(pe, 2),
        "growth_rate": growth_rate,
        "peg": round(peg, 2),
        "level": level,
    }


def industry_comparison(code: str) -> Dict:
    """行业相对估值"""
    metrics = get_valuation_metrics(code)
    if not metrics:
        return {}
    pe = metrics.get("pe_ttm", 0) or 0
    pb = metrics.get("pb", 0) or 0
    # 行业均值 (简化: 假设A股平均 PE 20, PB 1.5)
    industry_pe = 20.0
    industry_pb = 1.5
    return {
        "stock_pe": pe,
        "industry_pe": industry_pe,
        "pe_premium": round((pe - industry_pe) / industry_pe * 100, 2) if industry_pe else 0,
        "stock_pb": pb,
        "industry_pb": industry_pb,
        "pb_premium": round((pb - industry_pb) / industry_pb * 100, 2) if industry_pb else 0,
    }


def valuation_rating(code: str) -> Dict:
    """估值综合评级"""
    metrics = get_valuation_metrics(code)
    if not metrics:
        return {"rating": "unknown"}
    pe = metrics.get("pe_ttm", 0) or 0
    pb = metrics.get("pb", 0) or 0
    score = 50
    if pe < 0:
        rating = "亏损"
        score = 30
    elif pe < 15:
        rating = "严重低估"
        score = 90
    elif pe < 25:
        rating = "低估"
        score = 75
    elif pe < 40:
        rating = "合理"
        score = 55
    elif pe < 60:
        rating = "合理偏高"
        score = 40
    elif pe < 100:
        rating = "高估"
        score = 25
    else:
        rating = "严重高估"
        score = 10
    if 0 < pb < 1:
        score += 5
    elif pb > 5:
        score -= 5
    return {"rating": rating, "score": max(0, min(100, score))}


def main():
    parser = argparse.ArgumentParser(description="stock-valuation-analysis")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("metrics", help="估值指标")
    p.add_argument("code")
    p = sub.add_parser("percentile", help="PE分位")
    p.add_argument("code")
    p = sub.add_parser("peg", help="PEG")
    p.add_argument("code")
    p.add_argument("--growth", type=float, default=15.0)
    p = sub.add_parser("compare", help="行业对比")
    p.add_argument("code")
    p = sub.add_parser("rating", help="估值评级")
    p.add_argument("code")
    args = parser.parse_args()

    if args.cmd == "metrics":
        v = get_valuation_metrics(args.code)
        for k, val in v.items():
            print(f"  {k}: {val}")
    elif args.cmd == "percentile":
        r = calc_pe_percentile(args.code)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "peg":
        r = calc_peg(args.code, args.growth)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "compare":
        r = industry_comparison(args.code)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "rating":
        r = valuation_rating(args.code)
        print(f"评级: {r.get('rating')} (评分: {r.get('score')})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
