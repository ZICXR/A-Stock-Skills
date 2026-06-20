"""
market-analysis: 大盘分析
============================

功能:
    - 大盘趋势研判
    - 技术面分析 (均线/形态/突破)
    - 多空力量对比
    - 风险信号识别
    - 综合大盘研判报告
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import sys
sys.path.insert(0, "skills/01-infra")
from astock_utils.astock_utils import (
    add_all_indicators, get_market, calc_ma, calc_macd,
    normalize_stock_code
)

logger = logging.getLogger(__name__)


# ============================================================
# 1. 大盘趋势研判
# ============================================================
def analyze_index_trend(symbol: str = "000001", days: int = 60) -> Dict:
    """分析大盘指数趋势
    Args:
        symbol: 指数代码 (默认上证指数)
        days: 分析周期
    """
    try:
        import akshare as ak
        if symbol.startswith("000") or symbol.startswith("6"):
            df = ak.stock_zh_index_daily(symbol=f"sh{symbol}")
        else:
            df = ak.stock_zh_index_daily(symbol=f"sz{symbol}")
    except Exception as e:
        logger.error(f"获取指数K线失败: {e}")
        return {}

    if df.empty:
        return {}

    # 标准化
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df = df.tail(days).reset_index(drop=True)
    df = add_all_indicators(df)

    # 趋势研判
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    trend_signals = []

    # 均线系统
    ma5 = last.get("MA5", 0)
    ma10 = last.get("MA10", 0)
    ma20 = last.get("MA20", 0)
    ma60 = last.get("MA60", 0)
    close = last["close"]

    if ma5 > ma10 > ma20 > ma60:
        trend_signals.append(("多头排列", 2, "均线呈完美多头排列, 趋势向上"))
    elif ma5 < ma10 < ma20 < ma60:
        trend_signals.append(("空头排列", -2, "均线呈空头排列, 趋势向下"))
    elif close > ma20 and ma20 > ma60:
        trend_signals.append(("多头", 1, "中短期偏多"))
    elif close < ma20 and ma20 < ma60:
        trend_signals.append(("空头", -1, "中短期偏空"))
    else:
        trend_signals.append(("震荡", 0, "均线缠绕, 趋势不明"))

    # MACD
    dif = last.get("DIF", 0)
    dea = last.get("DEA", 0)
    macd = last.get("MACD", 0)
    if dif > dea and macd > 0:
        trend_signals.append(("MACD金叉", 1, "MACD红柱, 动能向上"))
    elif dif < dea and macd < 0:
        trend_signals.append(("MACD死叉", -1, "MACD绿柱, 动能向下"))

    # 趋势强度评分
    score = sum(s[1] for s in trend_signals)
    max_score = sum(abs(s[1]) for s in trend_signals)

    if score > 0:
        overall = "看多"
    elif score < 0:
        overall = "看空"
    else:
        overall = "中性"

    # 计算涨跌幅
    pct_1d = (close - prev["close"]) / prev["close"] * 100
    pct_5d = (close - df.iloc[-6]["close"]) / df.iloc[-6]["close"] * 100 if len(df) >= 6 else 0
    pct_20d = (close - df.iloc[-21]["close"]) / df.iloc[-21]["close"] * 100 if len(df) >= 21 else 0

    return {
        "symbol": symbol,
        "date": last["date"].strftime("%Y-%m-%d"),
        "close": round(float(close), 2),
        "pct_change_1d": round(float(pct_1d), 2),
        "pct_change_5d": round(float(pct_5d), 2),
        "pct_change_20d": round(float(pct_20d), 2),
        "MA5": round(float(ma5), 2) if ma5 else None,
        "MA20": round(float(ma20), 2) if ma20 else None,
        "MA60": round(float(ma60), 2) if ma60 else None,
        "DIF": round(float(dif), 4) if dif else None,
        "DEA": round(float(dea), 4) if dea else None,
        "signals": [{"name": s[0], "score": s[1], "desc": s[2]} for s in trend_signals],
        "total_score": score,
        "max_score": max_score,
        "overall": overall,
    }


# ============================================================
# 2. 大盘支撑压力位
# ============================================================
def calc_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict:
    """计算支撑位/压力位
    Args:
        df: K线数据
        window: 窗口
    """
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
        "R1": round(float(r1), 2),
        "R2": round(float(r2), 2),
        "S1": round(float(s1), 2),
        "S2": round(float(s2), 2),
        "period_high": round(float(recent["high"].max()), 2),
        "period_low": round(float(recent["low"].min()), 2),
    }


# ============================================================
# 3. 大盘量价分析
# ============================================================
def analyze_volume_price(df: pd.DataFrame) -> Dict:
    """量价分析"""
    if df.empty or len(df) < 5:
        return {}

    last = df.iloc[-1]
    avg_vol_5 = df["volume"].tail(5).mean()
    avg_vol_20 = df["volume"].tail(20).mean()
    vol_ratio_5 = last["volume"] / avg_vol_5 if avg_vol_5 else 1
    vol_ratio_20 = last["volume"] / avg_vol_20 if avg_vol_20 else 1

    change = (last["close"] - df.iloc[-2]["close"]) / df.iloc[-2]["close"] * 100

    signal = "正常"
    if vol_ratio_5 > 1.5 and change > 0:
        signal = "放量上涨"
    elif vol_ratio_5 > 1.5 and change < 0:
        signal = "放量下跌"
    elif vol_ratio_5 < 0.7 and change > 0:
        signal = "缩量上涨 (需警惕)"
    elif vol_ratio_5 < 0.7 and change < 0:
        signal = "缩量下跌 (抛压衰竭)"

    return {
        "today_vol": float(last["volume"]),
        "avg_vol_5": round(float(avg_vol_5), 2),
        "avg_vol_20": round(float(avg_vol_20), 2),
        "vol_ratio_5": round(float(vol_ratio_5), 2),
        "vol_ratio_20": round(float(vol_ratio_20), 2),
        "pct_change": round(float(change), 2),
        "signal": signal,
    }


# ============================================================
# 4. 综合大盘研判
# ============================================================
def full_market_analysis(symbol: str = "000001", days: int = 60) -> Dict:
    """综合大盘研判
    Args:
        symbol: 指数代码
        days: 分析周期
    """
    trend = analyze_index_trend(symbol, days)
    if not trend:
        return {}

    try:
        import akshare as ak
        if symbol.startswith("000") or symbol.startswith("6"):
            df = ak.stock_zh_index_daily(symbol=f"sh{symbol}")
        else:
            df = ak.stock_zh_index_daily(symbol=f"sz{symbol}")
        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"])
        df = df.tail(days).reset_index(drop=True)
    except:
        df = pd.DataFrame()

    support_resistance = calc_support_resistance(df) if not df.empty else {}
    volume_price = analyze_volume_price(df) if not df.empty else {}

    # 生成操作建议
    score = trend.get("total_score", 0)
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

    return {
        "trend": trend,
        "support_resistance": support_resistance,
        "volume_price": volume_price,
        "advice": advice,
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 上证指数综合分析 ===")
    result = full_market_analysis("000001", days=60)
    if result:
        print(f"\n【趋势研判】 {result['trend']['overall']} (评分: {result['trend']['total_score']})")
        for s in result['trend']['signals']:
            print(f"  - {s['name']}: {s['desc']}")
        print(f"\n【操作建议】 {result['advice']}")

        if result['support_resistance']:
            sr = result['support_resistance']
            print(f"\n【支撑压力】")
            print(f"  R2: {sr['R2']} | R1: {sr['R1']} | Pivot: {sr['pivot']}")
            print(f"  S1: {sr['S1']} | S2: {sr['S2']}")

        if result['volume_price']:
            vp = result['volume_price']
            print(f"\n【量价分析】 {vp['signal']}")
            print(f"  量比5日: {vp['vol_ratio_5']} | 量比20日: {vp['vol_ratio_20']}")
