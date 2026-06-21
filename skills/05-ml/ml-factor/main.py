#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ml-factor: ML多因子排序"""

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


def get_spot() -> pd.DataFrame:
    """获取全 A 股实时行情"""
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


def calc_factors(codes: List[str]) -> pd.DataFrame:
    """计算所有股票的因子"""
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
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def train(top_n: int = 500, model_name: str = "lightgbm") -> Dict:
    """训练 ML 因子模型"""
    spot = get_spot()
    if spot.empty:
        return {"error": "无法获取行情"}

    # 选活跃股票
    if "pct_change" in spot.columns:
        spot = spot[spot["pct_change"].notna()]
    if "total_mv" in spot.columns:
        spot = spot[spot["total_mv"] > 30e8]  # 市值>30亿
    codes = spot["code"].head(top_n).tolist()

    # 计算因子
    factors_df = calc_factors(codes)
    if factors_df.empty or len(factors_df) < 50:
        return {"error": "因子数据不足"}

    # 合并基础数据
    df = factors_df.merge(spot[["code", "pct_change", "pe", "pb", "total_mv", "turnover"]],
                          on="code", how="left")

    # 计算反转因子
    if "pe" in df.columns:
        df["value_pe"] = 1 / df["pe"].replace(0, np.nan)
    if "pb" in df.columns:
        df["value_pb"] = 1 / df["pb"].replace(0, np.nan)

    # 标签: 模拟未来收益 (使用历史波动率)
    df["label"] = df["momentum_20d"].fillna(0)

    # 训练
    feature_cols = ["momentum_5d", "momentum_20d", "volatility_20d", "volume_ratio",
                    "value_pe", "value_pb", "turnover", "total_mv"]
    feature_cols = [c for c in feature_cols if c in df.columns]

    df = df.dropna(subset=feature_cols + ["label"])
    if len(df) < 30:
        return {"error": "有效样本不足"}

    X = df[feature_cols]
    y = df["label"]

    # 模型
    if model_name == "lightgbm":
        try:
            from lightgbm import LGBMRegressor
            model = LGBMRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42, verbosity=-1)
        except ImportError:
            from sklearn.ensemble import GradientBoostingRegressor
            model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    elif model_name == "xgboost":
        try:
            from xgboost import XGBRegressor
            model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42, verbosity=0)
        except ImportError:
            from sklearn.ensemble import GradientBoostingRegressor
            model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    else:
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)

    model.fit(X, y)

    # 评估
    pred = model.predict(X)
    from sklearn.metrics import r2_score
    r2 = r2_score(y, pred)

    # 保存
    model_path = os.path.join(MODEL_DIR, f"factor_{model_name}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "features": feature_cols, "model_name": model_name}, f)

    return {
        "n_samples": len(df), "n_features": len(feature_cols),
        "model": model_name, "r2": round(r2, 4),
        "model_path": model_path,
    }


def rank(top_n: int = 30) -> pd.DataFrame:
    """全市场排序"""
    model_path = os.path.join(MODEL_DIR, "factor_lightgbm.pkl")
    if not os.path.exists(model_path):
        model_path = os.path.join(MODEL_DIR, "factor_xgboost.pkl")
    if not os.path.exists(model_path):
        # 尝试训练
        train_result = train()
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

    factors_df = calc_factors(codes)
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


def top_stocks(n: int = 20) -> pd.DataFrame:
    """Top N 股票"""
    return rank(top_n=n)


def main():
    parser = argparse.ArgumentParser(description="ml-factor")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("train", help="训练")
    p.add_argument("--top", type=int, default=500)
    p.add_argument("--model", default="lightgbm", choices=["lightgbm", "xgboost", "random_forest"])
    p = sub.add_parser("rank", help="全市场排序")
    p.add_argument("--top", type=int, default=30)
    p = sub.add_parser("top", help="Top N")
    p.add_argument("--n", type=int, default=20)
    p = sub.add_parser("evaluate", help="评估")
    args = parser.parse_args()

    if args.cmd == "train":
        r = train(args.top, args.model)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== 训练结果 ===")
            print(f"模型: {r['model']}")
            print(f"样本数: {r['n_samples']}, 特征数: {r['n_features']}")
            print(f"R²: {r['r2']}")
            print(f"模型已保存: {r['model_path']}")
    elif args.cmd == "rank":
        df = rank(args.top)
        if not df.empty and "name" in df.columns:
            print(f"\n=== ML 多因子排序 Top {args.top} ===")
            cols = [c for c in ["code", "name", "price", "pct_change", "score"] if c in df.columns]
            print(df[cols].to_string())
    elif args.cmd == "top":
        df = top_stocks(args.n)
        if not df.empty and "name" in df.columns:
            cols = [c for c in ["code", "name", "score"] if c in df.columns]
            print(df[cols].to_string())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
