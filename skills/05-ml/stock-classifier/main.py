#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-classifier: ML涨跌分类预测"""

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


def get_kline(code: str, days: int = 730) -> pd.DataFrame:
    """获取2年K线数据"""
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


# ============================================================
# 特征工程
# ============================================================
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """构建特征"""
    if df.empty or len(df) < 60:
        return df
    df = df.copy()

    # 价格类
    for p in [5, 10, 20, 60]:
        df[f"MA{p}"] = df["close"].rolling(p).mean()
        df[f"close_ma{p}_ratio"] = df["close"] / df[f"MA{p}"]

    # 动量类
    for d in [1, 5, 10, 20]:
        df[f"returns_{d}d"] = df["close"].pct_change(d)

    # 波动类
    df["volatility_20"] = df["close"].pct_change().rolling(20).std()
    tr = pd.concat([
        df["high"] - df["low"],
        abs(df["high"] - df["close"].shift()),
        abs(df["low"] - df["close"].shift()),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["atr_pct"] = df["atr_14"] / df["close"]

    # 成交量类
    if "volume" in df.columns:
        df["volume_ma5"] = df["volume"].rolling(5).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma5"]
        df["volume_change"] = df["volume"].pct_change()

    # 技术指标
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - 100 / (1 + rs)

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    df["macd_dif"] = dif
    df["macd_dea"] = dea
    df["macd_hist"] = (dif - dea) * 2

    # KDJ
    low_n = df["low"].rolling(9).min()
    high_n = df["high"].rolling(9).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    df["kdj_k"] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df["kdj_d"] = df["kdj_k"].ewm(alpha=1/3, adjust=False).mean()
    df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]

    # 价格位置 (close 在 N 日区间的位置)
    for p in [10, 20, 60]:
        df[f"close_position_{p}"] = (df["close"] - df["low"].rolling(p).min()) / (
            df["high"].rolling(p).max() - df["low"].rolling(p).min()
        )

    return df


def build_label(df: pd.DataFrame, horizon: int = 5, up_th: float = 0.03, down_th: float = -0.03) -> pd.Series:
    """构建标签
    1=涨, 0=震荡, -1=跌
    """
    future_ret = df["close"].shift(-horizon) / df["close"] - 1
    label = pd.Series(0, index=df.index)
    label[future_ret > up_th] = 1
    label[future_ret < down_th] = -1
    return label


# ============================================================
# 模型
# ============================================================
MODEL_DIR = os.path.expanduser("~/.astock_skills/models")
os.makedirs(MODEL_DIR, exist_ok=True)


def get_model(name: str):
    """获取模型"""
    if name == "xgboost":
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(
                n_estimators=100, max_depth=5, learning_rate=0.1,
                objective="multi:softprob", num_class=3, random_state=42,
                verbosity=0
            )
        except ImportError:
            print("xgboost 未安装, 使用 RandomForest")
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    elif name == "lightgbm":
        try:
            from lightgbm import LGBMClassifier
            return LGBMClassifier(
                n_estimators=100, max_depth=5, learning_rate=0.1,
                objective="multiclass", num_class=3, random_state=42,
                verbosity=-1
            )
        except ImportError:
            print("lightgbm 未安装, 使用 RandomForest")
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    elif name == "random_forest":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    else:  # logistic
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(max_iter=1000, random_state=42)


def get_feature_cols(df: pd.DataFrame) -> List[str]:
    """获取特征列"""
    exclude = {"date", "code", "name", "open", "high", "low", "close", "volume"}
    return [c for c in df.columns if c not in exclude and df[c].dtype in [np.float64, np.int64, np.float32, np.int32]]


def train(code: str, horizon: int = 5, model_name: str = "xgboost") -> Dict:
    """训练模型"""
    df = get_kline(code, days=730)
    if df.empty or len(df) < 100:
        return {"error": "数据不足"}
    df = build_features(df)
    df["label"] = build_label(df, horizon=horizon)
    df = df.dropna()
    if len(df) < 50:
        return {"error": "数据太少"}

    feature_cols = get_feature_cols(df)
    if "label" in feature_cols:
        feature_cols.remove("label")

    X = df[feature_cols]
    y = df["label"]
    y_mapped = y + 1  # -1→0, 0→1, 1→2

    # 时序分割 (避免未来数据)
    split = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y_mapped.iloc[:split], y_mapped.iloc[split:]

    model = get_model(model_name)
    model.fit(X_train, y_train)

    # 评估
    from sklearn.metrics import accuracy_score, f1_score
    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    test_f1 = f1_score(y_test, model.predict(X_test), average="macro")

    # 保存
    model_path = os.path.join(MODEL_DIR, f"{code}_h{horizon}_{model_name}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "features": feature_cols, "horizon": horizon}, f)

    return {
        "code": code, "horizon": horizon, "model": model_name,
        "train_acc": round(train_acc, 4),
        "test_acc": round(test_acc, 4),
        "test_f1": round(test_f1, 4),
        "n_features": len(feature_cols),
        "n_samples": len(df),
        "model_path": model_path,
    }


def predict(code: str, horizon: int = 5, model_name: str = "xgboost") -> Dict:
    """预测"""
    model_path = os.path.join(MODEL_DIR, f"{code}_h{horizon}_{model_name}.pkl")
    if not os.path.exists(model_path):
        return {"error": f"模型未训练, 请先运行: python main.py train --code {code}"}
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

    proba = model.predict_proba(X)[0]
    pred = model.predict(X)[0] - 1  # 反映射 0→-1, 1→0, 2→1

    if pred == 1:
        signal = "买入"
    elif pred == -1:
        signal = "卖出"
    else:
        signal = "观望"

    confidence = "高" if max(proba) > 0.6 else "中" if max(proba) > 0.4 else "低"
    return {
        "code": code,
        "horizon": horizon,
        "signal": signal,
        "prob_up": round(float(proba[2]), 4),
        "prob_flat": round(float(proba[1]), 4),
        "prob_down": round(float(proba[0]), 4),
        "confidence": confidence,
    }


def feature_importance(code: str, horizon: int = 5, model_name: str = "xgboost", top_n: int = 10) -> Dict:
    """特征重要性"""
    model_path = os.path.join(MODEL_DIR, f"{code}_h{horizon}_{model_name}.pkl")
    if not os.path.exists(model_path):
        return {"error": "模型未训练"}
    with open(model_path, "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    features = saved["features"]

    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
        idx = np.argsort(imp)[::-1][:top_n]
        return {
            "top_features": [
                {"feature": features[i], "importance": round(float(imp[i]), 4)}
                for i in idx
            ]
        }
    return {"error": "该模型不支持特征重要性"}


def batch_predict(codes: List[str], horizon: int = 5) -> pd.DataFrame:
    """批量预测"""
    results = []
    for code in codes:
        r = predict(code, horizon)
        if "error" not in r:
            r["code"] = code
            results.append(r)
    return pd.DataFrame(results)


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="stock-classifier")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("train", help="训练")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--model", default="xgboost", choices=["xgboost", "lightgbm", "random_forest", "logistic"])
    p = sub.add_parser("predict", help="预测")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--model", default="xgboost")
    p = sub.add_parser("importance", help="特征重要性")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--model", default="xgboost")
    p = sub.add_parser("batch", help="批量预测")
    p.add_argument("--codes", required=True)
    p.add_argument("--horizon", type=int, default=5)
    args = parser.parse_args()

    if args.cmd == "train":
        r = train(args.code, args.horizon, args.model)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== 训练结果 ===")
            print(f"代码: {r['code']}")
            print(f"模型: {r['model']}")
            print(f"样本数: {r['n_samples']}, 特征数: {r['n_features']}")
            print(f"训练准确率: {r['train_acc']}")
            print(f"测试准确率: {r['test_acc']}")
            print(f"测试 F1:    {r['test_f1']}")
            print(f"模型已保存: {r['model_path']}")
    elif args.cmd == "predict":
        r = predict(args.code, args.horizon, args.model)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== 预测结果 ===")
            print(f"代码: {r['code']}")
            print(f"信号: {r['signal']} (置信度: {r['confidence']})")
            print(f"上涨概率: {r['prob_up']*100:.1f}%")
            print(f"震荡概率: {r['prob_flat']*100:.1f}%")
            print(f"下跌概率: {r['prob_down']*100:.1f}%")
    elif args.cmd == "importance":
        r = feature_importance(args.code, args.horizon, args.model)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== Top {len(r['top_features'])} 特征 ===")
            for f in r["top_features"]:
                print(f"  {f['feature']:25s} {f['importance']:.4f}")
    elif args.cmd == "batch":
        codes = [c.strip() for c in args.codes.split(",")]
        df = batch_predict(codes, args.horizon)
        if not df.empty:
            print(df[["code", "signal", "prob_up", "prob_down", "confidence"]].to_string())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
