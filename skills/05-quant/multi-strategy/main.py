#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multi-strategy: 多策略组合器"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List
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


# ============================================================
# 策略实现
# ============================================================
def strategy_double_ma(df: pd.DataFrame, short: int = 5, long: int = 20) -> Dict:
    """双均线"""
    if df.empty or len(df) < long + 1:
        return {"signal": "数据不足"}
    ma_s = df["close"].rolling(short).mean()
    ma_l = df["close"].rolling(long).mean()
    if ma_s.iloc[-1] > ma_l.iloc[-1] and ma_s.iloc[-2] <= ma_l.iloc[-2]:
        return {"signal": "买入", "desc": f"MA{short}上穿MA{long}"}
    elif ma_s.iloc[-1] < ma_l.iloc[-1] and ma_s.iloc[-2] >= ma_l.iloc[-2]:
        return {"signal": "卖出", "desc": f"MA{short}下穿MA{long}"}
    return {"signal": "持仓" if ma_s.iloc[-1] > ma_l.iloc[-1] else "观望"}


def strategy_turtle(df: pd.DataFrame, period: int = 20) -> Dict:
    """海龟交易: 突破 N 日新高买入, 跌破 N 日新低卖出"""
    if df.empty or len(df) < period + 1:
        return {"signal": "数据不足"}
    high_n = df["high"].rolling(period).max()
    low_n = df["low"].rolling(period).min()
    if df["close"].iloc[-1] > high_n.iloc[-2]:
        return {"signal": "买入", "desc": f"突破{period}日新高"}
    elif df["close"].iloc[-1] < low_n.iloc[-2]:
        return {"signal": "卖出", "desc": f"跌破{period}日新低"}
    return {"signal": "持仓" if df["close"].iloc[-1] > high_n.iloc[-2] else "观望"}


def strategy_bollinger(df: pd.DataFrame, n: int = 20, k: float = 2) -> Dict:
    """布林带: 跌破下轨买入, 突破上轨卖出"""
    if df.empty or len(df) < n:
        return {"signal": "数据不足"}
    mid = df["close"].rolling(n).mean()
    std = df["close"].rolling(n).std()
    upper = mid + k * std
    lower = mid - k * std
    last = df["close"].iloc[-1]
    if last < lower.iloc[-1]:
        return {"signal": "买入", "desc": "跌破布林下轨"}
    elif last > upper.iloc[-1]:
        return {"signal": "卖出", "desc": "突破布林上轨"}
    return {"signal": "持仓"}


def strategy_grid(df: pd.DataFrame, grid_count: int = 5) -> Dict:
    """网格交易 (基于 N 日高低点划分网格)"""
    if df.empty or len(df) < 60:
        return {"signal": "数据不足"}
    high = df["high"].tail(60).max()
    low = df["low"].tail(60).min()
    last = df["close"].iloc[-1]
    grid_size = (high - low) / grid_count
    current_grid = int((last - low) / grid_size) if grid_size else 0
    if current_grid == 0:
        return {"signal": "买入", "desc": "网格最低位"}
    elif current_grid >= grid_count - 1:
        return {"signal": "卖出", "desc": "网格最高位"}
    return {"signal": "持仓", "desc": f"网格{current_grid}/{grid_count}"}


def strategy_mean_reversion(df: pd.DataFrame, n: int = 20, threshold: float = -0.05) -> Dict:
    """均值回归: 偏离均值超过阈值买入"""
    if df.empty or len(df) < n:
        return {"signal": "数据不足"}
    ma = df["close"].rolling(n).mean().iloc[-1]
    last = df["close"].iloc[-1]
    deviation = (last - ma) / ma
    if deviation < threshold:
        return {"signal": "买入", "desc": f"偏离MA{n}{deviation*100:.1f}%"}
    elif deviation > -threshold:
        return {"signal": "卖出", "desc": f"高于MA{n}{-deviation*100:.1f}%"}
    return {"signal": "观望"}


def strategy_momentum(df: pd.DataFrame, lookback: int = 20) -> Dict:
    """动量"""
    if df.empty or len(df) < lookback + 1:
        return {"signal": "数据不足"}
    ret = (df["close"].iloc[-1] - df["close"].iloc[-lookback - 1]) / df["close"].iloc[-lookback - 1]
    if ret > 0.10:
        return {"signal": "买入", "desc": f"{lookback}日涨幅{ret*100:.1f}%"}
    elif ret < -0.10:
        return {"signal": "卖出", "desc": f"{lookback}日跌幅{-ret*100:.1f}%"}
    return {"signal": "观望"}


def strategy_rsi(df: pd.DataFrame, period: int = 6) -> Dict:
    """RSI 反转"""
    if df.empty or len(df) < period + 1:
        return {"signal": "数据不足"}
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).iloc[-1]
    if rsi < 30:
        return {"signal": "买入", "desc": f"RSI={rsi:.0f}超卖"}
    elif rsi > 70:
        return {"signal": "卖出", "desc": f"RSI={rsi:.0f}超买"}
    return {"signal": "观望"}


def strategy_kdj(df: pd.DataFrame) -> Dict:
    """KDJ"""
    if df.empty or len(df) < 15:
        return {"signal": "数据不足"}
    low_n = df["low"].rolling(9).min()
    high_n = df["high"].rolling(9).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    d = k.ewm(alpha=1/3, adjust=False).mean()
    if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2] and k.iloc[-1] < 50:
        return {"signal": "买入", "desc": "KDJ低位金叉"}
    elif k.iloc[-1] < d.iloc[-1] and k.iloc[-2] >= d.iloc[-2] and k.iloc[-1] > 50:
        return {"signal": "卖出", "desc": "KDJ高位死叉"}
    return {"signal": "观望"}


def strategy_macd(df: pd.DataFrame) -> Dict:
    """MACD"""
    if df.empty or len(df) < 30:
        return {"signal": "数据不足"}
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
        return {"signal": "买入", "desc": "MACD金叉"}
    elif dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2]:
        return {"signal": "卖出", "desc": "MACD死叉"}
    return {"signal": "持仓" if dif.iloc[-1] > dea.iloc[-1] else "观望"}


def strategy_breakout(df: pd.DataFrame, n: int = 60) -> Dict:
    """突破策略: 突破 N 日新高"""
    if df.empty or len(df) < n:
        return {"signal": "数据不足"}
    if df["close"].iloc[-1] >= df["high"].tail(n).max():
        return {"signal": "买入", "desc": f"突破{n}日新高"}
    return {"signal": "观望"}


# 策略注册
STRATEGIES = {
    "double_ma": strategy_double_ma,
    "turtle": strategy_turtle,
    "bollinger": strategy_bollinger,
    "grid": strategy_grid,
    "mean_reversion": strategy_mean_reversion,
    "momentum": strategy_momentum,
    "rsi": strategy_rsi,
    "kdj": strategy_kdj,
    "macd": strategy_macd,
    "breakout": strategy_breakout,
}


# ============================================================
# 策略运行与投票
# ============================================================
def run_strategy(name: str, code: str) -> Dict:
    """运行单个策略"""
    df = get_kline(code)
    if df.empty:
        return {"signal": "无数据"}
    func = STRATEGIES.get(name)
    if not func:
        return {"error": f"未知策略: {name}"}
    result = func(df)
    result["strategy"] = name
    return result


def multi_strategy_vote(strategies: List[str], code: str) -> Dict:
    """多策略投票"""
    signals = []
    details = []
    for s in strategies:
        r = run_strategy(s, code)
        details.append(r)
        if r.get("signal") == "买入":
            signals.append(1)
        elif r.get("signal") == "卖出":
            signals.append(-1)
        else:
            signals.append(0)
    buy = signals.count(1)
    sell = signals.count(-1)
    if buy > sell:
        final = "买入"
        strength = "强" if buy >= len(signals) * 0.7 else "中"
    elif sell > buy:
        final = "卖出"
        strength = "强" if sell >= len(signals) * 0.7 else "中"
    else:
        final = "观望"
        strength = "中性"
    return {
        "buy": buy, "sell": sell, "hold": signals.count(0),
        "total": len(signals),
        "signal": final, "strength": strength,
        "details": details,
    }


def optimize_double_ma(code: str) -> List[Dict]:
    """双均线参数优化"""
    df = get_kline(code)
    if df.empty:
        return []
    results = []
    for short in [3, 5, 7, 10]:
        for long in [10, 15, 20, 30, 60]:
            if short >= long:
                continue
            ma_s = df["close"].rolling(short).mean()
            ma_l = df["close"].rolling(long).mean()
            signals = (ma_s > ma_l).astype(int).diff()
            buys = signals[signals > 0].index
            if len(buys) == 0:
                continue
            # 简化收益
            rets = []
            for b in buys:
                if b + long < len(df):
                    ret = (df["close"].iloc[b + long] - df["close"].iloc[b]) / df["close"].iloc[b]
                    rets.append(ret)
            if rets:
                avg_ret = np.mean(rets)
                results.append({
                    "short": short, "long": long,
                    "trades": len(rets), "avg_return": round(avg_ret * 100, 2),
                })
    results.sort(key=lambda x: x["avg_return"], reverse=True)
    return results[:10]


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="multi-strategy")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("list", help="列出所有策略")
    p = sub.add_parser("backtest", help="回测单策略")
    p.add_argument("strategy")
    p.add_argument("--code", required=True)
    p = sub.add_parser("vote", help="多策略投票")
    p.add_argument("--code", required=True)
    p.add_argument("--strategies", required=True)
    p = sub.add_parser("optimize", help="参数优化")
    p.add_argument("strategy")
    p.add_argument("--code", required=True)
    args = parser.parse_args()

    if args.cmd == "list":
        print("可用策略:")
        for name in STRATEGIES:
            print(f"  - {name}")
    elif args.cmd == "backtest":
        r = run_strategy(args.strategy, args.code)
        print(f"策略: {r.get('strategy')}, 信号: {r.get('signal')}")
        if r.get("desc"):
            print(f"  描述: {r['desc']}")
    elif args.cmd == "vote":
        strategies = [s.strip() for s in args.strategies.split(",")]
        r = multi_strategy_vote(strategies, args.code)
        print(f"\n=== 多策略投票 ({r['total']} 个策略) ===")
        print(f"买入: {r['buy']}, 卖出: {r['sell']}, 观望: {r['hold']}")
        print(f"最终信号: {r['signal']} ({r['strength']})")
        print("\n各策略详情:")
        for d in r["details"]:
            print(f"  [{d.get('strategy')}] {d.get('signal')}: {d.get('desc', '')}")
    elif args.cmd == "optimize":
        if args.strategy == "double_ma":
            r = optimize_double_ma(args.code)
            print(f"\n=== 双均线参数优化 Top 10 ===")
            for x in r:
                print(f"  MA({x['short']},{x['long']}): 收益 {x['avg_return']:+.2f}%, 交易 {x['trades']} 次")
        else:
            print("暂只支持 double_ma 参数优化")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
