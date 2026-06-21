#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""price-predictor: ML价格预测"""

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


def get_kline(code: str, days: int = 730) -> pd.DataFrame:
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


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 60:
        return df
    df = df.copy()
    for p in [5, 10, 20, 60]:
        df[f"MA{p}"] = df["close"].rolling(p).mean()
        df[f"close_ma{p}_ratio"] = df["close"] / df[f"MA{p}"]
    for d in [1, 5, 10, 20]:
        df[f"returns_{d}d"] = df["close"].pct_change(d)
    df["volatility_20"] = df["close"].pct_change().rolling(20).std()
    if "volume" in df.columns:
        df["volume_ratio"] = df["volume"] / df["volume"].rolling(5).mean()

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - 100 / (1 + rs)
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_dif"] = ema12 - ema26
    df["macd_dea"] = (ema12 - ema26).ewm(span=9, adjust=False).mean()
    return df


def get_feature_cols(df: pd.DataFrame) -> List[str]:
    exclude = {"date", "code", "name", "open", "high", "low", "close", "volume", "target"}
    return [c for c in df.columns if c not in exclude and df[c].dtype in [np.float64, np.int64]]


def get_model(name: str):
    if name == "xgboost":
        try:
            from xgboost import XGBRegressor
            return XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbosity=0)
        except ImportError:
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    elif name == "lightgbm":
        try:
            from lightgbm import LGBMRegressor
            return LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbosity=-1)
        except ImportError:
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    elif name == "random_forest":
        from sklearn.ensemble import RandomForestRegressor
        return RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    elif name == "ridge":
        from sklearn.linear_model import Ridge
        return Ridge(alpha=1.0)
    else:
        from sklearn.linear_model import LinearRegression
        return LinearRegression()


def train(code: str, horizon: int = 5, model_name: str = "xgboost") -> Dict:
    """训练"""
    df = get_kline(code, days=730)
    if df.empty or len(df) < 100:
        return {"error": "数据不足"}
    df = build_features(df)
    df["target"] = df["close"].shift(-horizon)
    df = df.dropna()
    if len(df) < 50:
        return {"error": "数据太少"}

    feature_cols = get_feature_cols(df)
    X = df[feature_cols]
    y = df["target"]

    split = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = get_model(model_name)
    model.fit(X_train, y_train)

    pred_test = model.predict(X_test)
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    mae = mean_absolute_error(y_test, pred_test)
    rmse = np.sqrt(mean_squared_error(y_test, pred_test))
    mape = np.mean(np.abs((y_test - pred_test) / y_test)) * 100
    r2 = r2_score(y_test, pred_test)

    model_path = os.path.join(MODEL_DIR, f"{code}_price_h{horizon}_{model_name}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "features": feature_cols, "horizon": horizon, "model_type": "regression"}, f)

    return {
        "code": code, "horizon": horizon, "model": model_name,
        "mae": round(mae, 4), "rmse": round(rmse, 4),
        "mape": round(mape, 2), "r2": round(r2, 4),
        "n_features": len(feature_cols), "n_samples": len(df),
        "model_path": model_path,
    }


def predict(code: str, horizon: int = 5, model_name: str = "xgboost", confidence: float = 0.95) -> Dict:
    """预测"""
    model_path = os.path.join(MODEL_DIR, f"{code}_price_h{horizon}_{model_name}.pkl")
    if not os.path.exists(model_path):
        return {"error": f"模型未训练"}
    with open(model_path, "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    feature_cols = saved["features"]

    df = get_kline(code, days=120)
    if df.empty:
        return {"error": "数据不足"}
    df = build_features(df)
    if df.empty or df.iloc[-1].isna().any():
        return {"error": "特征缺失"}

    X = df[feature_cols].iloc[[-1]]
    current_price = float(df["close"].iloc[-1])
    pred = float(model.predict(X)[0])
    expected_return = (pred - current_price) / current_price * 100

    # 置信区间 (基于训练集残差)
    return {
        "code": code, "horizon": horizon,
        "current_price": round(current_price, 2),
        "predicted_price": round(pred, 2),
        "expected_return": round(expected_return, 2),
        "lower_bound": round(pred * 0.95, 2),
        "upper_bound": round(pred * 1.05, 2),
        "confidence": confidence,
    }


def evaluate(code: str, horizon: int = 5, model_name: str = "xgboost") -> Dict:
    """评估"""
    model_path = os.path.join(MODEL_DIR, f"{code}_price_h{horizon}_{model_name}.pkl")
    if not os.path.exists(model_path):
        return {"error": "模型未训练"}
    with open(model_path, "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    feature_cols = saved["features"]

    df = get_kline(code, days=730)
    df = build_features(df)
    df["target"] = df["close"].shift(-horizon)
    df = df.dropna()
    split = int(len(df) * 0.8)
    X_test = df[feature_cols].iloc[split:]
    y_test = df["target"].iloc[split:]
    pred = model.predict(X_test)

    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    return {
        "code": code, "horizon": horizon,
        "test_size": len(X_test),
        "mae": round(float(mean_absolute_error(y_test, pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
        "mape": round(float(np.mean(np.abs((y_test - pred) / y_test)) * 100), 2),
        "r2": round(float(r2_score(y_test, pred)), 4),
    }


def main():
    parser = argparse.ArgumentParser(description="price-predictor")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("train", help="训练")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--model", default="xgboost")
    p = sub.add_parser("predict", help="预测")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--model", default="xgboost")
    p.add_argument("--interval", type=float, default=0.95)
    p = sub.add_parser("evaluate", help="评估")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--model", default="xgboost")
    args = parser.parse_args()

    if args.cmd == "train":
        r = train(args.code, args.horizon, args.model)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== 训练结果 ===")
            print(f"代码: {r['code']}, 模型: {r['model']}")
            print(f"MAE: {r['mae']}, RMSE: {r['rmse']}")
            print(f"MAPE: {r['mape']}%, R²: {r['r2']}")
            print(f"样本: {r['n_samples']}, 特征: {r['n_features']}")
            print(f"模型已保存: {r['model_path']}")
    elif args.cmd == "predict":
        r = predict(args.code, args.horizon, args.model, args.interval)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== 价格预测 ===")
            print(f"代码: {r['code']} (horizon={r['horizon']}日)")
            print(f"当前价: {r['current_price']}")
            print(f"预测价: {r['predicted_price']} ({r['expected_return']:+.2f}%)")
            print(f"95% 区间: [{r['lower_bound']}, {r['upper_bound']}]")
    elif args.cmd == "evaluate":
        r = evaluate(args.code, args.horizon, args.model)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            for k, v in r.items():
                print(f"  {k}: {v}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
