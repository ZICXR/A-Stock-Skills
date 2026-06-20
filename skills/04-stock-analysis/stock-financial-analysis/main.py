#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-financial-analysis: 财务报表分析"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_income_statement(code: str) -> pd.DataFrame:
    """利润表"""
    try:
        import akshare as ak
        return ak.stock_profit_sheet_by_report_em(symbol=code)
    except Exception as e:
        print(f"获取利润表失败: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_balance_sheet(code: str) -> pd.DataFrame:
    """资产负债表"""
    try:
        import akshare as ak
        return ak.stock_balance_sheet_by_report_em(symbol=code)
    except Exception as e:
        print(f"获取资产负债表失败: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_cash_flow(code: str) -> pd.DataFrame:
    """现金流量表"""
    try:
        import akshare as ak
        return ak.stock_cash_flow_sheet_by_report_em(symbol=code)
    except Exception as e:
        print(f"获取现金流量表失败: {e}", file=sys.stderr)
        return pd.DataFrame()


def dupont_analysis(code: str) -> Dict:
    """杜邦分析
    ROE = 净利率 × 总资产周转率 × 权益乘数
    """
    try:
        import akshare as ak
        # 获取主要财务指标
        df = ak.stock_financial_abstract_ths(symbol=code)
        if df.empty:
            return {}

        # 提取关键指标
        result = {
            "ROE": None,
            "净利率": None,
            "总资产周转率": None,
            "权益乘数": None,
        }
        for _, row in df.iterrows():
            for col in df.columns:
                val = row.get(col)
                if val is None or (hasattr(pd, 'isna') and pd.isna(val)):
                    continue
                col_str = str(col)
                if "ROE" in col_str or "净资产收益率" in col_str:
                    result["ROE"] = float(val) if val else None
                elif "净利率" in col_str or "销售净利率" in col_str:
                    result["净利率"] = float(val) if val else None
                elif "总资产周转率" in col_str:
                    result["总资产周转率"] = float(val) if val else None
                elif "权益乘数" in col_str or "资产负债率" in col_str:
                    if "权益乘数" in col_str:
                        result["权益乘数"] = float(val) if val else None

        # 验证
        if all(result.get(k) for k in ["净利率", "总资产周转率", "权益乘数"]):
            roe_calc = result["净利率"] * result["总资产周转率"] * result["权益乘数"]
            result["ROE计算"] = round(roe_calc, 2)
        return result
    except Exception as e:
        print(f"杜邦分析失败: {e}", file=sys.stderr)
        return {}


def assess_finance_quality(code: str) -> Dict:
    """财务质量评估"""
    issues = []
    score = 100

    # 利润含金量
    try:
        import akshare as ak
        cf = ak.stock_cash_flow_sheet_by_report_em(symbol=code)
        if not cf.empty:
            for col in cf.columns:
                if "经营活动产生的现金流量净额" in str(col) or "经营现金流" in str(col):
                    cf_val = float(cf[col].iloc[0])
                    break
            else:
                cf_val = None
            if cf_val is not None and cf_val < 0:
                issues.append("经营现金流为负, 利润质量存疑")
                score -= 20
    except Exception:
        pass

    # 资产负债率
    try:
        import akshare as ak
        df = ak.stock_financial_abstract_ths(symbol=code)
        if not df.empty:
            for _, row in df.iterrows():
                for col in df.columns:
                    if "资产负债率" in str(col):
                        v = float(row[col]) if row[col] else 0
                        if v > 70:
                            issues.append(f"资产负债率过高: {v:.1f}%")
                            score -= 15
                        break
                break
    except Exception:
        pass

    level = "优" if score >= 80 else "良" if score >= 60 else "中" if score >= 40 else "差"
    return {"score": max(0, score), "level": level, "issues": issues}


def main():
    parser = argparse.ArgumentParser(description="stock-financial-analysis")
    sub = parser.add_subparsers(dest="cmd")
    for cmd in ["income", "balance", "cashflow", "dupont", "quality"]:
        p = sub.add_parser(cmd)
        p.add_argument("code")
    args = parser.parse_args()

    if args.cmd == "income":
        df = get_income_statement(args.code)
        if not df.empty:
            print(df.head(8).to_string())
    elif args.cmd == "balance":
        df = get_balance_sheet(args.code)
        if not df.empty:
            print(df.head(8).to_string())
    elif args.cmd == "cashflow":
        df = get_cash_flow(args.code)
        if not df.empty:
            print(df.head(8).to_string())
    elif args.cmd == "dupont":
        r = dupont_analysis(args.code)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "quality":
        r = assess_finance_quality(args.code)
        print(f"评分: {r.get('score')} ({r.get('level')})")
        for issue in r.get("issues", []):
            print(f"  - {issue}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
