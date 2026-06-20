#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""factor-analysis: 多因子分析"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


def get_kline(code: str, days: int = 120) -> pd.DataFrame:
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=str(code).zfill(6), period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if df.empty:
            return df
        df.columns = [c.lower() for c in df.columns]
        return df.tail(days).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def get_basic(code: str) -> Dict:
    """获取基本面数据"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return {}
        row = target.iloc[0]
        return {
            "pe_ttm": float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else None,
            "pb": float(row.get("市净率", 0)) if row.get("市净率") else None,
        }
    except Exception:
        return {}


def calc_factor(code: str, factor_name: str) -> float:
    """计算单因子"""
    if factor_name == "momentum_20":
        df = get_kline(code, days=30)
        if df.empty or len(df) < 21:
            return 0
        return round((df["close"].iloc[-1] - df["close"].iloc[-21]) / df["close"].iloc[-21] * 100, 2)
    elif factor_name == "momentum_60":
        df = get_kline(code, days=70)
        if df.empty or len(df) < 61:
            return 0
        return round((df["close"].iloc[-1] - df["close"].iloc[-61]) / df["close"].iloc[-61] * 100, 2)
    elif factor_name == "value_pe":
        b = get_basic(code)
        pe = b.get("pe_ttm", 0) or 0
        return round(1 / pe, 4) if pe > 0 else 0
    elif factor_name == "value_pb":
        b = get_basic(code)
        pb = b.get("pb", 0) or 0
        return round(1 / pb, 4) if pb > 0 else 0
    elif factor_name == "volatility_20":
        df = get_kline(code, days=30)
        if df.empty or len(df) < 20:
            return 0
        return round(df["close"].pct_change().tail(20).std() * 100, 2)
    elif factor_name == "turnover_20":
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            target = df[df["代码"].astype(str) == str(code).zfill(6)]
            if target.empty:
                return 0
            return float(target.iloc[0].get("换手率", 0))
        except Exception:
            return 0
    elif factor_name == "quality_roe":
        try:
            import akshare as ak
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df.empty:
                return 0
            for _, row in df.iterrows():
                for col in df.columns:
                    if "ROE" in str(col) or "净资产收益率" in str(col):
                        v = float(row[col]) if row[col] else 0
                        return round(v, 2)
            return 0
        except Exception:
            return 0
    elif factor_name == "growth_profit":
        try:
            import akshare as ak
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df.empty:
                return 0
            for _, row in df.iterrows():
                for col in df.columns:
                    if "净利润" in str(col) and "增长" in str(col):
                        v = float(row[col]) if row[col] else 0
                        return round(v, 2)
            return 0
        except Exception:
            return 0
    return 0


def calc_all_factors(code: str) -> Dict:
    """计算所有因子"""
    return {
        "momentum_20": calc_factor(code, "momentum_20"),
        "momentum_60": calc_factor(code, "momentum_60"),
        "value_pe": calc_factor(code, "value_pe"),
        "value_pb": calc_factor(code, "value_pb"),
        "quality_roe": calc_factor(code, "quality_roe"),
        "growth_profit": calc_factor(code, "growth_profit"),
        "volatility_20": calc_factor(code, "volatility_20"),
    }


def factor_quantile(factor_values: List[float], n: int = 5) -> List[int]:
    """因子分组 (1~n)"""
    arr = np.array(factor_values)
    quantiles = np.quantile(arr[~np.isnan(arr)], np.linspace(0, 1, n + 1))
    result = []
    for v in factor_values:
        if np.isnan(v):
            result.append(0)
            continue
        for i in range(n):
            if v <= quantiles[i + 1]:
                result.append(i + 1)
                break
    return result


def multi_factor_score(codes: List[str], weights: Dict = None) -> List[Dict]:
    """多因子综合评分"""
    if weights is None:
        weights = {
            "momentum_20": 0.2,
            "momentum_60": 0.1,
            "value_pe": 0.15,
            "value_pb": 0.15,
            "quality_roe": 0.2,
            "growth_profit": 0.15,
            "volatility_20": -0.05,  # 低波动为佳
        }
    results = []
    for code in codes:
        factors = calc_all_factors(code)
        score = 0
        for fname, weight in weights.items():
            val = factors.get(fname, 0)
            score += val * weight
        results.append({
            "code": code,
            "score": round(score, 4),
            "factors": factors,
        })
    return sorted(results, key=lambda x: x["score"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="factor-analysis")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("calc", help="计算单因子")
    p.add_argument("code")
    p.add_argument("factor")
    sub.add_parser("all", help="所有因子").add_argument("code")
    p = sub.add_parser("score", help="多因子评分")
    p.add_argument("--codes", help="逗号分隔")
    p.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    if args.cmd == "calc":
        v = calc_factor(args.code, args.factor)
        print(f"{args.factor}: {v}")
    elif args.cmd == "all":
        r = calc_all_factors(args.code)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "score":
        if args.codes:
            codes = [c.strip() for c in args.codes.split(",")]
        else:
            # 默认全 A 股前 100
            try:
                import akshare as ak
                df = ak.stock_zh_a_spot_em()
                codes = df["代码"].astype(str).head(50).tolist()
            except Exception:
                codes = ["000001", "600519", "300750"]
        r = multi_factor_score(codes)
        for i, item in enumerate(r[:args.top], 1):
            print(f"{i}. {item['code']}: {item['score']:.4f}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
