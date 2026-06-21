#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lstm-forecaster: 简易LSTM时序预测 (纯numpy, 无PyTorch)"""

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


# ============================================================
# 简易 LSTM 实现 (基于 numpy)
# ============================================================
class SimpleLSTM:
    """简易 LSTM (标准版) - 教学用

    使用 numpy 实现, 包含:
    - 遗忘门 (forget gate)
    - 输入门 (input gate)
    - 输出门 (output gate)
    - 候选细胞状态

    ⚠️ 这是简化教学实现, 实际生产请用 PyTorch/TensorFlow
    """

    def __init__(self, input_size: int = 1, hidden_size: int = 32, output_size: int = 1, lr: float = 0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.lr = lr

        # 初始化权重 (Xavier)
        scale = np.sqrt(2.0 / (input_size + hidden_size))
        self.Wf = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.Wi = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.Wc = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.Wo = np.random.randn(hidden_size, input_size + hidden_size) * scale

        self.bf = np.zeros((hidden_size, 1))
        self.bi = np.zeros((hidden_size, 1))
        self.bc = np.zeros((hidden_size, 1))
        self.bo = np.zeros((hidden_size, 1))

        self.Wy = np.random.randn(output_size, hidden_size) * 0.1
        self.by = np.zeros((output_size, 1))

    def sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -50, 50)))

    def forward(self, X):
        """X shape: (seq_len, input_size)"""
        h = np.zeros((self.hidden_size, 1))
        c = np.zeros((self.hidden_size, 1))
        outputs = []
        for x in X:
            x = x.reshape(-1, 1) if x.ndim == 1 else x.reshape(-1, 1)
            concat = np.vstack([h, x])
            f = self.sigmoid(self.Wf @ concat + self.bf)
            i = self.sigmoid(self.Wi @ concat + self.bi)
            c_tilde = np.tanh(self.Wc @ concat + self.bc)
            o = self.sigmoid(self.Wo @ concat + self.bo)
            c = f * c + i * c_tilde
            h = o * np.tanh(c)
            y = self.Wy @ h + self.by
            outputs.append(y.flatten()[0])
        return outputs, h, c

    def train(self, X_list, y_list, epochs: int = 50, batch_size: int = 16):
        """简单训练"""
        losses = []
        for epoch in range(epochs):
            total_loss = 0
            indices = np.random.permutation(len(X_list))[:batch_size]
            for idx in indices:
                X = X_list[idx]
                y_true = y_list[idx]
                # Forward
                outputs, h, c = self.forward(X)
                pred = np.array(outputs[-self.output_size:]) if len(outputs) >= self.output_size else np.array(outputs)
                if len(pred) < self.output_size:
                    pred = np.concatenate([pred, np.zeros(self.output_size - len(pred))])
                # Loss
                loss = np.mean((pred - y_true) ** 2)
                total_loss += loss
                # 简化版: 仅更新输出层
                grad_y = 2 * (pred - y_true) / len(y_true)
                self.Wy -= self.lr * np.outer(grad_y, h.flatten())
                self.by -= self.lr * grad_y.reshape(-1, 1)
            losses.append(total_loss / max(len(indices), 1))
        return losses


# ============================================================
# 训练和预测
# ============================================================
def prepare_sequences(prices: np.ndarray, lookback: int = 20, horizon: int = 5):
    """准备序列数据"""
    X, y = [], []
    for i in range(len(prices) - lookback - horizon + 1):
        X.append(prices[i:i + lookback].reshape(-1, 1))
        y.append(prices[i + lookback:i + lookback + horizon])
    return X, y


def normalize(prices: np.ndarray):
    mean = prices.mean()
    std = prices.std() + 1e-8
    return (prices - mean) / std, mean, std


def denormalize(norm_prices: np.ndarray, mean: float, std: float):
    return norm_prices * std + mean


def train(code: str, lookback: int = 20, horizon: int = 5, epochs: int = 30) -> Dict:
    """训练 LSTM"""
    df = get_kline(code, days=730)
    if df.empty or len(df) < 100:
        return {"error": "数据不足"}

    prices = df["close"].values
    norm_prices, mean, std = normalize(prices)

    X, y = prepare_sequences(norm_prices, lookback, horizon)
    if len(X) < 50:
        return {"error": "序列数据不足"}

    model = SimpleLSTM(input_size=1, hidden_size=32, output_size=horizon, lr=0.01)
    losses = model.train(X, y, epochs=epochs)

    model_path = os.path.join(MODEL_DIR, f"{code}_lstm_lb{lookback}_h{horizon}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({
            "model": model, "mean": mean, "std": std,
            "lookback": lookback, "horizon": horizon,
        }, f)

    return {
        "code": code, "lookback": lookback, "horizon": horizon,
        "n_samples": len(X), "epochs": epochs,
        "final_loss": round(float(losses[-1]), 6),
        "model_path": model_path,
    }


def forecast(code: str, horizon: int = 5, lookback: int = 20) -> Dict:
    """预测"""
    model_path = os.path.join(MODEL_DIR, f"{code}_lstm_lb{lookback}_h{horizon}.pkl")
    if not os.path.exists(model_path):
        return {"error": f"模型未训练, 请先: python main.py train --code {code}"}
    with open(model_path, "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    mean, std = saved["mean"], saved["std"]

    df = get_kline(code, days=60)
    if df.empty:
        return {"error": "数据不足"}

    prices = df["close"].values
    norm_prices = (prices - mean) / std

    # 准备输入
    X = norm_prices[-lookback:].reshape(-1, 1)
    outputs, _, _ = model.forward(X)
    pred_norm = np.array(outputs[-horizon:]) if len(outputs) >= horizon else np.array(outputs + [outputs[-1]] * (horizon - len(outputs)))
    predictions = denormalize(pred_norm, mean, std)

    current = float(prices[-1])
    pred_final = float(predictions[-1])
    expected_change = (pred_final - current) / current * 100

    return {
        "code": code,
        "current_price": round(current, 2),
        "predictions": [round(float(p), 2) for p in predictions],
        "final_prediction": round(pred_final, 2),
        "expected_change": round(expected_change, 2),
        "horizon": horizon,
    }


def rolling_forecast(code: str, horizon: int = 5, lookback: int = 20, steps: int = 10) -> List[Dict]:
    """滚动预测"""
    results = []
    df = get_kline(code, days=200)
    if df.empty:
        return results

    for i in range(steps):
        if i * horizon >= len(df) - lookback - horizon:
            break
        sub = df.iloc[:len(df) - i * horizon]
        if len(sub) < 60:
            break
        # 使用最近数据预测
        if i == 0:
            r = forecast(code, horizon, lookback)
        else:
            r = forecast_from_data(sub, lookback, horizon)
        if r and "error" not in r:
            r["step"] = i + 1
            results.append(r)
    return results


def forecast_from_data(df: pd.DataFrame, lookback: int, horizon: int) -> Dict:
    """从数据预测 (用于滚动)"""
    model_path_glob = os.path.join(MODEL_DIR, "*_lstm_*.pkl")
    import glob
    files = glob.glob(model_path_glob)
    if not files:
        return {}
    with open(files[0], "rb") as f:
        saved = pickle.load(f)
    model = saved["model"]
    mean, std = saved["mean"], saved["std"]
    prices = df["close"].values
    norm_prices = (prices - mean) / std
    X = norm_prices[-lookback:].reshape(-1, 1)
    outputs, _, _ = model.forward(X)
    pred_norm = np.array(outputs[-horizon:])
    predictions = denormalize(pred_norm, mean, std)
    return {
        "current_price": round(float(prices[-1]), 2),
        "predictions": [round(float(p), 2) for p in predictions],
        "final_prediction": round(float(predictions[-1]), 2),
    }


def main():
    parser = argparse.ArgumentParser(description="lstm-forecaster")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("train", help="训练")
    p.add_argument("--code", required=True)
    p.add_argument("--lookback", type=int, default=20)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--epochs", type=int, default=30)
    p = sub.add_parser("predict", help="预测")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--lookback", type=int, default=20)
    p = sub.add_parser("rolling", help="滚动预测")
    p.add_argument("--code", required=True)
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--lookback", type=int, default=20)
    p.add_argument("--steps", type=int, default=10)
    args = parser.parse_args()

    if args.cmd == "train":
        r = train(args.code, args.lookback, args.horizon, args.epochs)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== 训练结果 ===")
            print(f"代码: {r['code']}, lookback={r['lookback']}, horizon={r['horizon']}")
            print(f"样本数: {r['n_samples']}, epochs: {r['epochs']}")
            print(f"最终损失: {r['final_loss']}")
            print(f"模型已保存: {r['model_path']}")
    elif args.cmd == "predict":
        r = forecast(args.code, args.horizon, args.lookback)
        if "error" in r:
            print(f"错误: {r['error']}")
        else:
            print(f"\n=== LSTM 预测 ===")
            print(f"代码: {r['code']}, horizon={r['horizon']}日")
            print(f"当前价: {r['current_price']}")
            print(f"预测序列: {r['predictions']}")
            print(f"最终预测: {r['final_prediction']} ({r['expected_change']:+.2f}%)")
    elif args.cmd == "rolling":
        r = rolling_forecast(args.code, args.horizon, args.lookback, args.steps)
        for item in r:
            print(f"Step {item['step']}: 当前 {item['current_price']} -> 预测 {item['final_prediction']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
