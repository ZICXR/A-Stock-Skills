#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""market-analysis: 大盘分析"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime, timedelta


def _add_ma(df, periods=(5, 10, 20, 60), col="close"):
    for p in periods:
        df[f"MA{p}"] = df[col].rolling(p).mean()
    return df


def _add_macd(df):
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2
    return df


def _get_kline(symbol: str, days: int) -> pd.DataFrame:
    try:
        import akshare as ak
        if str(symbol).startswith(("000", "6", "9")):
            sym = f"sh{symbol}"
        else:
            sym = f"sz{symbol}"
        df = ak.stock_zh_index_daily(symbol=sym)
        if df.empty:
            return df
        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"])
        return df.tail(days).reset_index(drop=True)
    except Exception as e:
        print(f"获取K线失败: {e}", file=sys.stderr)
        return pd.DataFrame()


def analyze_index_trend(symbol: str = "000001", days: int = 60) -> Dict:
    """指数趋势分析"""
    df = _get_kline(symbol, days)
    if df.empty:
        return {}

    df = _add_ma(df)
    df = _add_macd(df)
    last = df.iloc[-1]

    signals = []
    score = 0

    ma5, ma10, ma20, ma60 = last.get("MA5", 0), last.get("MA10", 0), last.get("MA20", 0), last.get("MA60", 0)
    close = last["close"]

    if ma5 > ma10 > ma20 > ma60:
        signals.append({"name": "多头排列", "score": 2, "desc": "均线呈完美多头排列"})
        score += 2
    elif ma5 < ma10 < ma20 < ma60:
        signals.append({"name": "空头排列", "score": -2, "desc": "均线呈空头排列"})
        score -= 2
    elif close > ma20 and ma20 > ma60:
        signals.append({"name": "偏多", "score": 1, "desc": "中短期偏多"})
        score += 1
    elif close < ma20 and ma20 < ma60:
        signals.append({"name": "偏空", "score": -1, "desc": "中短期偏空"})
        score -= 1
    else:
        signals.append({"name": "震荡", "score": 0, "desc": "均线缠绕"})

    dif, dea, macd = last.get("DIF", 0), last.get("DEA", 0), last.get("MACD", 0)
    if dif > dea and macd > 0:
        signals.append({"name": "MACD金叉", "score": 1, "desc": "MACD红柱"})
        score += 1
    elif dif < dea and macd < 0:
        signals.append({"name": "MACD死叉", "score": -1, "desc": "MACD绿柱"})
        score -= 1

    overall = "看多" if score > 0 else "看空" if score < 0 else "中性"

    pct_1d = 0.0
    pct_5d = 0.0
    pct_20d = 0.0
    if len(df) >= 2:
        pct_1d = round((close - df.iloc[-2]["close"]) / df.iloc[-2]["close"] * 100, 2)
    if len(df) >= 6:
        pct_5d = round((close - df.iloc[-6]["close"]) / df.iloc[-6]["close"] * 100, 2)
    if len(df) >= 21:
        pct_20d = round((close - df.iloc[-21]["close"]) / df.iloc[-21]["close"] * 100, 2)

    return {
        "symbol": symbol,
        "date": str(last.get("date", ""))[:10],
        "close": round(float(close), 2),
        "pct_change_1d": pct_1d, "pct_change_5d": pct_5d, "pct_change_20d": pct_20d,
        "MA5": round(float(ma5), 2) if ma5 else None,
        "MA20": round(float(ma20), 2) if ma20 else None,
        "MA60": round(float(ma60), 2) if ma60 else None,
        "DIF": round(float(dif), 4) if dif else None,
        "DEA": round(float(dea), 4) if dea else None,
        "signals": signals,
        "score": score,
        "overall": overall,
    }


def calc_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict:
    """支撑压力位"""
    if df.empty or len(df) < window:
        return {}
    recent = df.tail(window)
    pivot = (recent["high"].max() + recent["low"].min() + recent["close"].iloc[-1]) / 3
    r1 = 2 * pivot - recent["low"].min()
    s1 = 2 * pivot - recent["high"].max()
    r2 = pivot + (recent["high"].max() - recent["low"].min())
    s2 = pivot - (recent["high"].max() - recent["low"].min())
    return {
        "pivot": round(float(pivot), 2),
        "R1": round(float(r1), 2), "R2": round(float(r2), 2),
        "S1": round(float(s1), 2), "S2": round(float(s2), 2),
        "period_high": round(float(recent["high"].max()), 2),
        "period_low": round(float(recent["low"].min()), 2),
    }


def analyze_volume_price(df: pd.DataFrame) -> Dict:
    """量价分析"""
    if df.empty or len(df) < 5:
        return {}
    last = df.iloc[-1]
    avg5 = df["volume"].tail(5).mean()
    vol_ratio = last["volume"] / avg5 if avg5 else 1
    change = (last["close"] - df.iloc[-2]["close"]) / df.iloc[-2]["close"] * 100
    signal = "正常"
    if vol_ratio > 1.5 and change > 0:
        signal = "放量上涨"
    elif vol_ratio > 1.5 and change < 0:
        signal = "放量下跌"
    elif vol_ratio < 0.7 and change > 0:
        signal = "缩量上涨 (需警惕)"
    elif vol_ratio < 0.7 and change < 0:
        signal = "缩量下跌 (抛压衰竭)"
    return {
        "vol_ratio_5d": round(float(vol_ratio), 2),
        "pct_change": round(float(change), 2),
        "signal": signal,
    }


def full_market_analysis(symbol: str = "000001", days: int = 60) -> Dict:
    """综合分析"""
    trend = analyze_index_trend(symbol, days)
    df = _get_kline(symbol, days)
    sr = calc_support_resistance(df) if not df.empty else {}
    vp = analyze_volume_price(df) if not df.empty else {}

    score = trend.get("score", 0)
    if score >= 3:
        advice = "强势格局, 积极配置, 关注主线板块"
    elif score >= 1:
        advice = "偏多格局, 精选个股, 控制仓位"
    elif score <= -3:
        advice = "弱势格局, 防守为主, 降低仓位"
    elif score <= -1:
        advice = "偏空格局, 谨慎参与, 快进快出"
    else:
        advice = "震荡格局, 高抛低吸, 控制节奏"

    return {"trend": trend, "support_resistance": sr, "volume_price": vp, "advice": advice}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="market-analysis")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("trend", help="趋势分析")
    p.add_argument("symbol", nargs="?", default="000001")
    p.add_argument("--days", type=int, default=60)

    p = sub.add_parser("full", help="综合分析")
    p.add_argument("symbol", nargs="?", default="000001")
    p.add_argument("--days", type=int, default=60)

    p = sub.add_parser("volume", help="量价分析")
    p.add_argument("symbol", nargs="?", default="000001")
    p.add_argument("--days", type=int, default=30)

    args = parser.parse_args()
    if args.cmd in ("trend", "full", "volume"):
        if args.cmd == "trend":
            r = analyze_index_trend(args.symbol, args.days)
        elif args.cmd == "full":
            r = full_market_analysis(args.symbol, args.days)
        else:
            df = _get_kline(args.symbol, args.days)
            r = analyze_volume_price(df)
        import json
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
