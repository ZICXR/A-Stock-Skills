"""
stock-technical-analysis: 个股技术面分析
=========================================

功能:
    - K线形态识别
    - 趋势研判 (均线/MACD/趋势线)
    - 超买超卖 (KDJ/RSI)
    - 支撑压力位
    - 买卖信号
    - 综合技术评分
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import sys
sys.path.insert(0, "skills/01-infra")
from astock_utils.astock_utils import (
    add_all_indicators, calc_ma, calc_macd,
    calc_kdj, calc_rsi, calc_boll,
    normalize_stock_code
)

logger = logging.getLogger(__name__)


# ============================================================
# 1. 获取K线数据
# ============================================================
def get_kline(symbol: str, period: str = "daily",
              days: int = 120, adjust: str = "qfq") -> pd.DataFrame:
    """获取K线数据
    Args:
        symbol: 6位股票代码
        period: daily/weekly/monthly
        days: 获取天数
        adjust: qfq/hfq/不复权
    """
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(
            symbol=symbol, period=period,
            start_date=start, end_date=end, adjust=adjust
        )
    except Exception as e:
        logger.error(f"akshare 获取K线失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    # 标准化
    rename_map = {"日期": "date", "开盘": "open", "最高": "high",
                  "最低": "low", "收盘": "close", "成交量": "volume"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    df.columns = [c.lower() for c in df.columns]
    df = df.tail(days).reset_index(drop=True)
    return df


# ============================================================
# 2. K线形态识别
# ============================================================
def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict]:
    """识别K线形态
    常见: 十字星, 锤子线, 吞没, 早晨之星, 黄昏之星等
    """
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

        # 十字星
        if body / total < 0.1:
            patterns.append({
                "date": str(curr.get("date", "")),
                "pattern": "十字星",
                "signal": "反转",
                "desc": "多空胶着, 关注变盘"
            })

        # 锤子线
        elif lower > body * 2 and upper < body * 0.5:
            patterns.append({
                "date": str(curr.get("date", "")),
                "pattern": "锤子线",
                "signal": "看涨" if curr["close"] > curr["open"] else "看跌",
                "desc": "下影线长, 多方力量"
            })

        # 吞没形态
        prev_body = abs(prev["close"] - prev["open"])
        if prev["close"] < prev["open"] and curr["close"] > curr["open"] and \
           curr["close"] > prev["open"] and curr["open"] < prev["close"] and \
           body > prev_body:
            patterns.append({
                "date": str(curr.get("date", "")),
                "pattern": "看涨吞没",
                "signal": "看涨",
                "desc": "阳包阴, 强势反转"
            })
        elif prev["close"] > prev["open"] and curr["close"] < curr["open"] and \
             curr["close"] < prev["open"] and curr["open"] > prev["close"] and \
             body > prev_body:
            patterns.append({
                "date": str(curr.get("date", "")),
                "pattern": "看跌吞没",
                "signal": "看跌",
                "desc": "阴包阳, 弱势反转"
            })

    return patterns


# ============================================================
# 3. 趋势研判
# ============================================================
def analyze_trend(df: pd.DataFrame) -> Dict:
    """趋势研判
    综合: 均线排列 + MACD + 趋势线
    """
    if df.empty or len(df) < 20:
        return {}

    df = add_all_indicators(df)
    last = df.iloc[-1]

    signals = []
    score = 0

    # 均线
    ma5 = last.get("MA5", 0)
    ma10 = last.get("MA10", 0)
    ma20 = last.get("MA20", 0)
    ma60 = last.get("MA60", 0)
    close = last["close"]

    if ma5 > ma10 > ma20:
        signals.append(("均线多头", 2, "短期均线多头排列"))
        score += 2
    elif ma5 < ma10 < ma20:
        signals.append(("均线空头", -2, "短期均线空头排列"))
        score -= 2

    if close > ma20:
        signals.append(("站上MA20", 1, "股价站上20日均线"))
        score += 1
    elif close < ma20:
        signals.append(("跌破MA20", -1, "股价跌破20日均线"))
        score -= 1

    # MACD
    dif = last.get("DIF", 0)
    dea = last.get("DEA", 0)
    macd_val = last.get("MACD", 0)
    prev = df.iloc[-2]
    if dif > dea and prev.get("DIF", 0) <= prev.get("DEA", 0):
        signals.append(("MACD金叉", 2, "DIF上穿DEA"))
        score += 2
    elif dif < dea and prev.get("DIF", 0) >= prev.get("DEA", 0):
        signals.append(("MACD死叉", -2, "DIF下穿DEA"))
        score -= 2

    if macd_val > 0:
        signals.append(("MACD红柱", 1, "动能向上"))
        score += 1
    elif macd_val < 0:
        signals.append(("MACD绿柱", -1, "动能向下"))
        score -= 1

    # 趋势强度
    if score >= 5:
        trend = "强势上涨"
    elif score >= 2:
        trend = "上涨"
    elif score <= -5:
        trend = "强势下跌"
    elif score <= -2:
        trend = "下跌"
    else:
        trend = "震荡"

    return {
        "trend": trend,
        "score": score,
        "signals": [{"name": s[0], "score": s[1], "desc": s[2]} for s in signals],
    }


# ============================================================
# 4. 超买超卖
# ============================================================
def detect_overbought_oversold(df: pd.DataFrame) -> Dict:
    """超买超卖检测 (KDJ + RSI)"""
    if df.empty or len(df) < 20:
        return {}

    df = calc_kdj(df)
    df = calc_rsi(df)
    last = df.iloc[-1]

    k = last.get("K", 50)
    d = last.get("D", 50)
    j = last.get("J", 50)
    rsi6 = last.get("RSI6", 50)
    rsi12 = last.get("RSI12", 50)

    signals = []

    # KDJ
    if j > 100:
        signals.append(("KDJ超买", -1, f"J值={j:.0f}"))
    elif j < 0:
        signals.append(("KDJ超卖", 1, f"J值={j:.0f}"))

    if k > d and df.iloc[-2].get("K", 50) <= df.iloc[-2].get("D", 50):
        signals.append(("KDJ金叉", 1, "金叉形成"))
    elif k < d and df.iloc[-2].get("K", 50) >= df.iloc[-2].get("D", 50):
        signals.append(("KDJ死叉", -1, "死叉形成"))

    # RSI
    if rsi6 > 80:
        signals.append(("RSI超买", -1, f"RSI6={rsi6:.0f}"))
    elif rsi6 < 20:
        signals.append(("RSI超卖", 1, f"RSI6={rsi6:.0f}"))

    score = sum(s[1] for s in signals)
    level = "超买" if score < -1 else "超卖" if score > 1 else "中性"

    return {
        "level": level,
        "K": round(float(k), 2),
        "D": round(float(d), 2),
        "J": round(float(j), 2),
        "RSI6": round(float(rsi6), 2),
        "RSI12": round(float(rsi12), 2),
        "signals": [{"name": s[0], "score": s[1], "desc": s[2]} for s in signals],
    }


# ============================================================
# 5. 支撑压力位
# ============================================================
def calc_support_pressure(df: pd.DataFrame, window: int = 60) -> Dict:
    """计算支撑压力位"""
    if df.empty or len(df) < window:
        return {}

    recent = df.tail(window)
    pivot = (recent["high"].max() + recent["low"].min() + recent["close"].iloc[-1]) / 3
    r1 = 2 * pivot - recent["low"].min()
    s1 = 2 * pivot - recent["high"].max()
    r2 = pivot + (recent["high"].max() - recent["low"].min())
    s2 = pivot - (recent["high"].max() - recent["low"].min())

    # 近期高低点
    high_20 = recent.tail(20)["high"].max()
    low_20 = recent.tail(20)["low"].min()
    high_60 = recent["high"].max()
    low_60 = recent["low"].min()

    return {
        "pivot": round(float(pivot), 2),
        "R1": round(float(r1), 2),
        "R2": round(float(r2), 2),
        "S1": round(float(s1), 2),
        "S2": round(float(s2), 2),
        "high_20d": round(float(high_20), 2),
        "low_20d": round(float(low_20), 2),
        "high_60d": round(float(high_60), 2),
        "low_60d": round(float(low_60), 2),
    }


# ============================================================
# 6. 买卖信号
# ============================================================
def generate_trading_signal(df: pd.DataFrame) -> Dict:
    """生成买卖信号
    综合: 均线 + MACD + KDJ + 量价
    """
    if df.empty or len(df) < 30:
        return {}

    df = add_all_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    buy_signals = []
    sell_signals = []

    # 均线信号
    if last.get("MA5", 0) > last.get("MA10", 0) > last.get("MA20", 0):
        buy_signals.append("均线多头排列")
    elif last.get("MA5", 0) < last.get("MA10", 0) < last.get("MA20", 0):
        sell_signals.append("均线空头排列")

    # MACD
    if last.get("DIF", 0) > last.get("DEA", 0) and prev.get("DIF", 0) <= prev.get("DEA", 0):
        buy_signals.append("MACD金叉")
    elif last.get("DIF", 0) < last.get("DEA", 0) and prev.get("DIF", 0) >= prev.get("DEA", 0):
        sell_signals.append("MACD死叉")

    # KDJ
    if last.get("K", 0) > last.get("D", 0) and prev.get("K", 0) <= prev.get("D", 0) and last.get("K", 0) < 50:
        buy_signals.append("KDJ低位金叉")
    elif last.get("K", 0) < last.get("D", 0) and prev.get("K", 0) >= prev.get("D", 0) and last.get("K", 0) > 50:
        sell_signals.append("KDJ高位死叉")

    # 量价
    vol_ratio = last["volume"] / df["volume"].tail(5).mean() if df["volume"].tail(5).mean() else 1
    if vol_ratio > 1.5 and last["close"] > prev["close"]:
        buy_signals.append("放量上涨")
    elif vol_ratio > 1.5 and last["close"] < prev["close"]:
        sell_signals.append("放量下跌")

    # 综合判断
    buy_count = len(buy_signals)
    sell_count = len(sell_signals)

    if buy_count >= 2 and buy_count > sell_count:
        signal = "买入"
        strength = "强" if buy_count >= 3 else "中"
    elif sell_count >= 2 and sell_count > buy_count:
        signal = "卖出"
        strength = "强" if sell_count >= 3 else "中"
    else:
        signal = "观望"
        strength = "中性"

    return {
        "signal": signal,
        "strength": strength,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "score": buy_count - sell_count,
    }


# ============================================================
# 7. 综合技术分析
# ============================================================
def full_technical_analysis(symbol: str, days: int = 120) -> Dict:
    """完整技术分析
    Args:
        symbol: 6位股票代码
        days: 分析天数
    """
    df = get_kline(symbol, days=days)
    if df.empty:
        return {}

    patterns = detect_candlestick_patterns(df)
    trend = analyze_trend(df)
    obs = detect_overbought_oversold(df)
    sp = calc_support_pressure(df)
    signal = generate_trading_signal(df)

    return {
        "symbol": symbol,
        "date": str(df.iloc[-1].get("date", "")),
        "close": float(df.iloc[-1]["close"]),
        "patterns": patterns,
        "trend": trend,
        "overbought_oversold": obs,
        "support_pressure": sp,
        "trading_signal": signal,
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    symbol = "000001"
    print(f"=== {symbol} 技术面综合分析 ===")
    result = full_technical_analysis(symbol)
    if result:
        print(f"\n收盘价: {result['close']}")
        print(f"\n【趋势】 {result['trend'].get('trend')} (评分: {result['trend'].get('score')})")
        for s in result['trend'].get('signals', []):
            print(f"  - {s['name']}: {s['desc']}")

        print(f"\n【超买超卖】 {result['overbought_oversold'].get('level')}")
        print(f"  K={result['overbought_oversold'].get('K')}, D={result['overbought_oversold'].get('D')}, J={result['overbought_oversold'].get('J')}")
        print(f"  RSI6={result['overbought_oversold'].get('RSI6')}")

        print(f"\n【支撑压力】")
        sp = result['support_pressure']
        print(f"  R2: {sp['R2']} | R1: {sp['R1']} | PIVOT: {sp['pivot']}")
        print(f"  S1: {sp['S1']} | S2: {sp['S2']}")

        print(f"\n【交易信号】 {result['trading_signal']['signal']} ({result['trading_signal']['strength']})")
        if result['trading_signal']['buy_signals']:
            print(f"  买入: {', '.join(result['trading_signal']['buy_signals'])}")
        if result['trading_signal']['sell_signals']:
            print(f"  卖出: {', '.join(result['trading_signal']['sell_signals'])}")

        if result['patterns']:
            print(f"\n【K线形态】")
            for p in result['patterns']:
                print(f"  {p['date']}: {p['pattern']} - {p['desc']}")
