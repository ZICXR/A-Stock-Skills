#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-fundamental-analysis: 个股基本面分析"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_financial_indicator(code: str) -> pd.DataFrame:
    try:
        import akshare as ak
        return ak.stock_financial_abstract_ths(symbol=code)
    except Exception:
        try:
            import akshare as ak
            return ak.stock_financial_analysis_indicator(symbol=code)
        except:
            return pd.DataFrame()


def get_performance_express(code: str) -> pd.DataFrame:
    try:
        import akshare as ak
        return ak.stock_yjkb_em(symbol=code)
    except Exception:
        return pd.DataFrame()


def analyze_profitability(fin_df: pd.DataFrame) -> Dict:
    if fin_df.empty:
        return {}
    result = {"roe": {}, "roa": {}, "gross_margin": {}, "net_margin": {}}
    for _, row in fin_df.iterrows():
        period = str(row.get("日期", row.get("报告期", "")))
        if not period:
            continue
        for col in row.index:
            val = row.get(col)
            if val is None or (hasattr(pd, "isna") and pd.isna(val)):
                continue
            col_str = str(col)
            if "ROE" in col_str or "净资产收益率" in col_str:
                result["roe"][period] = float(val) if val else None
            elif "ROA" in col_str or "总资产收益率" in col_str:
                result["roa"][period] = float(val) if val else None
            elif "毛利率" in col_str:
                result["gross_margin"][period] = float(val) if val else None
            elif "净利率" in col_str:
                result["net_margin"][period] = float(val) if val else None
    return result


def analyze_growth(fin_df: pd.DataFrame) -> Dict:
    if fin_df.empty:
        return {}
    result = {"revenue_growth": {}, "profit_growth": {}, "eps_growth": {}}
    for _, row in fin_df.iterrows():
        period = str(row.get("日期", row.get("报告期", "")))
        if not period:
            continue
        for col in row.index:
            val = row.get(col)
            if val is None:
                continue
            col_str = str(col)
            if "营业总收入" in col_str and "增长" in col_str:
                result["revenue_growth"][period] = float(val) if val else None
            elif "净利润" in col_str and "增长" in col_str:
                result["profit_growth"][period] = float(val) if val else None
    return result


def analyze_valuation(code: str) -> Dict:
    result = {}
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if not target.empty:
            row = target.iloc[0]
            result["pe_ttm"] = float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else None
            result["pe_static"] = float(row.get("市盈率", 0)) if row.get("市盈率") else None
            result["pb"] = float(row.get("市净率", 0)) if row.get("市净率") else None
            result["ps_ttm"] = float(row.get("市销率", 0)) if row.get("市销率") else None
    except Exception:
        pass
    return result


def analyze_financial_health(fin_df: pd.DataFrame) -> Dict:
    if fin_df.empty:
        return {}
    score = 0
    issues = []
    for _, row in fin_df.iterrows():
        for col in row.index:
            val = row.get(col)
            if val is None:
                continue
            col_str = str(col)
            if "资产负债率" in col_str:
                try:
                    v = float(val)
                    if v > 70:
                        issues.append(f"资产负债率过高: {v:.1f}%")
                        score -= 1
                    elif v < 30:
                        score += 1
                except:
                    pass
            elif "流动比率" in col_str:
                try:
                    v = float(val)
                    if v < 1:
                        issues.append(f"流动比率过低: {v:.2f}")
                        score -= 1
                except:
                    pass
    level = "健康" if score > 0 else "需关注" if score < 0 else "中性"
    return {"score": score, "issues": issues, "level": level}


def full_fundamental_analysis(code: str) -> Dict:
    """综合基本面分析"""
    fin_df = get_financial_indicator(code)
    profitability = analyze_profitability(fin_df)
    growth = analyze_growth(fin_df)
    valuation = analyze_valuation(code)
    health = analyze_financial_health(fin_df)

    score = 0
    max_score = 0

    if profitability.get("roe"):
        latest_roe = list(profitability["roe"].values())[0] or 0
        if latest_roe > 15: score += 2
        elif latest_roe > 10: score += 1
        max_score += 2

    if growth.get("revenue_growth"):
        latest_rg = list(growth["revenue_growth"].values())[0] or 0
        if latest_rg > 30: score += 2
        elif latest_rg > 15: score += 1
        max_score += 2

    if growth.get("profit_growth"):
        latest_pg = list(growth["profit_growth"].values())[0] or 0
        if latest_pg > 30: score += 2
        elif latest_pg > 15: score += 1
        max_score += 2

    pe = valuation.get("pe_ttm") or 0
    if 0 < pe < 20: score += 2
    elif 0 < pe < 40: score += 1
    max_score += 2

    pb = valuation.get("pb") or 0
    if 0 < pb < 2: score += 1
    max_score += 1

    score += health.get("score", 0)
    max_score += 3

    final_score = (score / max(max_score, 1)) * 100
    if final_score >= 70: rating = "优"
    elif final_score >= 50: rating = "良"
    elif final_score >= 30: rating = "中"
    else: rating = "差"

    return {
        "code": code,
        "profitability": profitability,
        "growth": growth,
        "valuation": valuation,
        "health": health,
        "score": round(float(final_score), 2),
        "rating": rating,
    }


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="stock-fundamental-analysis")
    sub = parser.add_subparsers(dest="cmd")

    for cmd in ["fin", "express", "valuation", "full"]:
        p = sub.add_parser(cmd, help=cmd)
        p.add_argument("code")

    p = sub.add_parser("profit", help="盈利能力")
    p.add_argument("code")
    p = sub.add_parser("growth", help="成长性")
    p.add_argument("code")
    p = sub.add_parser("health", help="财务健康")
    p.add_argument("code")

    args = parser.parse_args()

    if args.cmd in ("fin", "express"):
        if args.cmd == "fin":
            df = get_financial_indicator(args.code)
        else:
            df = get_performance_express(args.code)
        if not df.empty:
            print(df.to_string())
        else:
            print("无数据")

    elif args.cmd == "valuation":
        v = analyze_valuation(args.code)
        for k, val in v.items():
            print(f"  {k}: {val}")

    elif args.cmd == "profit":
        fin = get_financial_indicator(args.code)
        r = analyze_profitability(fin)
        for k, v in r.items():
            if v:
                print(f"  {k}: {v}")

    elif args.cmd == "growth":
        fin = get_financial_indicator(args.code)
        r = analyze_growth(fin)
        for k, v in r.items():
            if v:
                print(f"  {k}: {v}")

    elif args.cmd == "health":
        fin = get_financial_indicator(args.code)
        r = analyze_financial_health(fin)
        print(f"等级: {r.get('level')}")
        for issue in r.get("issues", []):
            print(f"  - {issue}")

    elif args.cmd == "full":
        r = full_fundamental_analysis(args.code)
        import json
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
