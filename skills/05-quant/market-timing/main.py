#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""market-timing: 择时模型"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime, timedelta


def get_kline(code: str, days: int = 365) -> pd.DataFrame:
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


def get_index_kline(symbol: str = "000001", days: int = 365) -> pd.DataFrame:
    try:
        import akshare as ak
        if str(symbol).startswith(("000", "6", "9")):
            sym = f"sh{symbol}"
        else:
            sym = f"sz{symbol}"
        df = ak.stock_zh_index_daily(symbol=sym)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"])
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        return df[df["date"] >= cutoff].reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ============================================================
# 1. 趋势择时
# ============================================================
def trend_timing(df: pd.DataFrame) -> Dict:
    """趋势择时"""
    if df.empty or len(df) < 30:
        return {"signal": "数据不足"}
    df = df.copy()
    df["MA5"] = df["close"].rolling(5).mean()
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA60"] = df["close"].rolling(60).mean()
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()

    score = 0
    signals = []
    last = df.iloc[-1]
    prev = df.iloc[-1]

    # 均线
    if last["MA5"] > last["MA20"] > last["MA60"]:
        score += 2; signals.append("均线多头排列")
    elif last["MA5"] < last["MA20"] < last["MA60"]:
        score -= 2; signals.append("均线空头排列")

    if last["close"] > last["MA20"]:
        score += 1; signals.append("站上MA20")
    elif last["close"] < last["MA20"]:
        score -= 1; signals.append("跌破MA20")

    # MACD
    if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
        score += 2; signals.append("MACD金叉")
    elif dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2]:
        score -= 2; signals.append("MACD死叉")

    if score >= 3:
        signal = "买入"
    elif score >= 1:
        signal = "谨慎买入"
    elif score <= -3:
        signal = "卖出"
    elif score <= -1:
        signal = "谨慎卖出"
    else:
        signal = "观望"

    return {"signal": signal, "score": score, "details": signals}


# ============================================================
# 2. 反转择时
# ============================================================
def reversal_timing(df: pd.DataFrame) -> Dict:
    """反转择时"""
    if df.empty or len(df) < 30:
        return {"signal": "数据不足"}
    score = 0
    signals = []

    # RSI
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).iloc[-1]

    if rsi < 30:
        score += 2; signals.append(f"RSI={rsi:.0f}超卖")
    elif rsi < 40:
        score += 1; signals.append("RSI偏低")
    elif rsi > 70:
        score -= 2; signals.append(f"RSI={rsi:.0f}超买")
    elif rsi > 60:
        score -= 1; signals.append("RSI偏高")

    # 布林带
    mid = df["close"].rolling(20).mean()
    std = df["close"].rolling(20).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    last = df["close"].iloc[-1]
    if last < lower.iloc[-1]:
        score += 2; signals.append("跌破布林下轨")
    elif last > upper.iloc[-1]:
        score -= 2; signals.append("突破布林上轨")

    # KDJ
    low_n = df["low"].rolling(9).min()
    high_n = df["high"].rolling(9).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    d = k.ewm(alpha=1/3, adjust=False).mean()
    if k.iloc[-1] < 20:
        score += 1; signals.append("KDJ超卖")
    elif k.iloc[-1] > 80:
        score -= 1; signals.append("KDJ超买")

    if score >= 2:
        signal = "买入"
    elif score >= 1:
        signal = "谨慎买入"
    elif score <= -2:
        signal = "卖出"
    elif score <= -1:
        signal = "谨慎卖出"
    else:
        signal = "观望"

    return {"signal": signal, "score": score, "details": signals}


# ============================================================
# 3. 波动率择时
# ============================================================
def volatility_timing(df: pd.DataFrame) -> Dict:
    """波动率择时"""
    if df.empty or len(df) < 20:
        return {"signal": "数据不足"}
    returns = df["close"].pct_change().dropna()
    vol = returns.std() * np.sqrt(252) * 100  # 年化波动率
    recent_vol = returns.tail(10).std() * np.sqrt(252) * 100

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        abs(df["high"] - df["close"].shift()),
        abs(df["low"] - df["close"].shift()),
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    atr_pct = atr / df["close"].iloc[-1] * 100

    # 判断
    if vol < 15:
        level = "低波动, 适合买入"
        signal = "买入"
        score = 1
    elif vol < 25:
        level = "中等波动"
        signal = "观望"
        score = 0
    elif vol < 40:
        level = "高波动, 注意风险"
        signal = "谨慎"
        score = -1
    else:
        level = "极高波动, 远离"
        signal = "卖出"
        score = -2

    return {
        "signal": signal, "score": score, "level": level,
        "annual_vol": round(vol, 2), "recent_vol": round(recent_vol, 2),
        "atr_pct": round(atr_pct, 2),
    }


# ============================================================
# 4. 估值择时
# ============================================================
def valuation_timing(code: str) -> Dict:
    """估值择时"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return {"signal": "数据不足"}
        row = target.iloc[0]
        pe = float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else 0
        pb = float(row.get("市净率", 0)) if row.get("市净率") else 0

        # 简化的历史分位
        if pe < 0:
            level = "亏损"
            signal = "观望"
            score = 0
        elif pe < 15:
            level = "严重低估"
            signal = "买入"
            score = 2
        elif pe < 25:
            level = "低估"
            signal = "买入"
            score = 1
        elif pe < 40:
            level = "合理"
            signal = "观望"
            score = 0
        elif pe < 60:
            level = "高估"
            signal = "卖出"
            score = -1
        else:
            level = "严重高估"
            signal = "卖出"
            score = -2

        return {
            "signal": signal, "score": score, "level": level,
            "pe": pe, "pb": pb,
        }
    except Exception:
        return {"signal": "数据不足"}


# ============================================================
# 综合择时
# ============================================================
def comprehensive_timing(code: str) -> Dict:
    """综合择时"""
    df = get_kline(code, days=120)
    if df.empty:
        return {}

    trend = trend_timing(df)
    reversal = reversal_timing(df)
    vol = volatility_timing(df)
    val = valuation_timing(code)

    # 加权评分
    weights = {"trend": 0.3, "reversal": 0.25, "vol": 0.2, "val": 0.25}
    total_score = (
        trend.get("score", 0) * weights["trend"]
        + reversal.get("score", 0) * weights["reversal"]
        + vol.get("score", 0) * weights["vol"]
        + val.get("score", 0) * weights["val"]
    )

    if total_score >= 1.5:
        final = "强烈买入"
    elif total_score >= 0.7:
        final = "买入"
    elif total_score >= -0.7:
        final = "观望"
    elif total_score >= -1.5:
        final = "卖出"
    else:
        final = "强烈卖出"

    # 信心度
    if abs(total_score) >= 1.5:
        confidence = "高"
    elif abs(total_score) >= 0.7:
        confidence = "中"
    else:
        confidence = "低"

    return {
        "code": code,
        "trend": trend,
        "reversal": reversal,
        "volatility": vol,
        "valuation": val,
        "total_score": round(total_score, 2),
        "comprehensive": final,
        "confidence": confidence,
    }


def market_timing() -> Dict:
    """大盘择时 (上证指数)"""
    df = get_index_kline("000001", days=120)
    if df.empty:
        return {}
    df.columns = [c.lower() for c in df.columns]
    trend = trend_timing(df)
    reversal = reversal_timing(df)
    vol = volatility_timing(df)
    score = trend.get("score", 0) * 0.5 + reversal.get("score", 0) * 0.3 + vol.get("score", 0) * 0.2
    if score >= 2:
        signal = "大盘看多"
    elif score >= 0.5:
        signal = "大盘偏多"
    elif score >= -0.5:
        signal = "大盘震荡"
    elif score >= -2:
        signal = "大盘偏空"
    else:
        signal = "大盘看空"
    return {"signal": signal, "score": round(score, 2), "trend": trend, "volatility": vol}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="market-timing")
    sub = parser.add_subparsers(dest="cmd")
    for cmd in ["trend", "reversal", "volatility", "valuation", "all"]:
        p = sub.add_parser(cmd, help=cmd)
        if cmd != "market":
            p.add_argument("code")
    sub.add_parser("market", help="大盘择时")
    args = parser.parse_args()

    if args.cmd == "trend":
        df = get_kline(args.code, 120)
        r = trend_timing(df)
        print(f"信号: {r['signal']} (分数: {r.get('score')})")
        for d in r.get("details", []):
            print(f"  - {d}")
    elif args.cmd == "reversal":
        df = get_kline(args.code, 120)
        r = reversal_timing(df)
        print(f"信号: {r['signal']} (分数: {r.get('score')})")
        for d in r.get("details", []):
            print(f"  - {d}")
    elif args.cmd == "volatility":
        df = get_kline(args.code, 120)
        r = volatility_timing(df)
        print(f"信号: {r['signal']} - {r.get('level')}")
        print(f"  年化波动率: {r.get('annual_vol')}%")
        print(f"  ATR%: {r.get('atr_pct')}%")
    elif args.cmd == "valuation":
        r = valuation_timing(args.code)
        print(f"信号: {r['signal']} - {r.get('level')}")
        print(f"  PE: {r.get('pe')}, PB: {r.get('pb')}")
    elif args.cmd == "all":
        r = comprehensive_timing(args.code)
        print(f"\n=== {args.code} 综合择时 ===\n")
        for k in ["trend", "reversal", "volatility", "valuation"]:
            v = r.get(k, {})
            print(f"  [{k}] {v.get('signal', 'N/A')}: {v.get('level', '')} {v.get('details', '')}")
        print(f"\n综合: {r['comprehensive']} (信心度: {r['confidence']}, 分数: {r['total_score']})")
    elif args.cmd == "market":
        r = market_timing()
        print(f"\n=== 大盘择时 ===")
        print(f"信号: {r['signal']} (分数: {r['score']})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
