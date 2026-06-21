#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multi-signal-backtest: 多信号组合回测"""

import os
import sys
import json
import itertools
import argparse
import warnings
import pandas as pd
import numpy as np
from typing import Dict, List, Set
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")


# ============================================================
# 信号定义 (复用 signal-screener 风格)
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


def calc_signals(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有信号"""
    if df.empty or len(df) < 30:
        return df
    df = df.copy()

    # MA
    df["MA5"] = df["close"].rolling(5).mean()
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA60"] = df["close"].rolling(60).mean()

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2

    # RSI
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI6"] = 100 - 100 / (1 + rs)

    # KDJ
    low_n = df["low"].rolling(9).min()
    high_n = df["high"].rolling(9).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    df["K"] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df["D"] = df["K"].ewm(alpha=1/3, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]

    # 成交量
    if "volume" in df.columns:
        df["vol_ma5"] = df["volume"].rolling(5).mean()

    # 信号
    df["sig_ma_cross"] = (df["MA5"] > df["MA20"]).astype(int) - (df["MA5"] < df["MA20"]).astype(int)
    df["sig_macd_golden"] = ((df["DIF"] > df["DEA"]) & (df["DIF"].shift(1) <= df["DEA"].shift(1))).astype(int)
    df["sig_macd_death"] = ((df["DIF"] < df["DEA"]) & (df["DIF"].shift(1) >= df["DEA"].shift(1))).astype(int)
    df["sig_above_ma20"] = (df["close"] > df["MA20"]).astype(int)
    df["sig_above_ma60"] = (df["close"] > df["MA60"]).astype(int)
    df["sig_volume_break"] = (df["volume"] > df["vol_ma5"] * 1.5).astype(int) if "volume" in df.columns else 0
    df["sig_volume_shrink"] = (df["volume"] < df["vol_ma5"] * 0.7).astype(int) if "volume" in df.columns else 0
    df["sig_rsi_oversold"] = (df["RSI6"] < 30).astype(int)
    df["sig_rsi_overbought"] = (df["RSI6"] > 70).astype(int)
    df["sig_kdj_golden"] = ((df["K"] > df["D"]) & (df["K"].shift(1) <= df["D"].shift(1)) & (df["K"] < 50)).astype(int)
    df["sig_new_high_60"] = (df["close"] >= df["high"].rolling(60).max()).astype(int)

    return df


def get_signal_value(df: pd.DataFrame, signal: str) -> pd.Series:
    """获取单个信号的布尔序列"""
    col = f"sig_{signal}"
    if col in df.columns:
        return df[col].astype(bool)
    return pd.Series([False] * len(df), index=df.index)


# ============================================================
# 单股回测
# ============================================================
def backtest_single(code: str, signals: List[str], hold_days: int = 5) -> Dict:
    """对单股回测信号组合"""
    df = get_kline(code, days=365)
    if df.empty or len(df) < 60:
        return {"code": code, "hits": 0, "returns": []}

    df = calc_signals(df)
    if not signals:
        return {"code": code, "hits": 0, "returns": []}

    # AND 组合
    combined = get_signal_value(df, signals[0])
    for sig in signals[1:]:
        combined = combined & get_signal_value(df, sig)

    # 计算每次命中后 N 日收益
    hit_indices = df.index[combined].tolist()
    returns = []
    for idx in hit_indices:
        pos = df.index.get_loc(idx) if idx in df.index else None
        if pos is None or pos + hold_days >= len(df):
            continue
        buy_price = df["close"].iloc[pos]
        sell_price = df["close"].iloc[pos + hold_days]
        ret = (sell_price - buy_price) / buy_price * 100
        returns.append(ret)

    return {
        "code": code,
        "hits": len(returns),
        "returns": returns,
    }


# ============================================================
# 批量回测
# ============================================================
def get_all_stocks() -> List[str]:
    """获取全 A 股列表"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df.empty:
            return []
        # 排除 ST 和停牌
        if "名称" in df.columns:
            df = df[~df["名称"].astype(str).str.contains("ST", na=False)]
        if "最新价" in df.columns:
            df = df[df["最新价"] > 0]
        if "总市值" in df.columns:
            df = df[df["总市值"] > 30e8]  # 市值 > 30 亿
        return df["代码"].astype(str).tolist() if "代码" in df.columns else []
    except Exception:
        return []


def backtest_combo(signals: List[str], hold_days: int = 5,
                  start: str = None, end: str = None,
                  scope: List[str] = None,
                  mode: str = "and",
                  max_stocks: int = 500) -> Dict:
    """组合回测"""
    if scope is None:
        scope = get_all_stocks()[:max_stocks]

    all_returns = []
    hit_count = 0
    stock_count = 0

    for code in scope:
        r = backtest_single(code, signals, hold_days)
        if r["hits"] > 0:
            all_returns.extend(r["returns"])
            hit_count += r["hits"]
            stock_count += 1

    if not all_returns:
        return {
            "signals": signals, "hold_days": hold_days,
            "hits": 0, "stock_count": 0, "win_rate": 0,
            "avg_return": 0, "total_return": 0,
        }

    arr = np.array(all_returns)
    wins = arr[arr > 0]
    losses = arr[arr <= 0]
    win_rate = len(wins) / len(arr) * 100
    avg_return = float(arr.mean())
    total_return = float((1 + arr / 100).prod() - 1) * 100

    return {
        "signals": signals,
        "hold_days": hold_days,
        "mode": mode,
        "hits": hit_count,
        "stock_count": stock_count,
        "win_rate": round(win_rate, 2),
        "avg_return": round(avg_return, 2),
        "median_return": round(float(np.median(arr)), 2),
        "max_return": round(float(arr.max()), 2),
        "min_return": round(float(arr.min()), 2),
        "total_return": round(total_return, 2),
    }


def optimize_combo(candidates: List[str], top_n: int = 5,
                  hold_days: int = 5, max_combo_size: int = 3) -> List[Dict]:
    """优化信号组合
    尝试所有 N 个信号的不同组合, 找出最佳
    """
    results = []
    for size in range(2, min(max_combo_size + 1, len(candidates) + 1)):
        for combo in itertools.combinations(candidates, size):
            r = backtest_combo(list(combo), hold_days=hold_days)
            if r["hits"] >= 5:  # 至少 5 次命中
                results.append(r)

    # 按平均收益排序
    results.sort(key=lambda x: x.get("avg_return", 0), reverse=True)
    return results[:top_n]


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="multi-signal-backtest")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("backtest", help="组合回测")
    p.add_argument("--signals", help="信号列表, 逗号分隔")
    p.add_argument("--strategy", help="策略文件 (YAML)")
    p.add_argument("--hold-days", type=int, default=5)
    p.add_argument("--scope", help="股票范围文件 (每行一个代码)")
    p.add_argument("--max", type=int, default=500)

    p = sub.add_parser("optimize", help="信号组合优化")
    p.add_argument("--candidates", required=True, help="候选信号")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--hold-days", type=int, default=5)
    args = parser.parse_args()

    if args.cmd == "backtest":
        if args.strategy:
            import yaml
            with open(args.strategy, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            signals = cfg.get("signals", [])
            hold_days = cfg.get("hold_days", 5)
        else:
            signals = [s.strip() for s in args.signals.split(",")]
            hold_days = args.hold_days

        scope = None
        if args.scope:
            with open(args.scope, "r") as f:
                scope = [line.strip() for line in f if line.strip()]

        print(f"\n正在回测 {len(signals)} 信号组合 (持仓 {hold_days} 日)...")
        r = backtest_combo(signals, hold_days=hold_days, scope=scope, max_stocks=args.max)
        if r["hits"] == 0:
            print("无命中, 尝试放宽条件")
        else:
            print(f"\n=== 组合回测结果 ===")
            print(f"信号: {' + '.join(signals)}")
            print(f"持仓周期: {r['hold_days']} 日")
            print(f"命中股票数: {r['stock_count']}")
            print(f"总命中次数: {r['hits']}")
            print(f"胜率: {r['win_rate']}%")
            print(f"平均收益: {r['avg_return']:+.2f}%")
            print(f"中位收益: {r['median_return']:+.2f}%")
            print(f"最大收益: {r['max_return']:+.2f}%")
            print(f"最小收益: {r['min_return']:+.2f}%")
            print(f"累计收益: {r['total_return']:+.2f}%")
    elif args.cmd == "optimize":
        candidates = [s.strip() for s in args.candidates.split(",")]
        print(f"\n正在优化 {len(candidates)} 个信号的组合 (Top {args.top})...")
        results = optimize_combo(candidates, top_n=args.top, hold_days=args.hold_days)
        print(f"\n=== Top {args.top} 组合 ===")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {' + '.join(r['signals'])}")
            print(f"   命中: {r['hits']} 次, 胜率: {r['win_rate']}%, "
                  f"平均收益: {r['avg_return']:+.2f}%")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
