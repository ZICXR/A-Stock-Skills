#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backtest: 策略回测 (基础 + 专业 + 多信号 3合1)

合并: strategy-backtest + advanced-backtest + multi-signal-backtest
"""

import os
import sys
import json
import itertools
import argparse
import warnings
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")


# ============================================================
# 通用数据获取
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


def get_all_stocks() -> List[str]:
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df.empty:
            return []
        if "名称" in df.columns:
            df = df[~df["名称"].astype(str).str.contains("ST", na=False)]
        if "最新价" in df.columns:
            df = df[df["最新价"] > 0]
        if "总市值" in df.columns:
            df = df[df["总市值"] > 30e8]
        return df["代码"].astype(str).tolist() if "代码" in df.columns else []
    except Exception:
        return []


# ============================================================
# 信号计算
# ============================================================
def calc_signals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 30:
        return df
    df = df.copy()
    df["MA5"] = df["close"].rolling(5).mean()
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA60"] = df["close"].rolling(60).mean()
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI6"] = 100 - 100 / (1 + rs)
    low_n = df["low"].rolling(9).min()
    high_n = df["high"].rolling(9).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    df["K"] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df["D"] = df["K"].ewm(alpha=1/3, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]
    if "volume" in df.columns:
        df["vol_ma5"] = df["volume"].rolling(5).mean()

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


# ============================================================
# 基础回测 (strategy-backtest 合并)
# ============================================================
def run_strategy(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    df = df.copy()
    df["signal"] = 0
    if strategy == "ma_cross":
        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df.loc[df["MA5"] > df["MA20"], "signal"] = 1
        df.loc[df["MA5"] < df["MA20"], "signal"] = -1
    elif strategy == "macd_cross":
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        df.loc[dif > dea, "signal"] = 1
        df.loc[dif < dea, "signal"] = -1
    elif strategy == "momentum":
        df["returns"] = df["close"].pct_change(20)
        df.loc[df["returns"] > 0.05, "signal"] = 1
        df.loc[df["returns"] < -0.05, "signal"] = -1
    elif strategy == "turtle":
        df["high_20"] = df["high"].rolling(20).max()
        df["low_20"] = df["low"].rolling(20).min()
        df.loc[df["close"] > df["high_20"].shift(1), "signal"] = 1
        df.loc[df["close"] < df["low_20"].shift(1), "signal"] = -1
    return df


def basic_backtest(strategy: str, code: str, params: Dict = None) -> Dict:
    if params is None:
        params = {}
    df = get_kline(code, days=365)
    if df.empty:
        return {}
    df = run_strategy(df, strategy)

    capital = 1.0
    position = 0
    entry_price = 0
    trades = []
    equity = [1.0]

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        sig = df["signal"].iloc[i]
        if sig == 1 and position == 0:
            position = capital / price
            entry_price = price
            capital = 0
        elif sig == -1 and position > 0:
            capital = position * price
            profit = (price - entry_price) / entry_price * 100
            trades.append({"profit_pct": round(profit, 2)})
            position = 0
        equity.append(capital if capital > 0 else position * price)

    return calc_metrics(equity, trades, 1.0)


# ============================================================
# 专业回测 (advanced-backtest 合并)
# ============================================================
DEFAULT_COSTS = {
    "commission": 0.00025, "stamp_tax": 0.001,
    "transfer_fee": 0.00001, "slippage": 0.001, "min_commission": 5.0,
}


def calc_buy_cost(amount, costs):
    return max(amount * costs["commission"], costs["min_commission"]) + amount * costs["transfer_fee"]


def calc_sell_cost(amount, costs):
    return (max(amount * costs["commission"], costs["min_commission"]) +
            amount * costs["stamp_tax"] + amount * costs["transfer_fee"])


def apply_slippage(price, direction, slippage):
    return price * (1 + slippage) if direction == "buy" else price * (1 - slippage)


def calc_position_size(mode, capital, price, costs, win_rate=0.5, pl_ratio=1.5):
    if mode == "all_in":
        shares = int(capital / price / 100) * 100
    elif mode == "equal_split":
        shares = int(capital / price / 3 / 100) * 100
    elif mode == "kelly":
        kelly = max(0, (pl_ratio * win_rate - (1 - win_rate)) / pl_ratio)
        kelly = min(kelly, 0.25)
        shares = int(capital * kelly / price / 100) * 100
    else:
        shares = int(capital * 0.3 / price / 100) * 100
    return max(shares, 0)


def advanced_backtest(strategy: str, code: str, costs: Dict = None,
                     position_mode: str = "all_in",
                     stop_loss: float = None, take_profit: float = None,
                     capital: float = 100000) -> Dict:
    if costs is None:
        costs = DEFAULT_COSTS.copy()
    df = get_kline(code, days=365)
    if df.empty:
        return {}
    df = run_strategy(df, strategy)

    cash = capital
    position = 0
    avg_cost = 0
    entry_price = 0
    trades = []
    equity_curve = [capital]

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        sig = df["signal"].iloc[i]
        if position > 0 and stop_loss and price < entry_price * (1 - stop_loss):
            sig = -1
        if position > 0 and take_profit and price > entry_price * (1 + take_profit):
            sig = -1

        if sig == 1 and position == 0 and cash > 0:
            buy_price = apply_slippage(price, "buy", costs["slippage"])
            shares = calc_position_size(position_mode, cash, buy_price, costs)
            if shares > 0:
                amount = shares * buy_price
                cost = calc_buy_cost(amount, costs)
                if cash >= amount + cost:
                    cash -= (amount + cost)
                    position = shares
                    entry_price = buy_price
                    avg_cost = (amount + cost) / shares

        elif sig == -1 and position > 0:
            sell_price = apply_slippage(price, "sell", costs["slippage"])
            amount = position * sell_price
            cost = calc_sell_cost(amount, costs)
            profit = (sell_price - avg_cost) * position - cost
            profit_pct = (sell_price - avg_cost) / avg_cost
            trades.append({
                "entry": round(entry_price, 2), "exit": round(sell_price, 2),
                "shares": position, "profit": round(profit, 2),
                "profit_pct": round(profit_pct * 100, 2),
            })
            cash += (amount - cost)
            position = 0

        equity_curve.append(cash + position * price)

    return calc_metrics(equity_curve, trades, capital)


# ============================================================
# 多信号组合回测 (multi-signal-backtest 合并)
# ============================================================
def multi_signal_backtest_single(code: str, signals: List[str], hold_days: int = 5) -> Dict:
    df = get_kline(code, days=365)
    if df.empty or len(df) < 60:
        return {"code": code, "hits": 0, "returns": []}
    df = calc_signals(df)
    if not signals:
        return {"code": code, "hits": 0, "returns": []}

    combined = df[f"sig_{signals[0]}"].astype(bool) if f"sig_{signals[0]}" in df.columns else pd.Series([False]*len(df))
    for sig in signals[1:]:
        col = f"sig_{sig}"
        if col in df.columns:
            combined = combined & df[col].astype(bool)
        else:
            return {"code": code, "hits": 0, "returns": []}

    hit_indices = df.index[combined].tolist()
    returns = []
    for idx in hit_indices:
        pos = df.index.get_loc(idx)
        if pos + hold_days >= len(df):
            continue
        buy_price = df["close"].iloc[pos]
        sell_price = df["close"].iloc[pos + hold_days]
        ret = (sell_price - buy_price) / buy_price * 100
        returns.append(ret)
    return {"code": code, "hits": len(returns), "returns": returns}


def multi_signal_backtest(signals: List[str], hold_days: int = 5, max_stocks: int = 500) -> Dict:
    scope = get_all_stocks()[:max_stocks]
    all_returns = []
    hit_count = 0
    stock_count = 0
    for code in scope:
        r = multi_signal_backtest_single(code, signals, hold_days)
        if r["hits"] > 0:
            all_returns.extend(r["returns"])
            hit_count += r["hits"]
            stock_count += 1
    if not all_returns:
        return {"signals": signals, "hits": 0, "win_rate": 0, "avg_return": 0}
    arr = np.array(all_returns)
    wins = arr[arr > 0]
    return {
        "signals": signals, "hold_days": hold_days,
        "hits": hit_count, "stock_count": stock_count,
        "win_rate": round(len(wins) / len(arr) * 100, 2),
        "avg_return": round(float(arr.mean()), 2),
        "median_return": round(float(np.median(arr)), 2),
        "max_return": round(float(arr.max()), 2),
        "min_return": round(float(arr.min()), 2),
    }


# ============================================================
# 通用指标计算
# ============================================================
def calc_metrics(equity_curve, trades, initial_capital):
    if len(equity_curve) < 2:
        return {}
    eq = pd.Series(equity_curve)
    total_return = (eq.iloc[-1] - initial_capital) / initial_capital * 100
    days = len(eq)
    annual_return = ((1 + total_return / 100) ** (252 / max(days, 1)) - 1) * 100
    cummax = eq.cummax()
    drawdown = (eq - cummax) / cummax
    max_drawdown = drawdown.min() * 100
    daily_ret = eq.pct_change().dropna()
    sharpe = (daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0

    if trades:
        wins = [t for t in trades if t.get("profit_pct", t.get("profit", 0)) > 0]
        win_rate = len(wins) / len(trades) * 100
    else:
        win_rate = 0

    return {
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 2),
        "trade_count": len(trades),
        "final_equity": round(float(eq.iloc[-1]), 2),
    }


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="backtest (3合1)")
    sub = parser.add_subparsers(dest="cmd")

    # 基础
    p = sub.add_parser("basic", help="基础回测")
    p.add_argument("--code", required=True)
    p.add_argument("--strategy", default="ma_cross")
    p.add_argument("--short", type=int, default=5)
    p.add_argument("--long", type=int, default=20)

    # 专业
    p = sub.add_parser("advanced", help="专业回测 (含成本)")
    p.add_argument("--code", required=True)
    p.add_argument("--strategy", default="ma_cross")
    p.add_argument("--position-mode", default="all_in",
                   choices=["all_in", "equal_split", "kelly", "fixed_fraction"])
    p.add_argument("--stop-loss", type=float)
    p.add_argument("--take-profit", type=float)
    p.add_argument("--capital", type=float, default=100000)

    # 多信号
    p = sub.add_parser("multi-signal", help="多信号组合")
    p.add_argument("--signals", help="信号列表, 逗号分隔")
    p.add_argument("--hold-days", type=int, default=5)
    p.add_argument("--max", type=int, default=500)
    p.add_argument("--optimize", action="store_true", help="自动优化")
    p.add_argument("--candidates", help="优化时的候选信号")

    # 批量
    p = sub.add_parser("batch", help="批量回测")
    p.add_argument("--codes", required=True)
    p.add_argument("--strategy", default="ma_cross")
    args = parser.parse_args()

    if args.cmd == "basic":
        params = {}
        if args.strategy == "ma_cross":
            params = {"short": args.short, "long": args.long}
        r = basic_backtest(args.strategy, args.code, params)
        print(f"策略: {args.strategy}, 代码: {args.code}")
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "advanced":
        r = advanced_backtest(args.strategy, args.code,
                              position_mode=args.position_mode,
                              stop_loss=args.stop_loss, take_profit=args.take_profit,
                              capital=args.capital)
        print(f"\n=== {args.code} 专业回测 ===")
        print(f"  策略: {args.strategy}")
        print(f"  仓位模式: {args.position_mode}")
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "multi-signal":
        if args.optimize:
            candidates = [s.strip() for s in args.candidates.split(",")]
            print(f"\n正在优化 {len(candidates)} 个信号组合...")
            results = []
            for size in range(2, min(4, len(candidates) + 1)):
                for combo in itertools.combinations(candidates, size):
                    r = multi_signal_backtest(list(combo), hold_days=args.hold_days, max_stocks=args.max)
                    if r["hits"] >= 5:
                        results.append(r)
            results.sort(key=lambda x: x.get("avg_return", 0), reverse=True)
            print(f"\n=== Top 5 组合 ===")
            for i, r in enumerate(results[:5], 1):
                print(f"{i}. {' + '.join(r['signals'])}: 胜率 {r['win_rate']}%, 收益 {r['avg_return']:+.2f}%")
        else:
            signals = [s.strip() for s in args.signals.split(",")]
            r = multi_signal_backtest(signals, hold_days=args.hold_days, max_stocks=args.max)
            print(f"\n=== 多信号组合回测 ===")
            print(f"信号: {' + '.join(signals)}")
            print(f"持仓: {r['hold_days']}日")
            for k, v in r.items():
                if k not in ("signals", "hold_days"):
                    print(f"  {k}: {v}")
    elif args.cmd == "batch":
        codes = [c.strip() for c in args.codes.split(",")]
        results = []
        for code in codes:
            r = basic_backtest(args.strategy, code)
            if r:
                r["code"] = code
                results.append(r)
        results.sort(key=lambda x: x.get("annual_return", 0), reverse=True)
        print(f"\n=== 多股对比 ({args.strategy}) ===")
        for r in results:
            print(f"  {r['code']}: 年化 {r.get('annual_return', 0):.2f}%, "
                  f"夏普 {r.get('sharpe', 0):.2f}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
