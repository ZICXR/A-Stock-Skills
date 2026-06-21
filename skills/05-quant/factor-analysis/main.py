#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""factor-analysis: 多因子分析 (传统 + ML 增强版)

合并: factor-analysis + ml-factor + multi-strategy 的因子计算
"""

import os
import sys
import pickle
import argparse
import warnings
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

MODEL_DIR = os.path.expanduser("~/.astock_skills/models")
os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# 因子计算
# ============================================================
def get_kline(code: str, days: int = 365) -> pd.DataFrame:
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=int(days * 1.2))).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=str(code).zfill(6), period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if df.empty:
            return df
        df.columns = [c.lower() for c in df.columns]
        return df.tail(days).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def get_spot() -> pd.DataFrame:
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df.empty:
            return df
        rename_map = {
            "代码": "code", "名称": "name", "最新价": "price",
            "涨跌幅": "pct_change", "换手率": "turnover",
            "市盈率-动态": "pe", "市净率": "pb",
            "总市值": "total_mv", "流通市值": "circ_mv", "所属行业": "industry",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        if "code" in df.columns:
            df["code"] = df["code"].astype(str)
        return df
    except Exception:
        return pd.DataFrame()


def calc_factor(code: str, factor_name: str) -> float:
    """单因子计算"""
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
        spot = get_spot()
        if spot.empty:
            return 0
        target = spot[spot["code"] == str(code).zfill(6)]
        if target.empty:
            return 0
        pe = float(target.iloc[0].get("pe", 0)) or 0
        return round(1 / pe, 4) if pe > 0 else 0
    elif factor_name == "value_pb":
        spot = get_spot()
        if spot.empty:
            return 0
        target = spot[spot["code"] == str(code).zfill(6)]
        if target.empty:
            return 0
        pb = float(target.iloc[0].get("pb", 0)) or 0
        return round(1 / pb, 4) if pb > 0 else 0
    elif factor_name == "quality_roe":
        try:
            import akshare as ak
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df.empty:
                return 0
            for _, row in df.iterrows():
                for col in df.columns:
                    if "ROE" in str(col) or "净资产收益率" in str(col):
                        return round(float(row[col]) if row[col] else 0, 2)
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
                        return round(float(row[col]) if row[col] else 0, 2)
            return 0
        except Exception:
            return 0
    elif factor_name == "volatility_20":
        df = get_kline(code, days=30)
        if df.empty or len(df) < 20:
            return 0
        return round(df["close"].pct_change().tail(20).std() * 100, 2)
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


# ============================================================
# 传统因子评分
# ============================================================
def multi_factor_score(codes: List[str], weights: Dict = None) -> List[Dict]:
    """多因子综合评分 (传统)"""
    if weights is None:
        weights = {
            "momentum_20": 0.2, "momentum_60": 0.1,
            "value_pe": 0.15, "value_pb": 0.15,
            "quality_roe": 0.2, "growth_profit": 0.15,
            "volatility_20": -0.05,
        }
    results = []
    for code in codes:
        factors = calc_all_factors(code)
        score = sum(factors.get(k, 0) * w for k, w in weights.items())
        results.append({"code": code, "score": round(score, 4), "factors": factors})
    return sorted(results, key=lambda x: x["score"], reverse=True)


# ============================================================
# ML 因子评分
# ============================================================
def calc_factors_batch(codes: List[str]) -> pd.DataFrame:
    """批量计算因子 (用于 ML 训练)"""
    rows = []
    for code in codes:
        try:
            import akshare as ak
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")
            df = ak.stock_zh_a_hist(symbol=code.zfill(6), period="daily",
                                     start_date=start, end_date=end, adjust="qfq")
            if df.empty or len(df) < 20:
                continue
            df.columns = [c.lower() for c in df.columns]
            row = {"code": code.zfill(6)}
            row["momentum_5d"] = (df["close"].iloc[-1] - df["close"].iloc[-6]) / df["close"].iloc[-6] * 100 if len(df) >= 6 else 0
            row["momentum_20d"] = (df["close"].iloc[-1] - df["close"].iloc[-21]) / df["close"].iloc[-21] * 100 if len(df) >= 21 else 0
            row["volatility_20d"] = df["close"].pct_change().tail(20).std() * 100
            if "volume" in df.columns:
                row["volume_ratio"] = df["volume"].iloc[-1] / df["volume"].tail(5).mean() if df["volume"].tail(5).mean() else 1
            rows.append(row)
        except Exception:
            continue
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def train_ml_model(top_n: int = 500, model_name: str = "lightgbm") -> Dict:
    """训练 ML 因子模型"""
    spot = get_spot()
    if spot.empty:
        return {"error": "无法获取行情"}
    if "pct_change" in spot.columns:
        spot = spot[spot["pct_change"].notna()]
    if "total_mv" in spot.columns:
        spot = spot[spot["total_mv"] > 30e8]
    codes = spot["code"].head(top_n).tolist()

    factors_df = calc_factors_batch(codes)
    if factors_df.empty or len(factors_df) < 50:
        return {"error": "因子数据不足"}

    df = factors_df.merge(spot[["code", "pct_change", "pe", "pb", "total_mv", "turnover"]],
                          on="code", how="left")
    if "pe" in df.columns:
        df["value_pe"] = 1 / df["pe"].replace(0, np.nan)
    if "pb" in df.columns:
        df["value_pb"] = 1 / df["pb"].replace(0, np.nan)

    df["label"] = df["momentum_20d"].fillna(0)

    feature_cols = ["momentum_5d", "momentum_20d", "volatility_20d", "volume_ratio",
                    "value_pe", "value_pb", "turnover", "total_mv"]
    feature_cols = [c for c in feature_cols if c in df.columns]
    df = df.dropna(subset=feature_cols + ["label"])
    if len(df) < 30:
        return {"error": "有效样本不足"}

    X = df[feature_cols]
    y = df["label"]

    if model_name == "lightgbm":
        try:
            from lightgbm import LGBMRegressor
            model = LGBMRegressor(n_estimators=100, max_depth=4, learning_rate=0.1,
                                  random_state=42, verbosity=-1)
        except ImportError:
            from sklearn.ensemble import GradientBoostingRegressor
            model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    elif model_name == "xgboost":
        try:
            from xgboost import XGBRegressor
            model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1,
                                 random_state=42, verbosity=0)
        except ImportError:
            from sklearn.ensemble import GradientBoostingRegressor
            model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    else:
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)

    model.fit(X, y)
    from sklearn.metrics import r2_score
    r2 = r2_score(y, model.predict(X))

    model_path = os.path.join(MODEL_DIR, f"factor_{model_name}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "features": feature_cols, "model_name": model_name}, f)

    return {"n_samples": len(df), "r2": round(r2, 4), "model_path": model_path, "model": model_name}


def ml_rank(top_n: int = 30) -> pd.DataFrame:
    """ML 因子排序"""
    model_path = os.path.join(MODEL_DIR, "factor_lightgbm.pkl")
    if not os.path.exists(model_path):
        model_path = os.path.join(MODEL_DIR, "factor_xgboost.pkl")
    if not os.path.exists(model_path):
        train_result = train_ml_model()
        if "error" in train_result:
            return pd.DataFrame({"error": [train_result["error"]]})

    with open(model_path, "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    features = saved["features"]

    spot = get_spot()
    if spot.empty:
        return pd.DataFrame()
    if "total_mv" in spot.columns:
        spot = spot[spot["total_mv"] > 30e8]
    codes = spot["code"].head(500).tolist()

    factors_df = calc_factors_batch(codes)
    df = factors_df.merge(spot[["code", "name", "price", "pct_change", "pe", "pb", "total_mv", "turnover"]],
                          on="code", how="left")
    if "pe" in df.columns:
        df["value_pe"] = 1 / df["pe"].replace(0, np.nan)
    if "pb" in df.columns:
        df["value_pb"] = 1 / df["pb"].replace(0, np.nan)
    df = df.dropna(subset=features)
    if df.empty:
        return df

    X = df[features]
    df["score"] = model.predict(X)
    df["score"] = (df["score"] - df["score"].min()) / (df["score"].max() - df["score"].min()) * 100
    return df.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)


# ============================================================
# IC 计算
# ============================================================
def calc_ic(factor_values: List[float], returns: List[float]) -> Dict:
    """计算 IC (Information Coefficient)"""
    if len(factor_values) != len(returns) or len(factor_values) < 2:
        return {}
    arr_f = np.array(factor_values)
    arr_r = np.array(returns)
    valid = ~(np.isnan(arr_f) | np.isnan(arr_r))
    if valid.sum() < 2:
        return {}
    corr = np.corrcoef(arr_f[valid], arr_r[valid])[0, 1]
    abs_corr = abs(corr)
    if abs_corr > 0.05:
        level = "强"
    elif abs_corr > 0.02:
        level = "中"
    else:
        level = "弱"
    return {"ic": round(float(corr), 4), "abs_ic": round(float(abs_corr), 4), "level": level}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="factor-analysis (传统+ML)")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("calc", help="单因子")
    p.add_argument("code")
    p.add_argument("factor")
    sub.add_parser("all", help="所有因子").add_argument("code")
    p = sub.add_parser("score", help="多因子评分 (传统)")
    p.add_argument("--codes", help="股票列表")
    p.add_argument("--top", type=int, default=20)

    # ML 相关
    p = sub.add_parser("train-ml", help="训练 ML 模型")
    p.add_argument("--top", type=int, default=500)
    p.add_argument("--model", default="lightgbm", choices=["lightgbm", "xgboost", "random_forest"])
    p = sub.add_parser("ml-rank", help="ML 排序")
    p.add_argument("--top", type=int, default=30)

    # IC
    p = sub.add_parser("ic", help="计算 IC")
    p.add_argument("--factor", required=True)
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
            try:
                import akshare as ak
                df = ak.stock_zh_a_spot_em()
                codes = df["代码"].astype(str).head(50).tolist()
            except Exception:
                codes = ["000001", "600519", "300750"]
        r = multi_factor_score(codes)
        for i, item in enumerate(r[:args.top], 1):
            print(f"{i}. {item['code']}: {item['score']:.4f}")
    elif args.cmd == "train-ml":
        r = train_ml_model(args.top, args.model)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== ML 训练结果 ===")
            print(f"模型: {r['model']}, 样本: {r['n_samples']}, R²: {r['r2']}")
            print(f"模型已保存: {r['model_path']}")
    elif args.cmd == "ml-rank":
        df = ml_rank(args.top)
        if not df.empty and "name" in df.columns:
            cols = [c for c in ["code", "name", "score"] if c in df.columns]
            print(df[cols].to_string())
        else:
            print("无数据, 请先训练: train-ml")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
