#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-technical-analysis: 个股技术面分析"""

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


def _add_kdj(df, n=9):
    low_n = df["low"].rolling(n).min()
    high_n = df["high"].rolling(n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    df["K"] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df["D"] = df["K"].ewm(alpha=1/3, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]
    return df


def _add_rsi(df, periods=(6, 12, 24)):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    for p in periods:
        avg_g = gain.rolling(p).mean()
        avg_l = loss.rolling(p).mean()
        rs = avg_g / avg_l.replace(0, np.nan)
        df[f"RSI{p}"] = 100 - (100 / (1 + rs))
    return df


def _add_boll(df, n=20, k=2):
    df["MID"] = df["close"].rolling(n).mean()
    std = df["close"].rolling(n).std()
    df["UPPER"] = df["MID"] + k * std
    df["LOWER"] = df["MID"] - k * std
    return df


def get_kline(code: str, days: int = 120, adjust: str = "qfq") -> pd.DataFrame:
    """获取K线"""
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(
            symbol=str(code).zfill(6), period="daily",
            start_date=start, end_date=end, adjust=adjust
        )
    except Exception as e:
        print(f"获取K线失败: {e}", file=sys.stderr)
        return pd.DataFrame()
    if df.empty:
        return df
    rm = {"日期": "date", "开盘": "open", "最高": "high",
          "最低": "low", "收盘": "close", "成交量": "volume"}
    df = df.rename(columns={k: v for k, v in rm.items() if k in df.columns})
    df.columns = [c.lower() for c in df.columns]
    return df.tail(days).reset_index(drop=True)


def detect_patterns(df: pd.DataFrame) -> list:
    """K线形态识别"""
    patterns = []
    if df.empty or len(df) < 3:
        return patterns
    for i in range(-3, 0):
        if abs(i) > len(df):
            continue
        curr = df.iloc[i]
        prev = df.iloc[i - 1] if abs(i) < len(df) else None
        if prev is None:
            continue
        body = abs(curr["close"] - curr["open"])
        upper = curr["high"] - max(curr["close"], curr["open"])
        lower = min(curr["close"], curr["open"]) - curr["low"]
        total = curr["high"] - curr["low"]
        if total == 0:
            continue
        date_str = str(curr.get("date", ""))[:10]

        if body / total < 0.1:
            patterns.append({"date": date_str, "pattern": "十字星", "signal": "反转", "desc": "多空胶着"})
        elif lower > body * 2 and upper < body * 0.5:
            sig = "看涨" if curr["close"] > curr["open"] else "看跌"
            patterns.append({"date": date_str, "pattern": "锤子线", "signal": sig, "desc": "下影线长"})
        else:
            prev_body = abs(prev["close"] - prev["open"])
            if (prev["close"] < prev["open"] and curr["close"] > curr["open"] and
                curr["close"] > prev["open"] and curr["open"] < prev["close"] and body > prev_body):
                patterns.append({"date": date_str, "pattern": "看涨吞没", "signal": "看涨", "desc": "阳包阴"})
            elif (prev["close"] > prev["open"] and curr["close"] < curr["open"] and
                  curr["close"] < prev["open"] and curr["open"] > prev["close"] and body > prev_body):
                patterns.append({"date": date_str, "pattern": "看跌吞没", "signal": "看跌", "desc": "阴包阳"})
    return patterns


def analyze_trend(df: pd.DataFrame) -> Dict:
    """趋势研判"""
    if df.empty or len(df) < 20:
        return {}
    df = _add_ma(df)
    df = _add_macd(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    signals = []
    score = 0
    ma5, ma10, ma20, ma60 = last.get("MA5", 0), last.get("MA10", 0), last.get("MA20", 0), last.get("MA60", 0)
    close = last["close"]
    if ma5 > ma10 > ma20:
        signals.append({"name": "均线多头", "score": 2, "desc": "短期多头排列"})
        score += 2
    elif ma5 < ma10 < ma20:
        signals.append({"name": "均线空头", "score": -2, "desc": "短期空头排列"})
        score -= 2
    if close > ma20:
        signals.append({"name": "站上MA20", "score": 1, "desc": ""})
        score += 1
    elif close < ma20:
        signals.append({"name": "跌破MA20", "score": -1, "desc": ""})
        score -= 1
    dif, dea, macd = last.get("DIF", 0), last.get("DEA", 0), last.get("MACD", 0)
    if dif > dea and prev.get("DIF", 0) <= prev.get("DEA", 0):
        signals.append({"name": "MACD金叉", "score": 2, "desc": ""})
        score += 2
    elif dif < dea and prev.get("DIF", 0) >= prev.get("DEA", 0):
        signals.append({"name": "MACD死叉", "score": -2, "desc": ""})
        score -= 2

    if score >= 5: trend = "强势上涨"
    elif score >= 2: trend = "上涨"
    elif score <= -5: trend = "强势下跌"
    elif score <= -2: trend = "下跌"
    else: trend = "震荡"
    return {"trend": trend, "score": score, "signals": signals}


def detect_obs(df: pd.DataFrame) -> Dict:
    """超买超卖"""
    if df.empty or len(df) < 20:
        return {}
    df = _add_kdj(df)
    df = _add_rsi(df)
    last = df.iloc[-1]
    k, d, j = last.get("K", 50), last.get("D", 50), last.get("J", 50)
    rsi6 = last.get("RSI6", 50)
    signals = []
    if j > 100: signals.append({"name": "KDJ超买", "score": -1})
    elif j < 0: signals.append({"name": "KDJ超卖", "score": 1})
    if k > d and df.iloc[-2].get("K", 50) <= df.iloc[-2].get("D", 50):
        signals.append({"name": "KDJ金叉", "score": 1})
    elif k < d and df.iloc[-2].get("K", 50) >= df.iloc[-2].get("D", 50):
        signals.append({"name": "KDJ死叉", "score": -1})
    if rsi6 > 80: signals.append({"name": "RSI超买", "score": -1})
    elif rsi6 < 20: signals.append({"name": "RSI超卖", "score": 1})
    score = sum(s["score"] for s in signals)
    level = "超买" if score < -1 else "超卖" if score > 1 else "中性"
    return {"level": level, "K": round(float(k), 2), "D": round(float(d), 2), "J": round(float(j), 2),
            "RSI6": round(float(rsi6), 2), "signals": signals}


def calc_support_pressure(df: pd.DataFrame, window: int = 60) -> Dict:
    """支撑压力"""
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
    }


def generate_trading_signal(df: pd.DataFrame) -> Dict:
    """买卖信号"""
    if df.empty or len(df) < 30:
        return {}
    df = _add_ma(df)
    df = _add_macd(df)
    df = _add_kdj(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    buy, sell = [], []
    if last.get("MA5", 0) > last.get("MA10", 0) > last.get("MA20", 0):
        buy.append("均线多头排列")
    elif last.get("MA5", 0) < last.get("MA10", 0) < last.get("MA20", 0):
        sell.append("均线空头排列")
    if last.get("DIF", 0) > last.get("DEA", 0) and prev.get("DIF", 0) <= prev.get("DEA", 0):
        buy.append("MACD金叉")
    elif last.get("DIF", 0) < last.get("DEA", 0) and prev.get("DIF", 0) >= prev.get("DEA", 0):
        sell.append("MACD死叉")
    if last.get("K", 0) > last.get("D", 0) and prev.get("K", 0) <= prev.get("D", 0) and last.get("K", 0) < 50:
        buy.append("KDJ低位金叉")
    elif last.get("K", 0) < last.get("D", 0) and prev.get("K", 0) >= prev.get("D", 0) and last.get("K", 0) > 50:
        sell.append("KDJ高位死叉")
    vol_ratio = last["volume"] / df["volume"].tail(5).mean() if df["volume"].tail(5).mean() else 1
    if vol_ratio > 1.5 and last["close"] > prev["close"]:
        buy.append("放量上涨")
    elif vol_ratio > 1.5 and last["close"] < prev["close"]:
        sell.append("放量下跌")

    bc, sc = len(buy), len(sell)
    if bc >= 2 and bc > sc:
        signal, strength = "买入", "强" if bc >= 3 else "中"
    elif sc >= 2 and sc > bc:
        signal, strength = "卖出", "强" if sc >= 3 else "中"
    else:
        signal, strength = "观望", "中性"
    return {"signal": signal, "strength": strength, "buy_signals": buy, "sell_signals": sell, "score": bc - sc}


def full_technical_analysis(code: str, days: int = 120) -> Dict:
    """综合分析"""
    df = get_kline(code, days=days)
    if df.empty:
        return {}
    return {
        "symbol": code,
        "close": float(df.iloc[-1]["close"]),
        "patterns": detect_patterns(df),
        "trend": analyze_trend(df),
        "overbought_oversold": detect_obs(df),
        "support_pressure": calc_support_pressure(df),
        "trading_signal": generate_trading_signal(df),
    }


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="stock-technical-analysis")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("kline", help="K线")
    p.add_argument("code")
    p.add_argument("--days", type=int, default=120)
    p.add_argument("--adjust", default="qfq")

    for cmd in ["trend", "signal", "patterns", "obs", "sp", "full"]:
        p = sub.add_parser(cmd, help=cmd)
        p.add_argument("code")
        p.add_argument("--days", type=int, default=60 if cmd in ("trend", "signal") else 120)

    args = parser.parse_args()

    if args.cmd == "kline":
        df = get_kline(args.code, args.days, args.adjust)
        print(df.tail(args.days).to_string())

    elif args.cmd == "full":
        r = full_technical_analysis(args.code, args.days)
        import json
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))

    elif args.cmd == "trend":
        df = get_kline(args.code, args.days)
        r = analyze_trend(df)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))

    elif args.cmd == "signal":
        df = get_kline(args.code, args.days)
        r = generate_trading_signal(df)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))

    elif args.cmd == "patterns":
        df = get_kline(args.code, args.days)
        for p in detect_patterns(df):
            print(f"  {p['date']}: {p['pattern']} - {p['desc']} ({p['signal']})")

    elif args.cmd == "obs":
        df = get_kline(args.code, args.days)
        r = detect_obs(df)
        print(f"等级: {r.get('level')}")
        print(f"K={r.get('K')}, D={r.get('D')}, J={r.get('J')}, RSI6={r.get('RSI6')}")

    elif args.cmd == "sp":
        df = get_kline(args.code, args.days)
        r = calc_support_pressure(df)
        for k, v in r.items():
            print(f"  {k}: {v}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
