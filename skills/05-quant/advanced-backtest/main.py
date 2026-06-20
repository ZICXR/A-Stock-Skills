#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""advanced-backtest: 专业回测引擎"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


# 默认 A 股交易成本
DEFAULT_COSTS = {
    "commission": 0.00025,   # 佣金 0.025%
    "stamp_tax": 0.001,      # 印花税 0.1% (仅卖出)
    "transfer_fee": 0.00001,  # 过户费
    "slippage": 0.001,       # 滑点 0.1%
    "min_commission": 5.0,    # 最低佣金 5 元
}


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
# 成本计算
# ============================================================
def calc_buy_cost(amount: float, costs: Dict) -> float:
    """买入成本 (不含印花税)"""
    commission = max(amount * costs["commission"], costs["min_commission"])
    transfer = amount * costs["transfer_fee"]
    return commission + transfer


def calc_sell_cost(amount: float, costs: Dict) -> float:
    """卖出成本 (含印花税)"""
    commission = max(amount * costs["commission"], costs["min_commission"])
    stamp = amount * costs["stamp_tax"]
    transfer = amount * costs["transfer_fee"]
    return commission + stamp + transfer


def apply_slippage(price: float, direction: str, slippage: float) -> float:
    """应用滑点"""
    if direction == "buy":
        return price * (1 + slippage)
    return price * (1 - slippage)


# ============================================================
# 策略实现 (与基础版相同, 但生成交易信号)
# ============================================================
def generate_signals(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """生成买卖信号 (1=买, -1=卖, 0=持仓)"""
    df = df.copy()
    df["signal"] = 0

    if strategy == "ma_cross":
        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df.loc[df["MA5"] > df["MA20"], "signal"] = 1
        df.loc[df["MA5"] < df["MA20"], "signal"] = -1
    elif strategy == "turtle":
        df["high_20"] = df["high"].rolling(20).max()
        df["low_20"] = df["low"].rolling(20).min()
        df.loc[df["close"] > df["high_20"].shift(1), "signal"] = 1
        df.loc[df["close"] < df["low_20"].shift(1), "signal"] = -1
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
    return df


# ============================================================
# 仓位管理
# ============================================================
def calc_position_size(mode: str, capital: float, price: float, costs: Dict,
                       win_rate: float = 0.5, pl_ratio: float = 1.5) -> float:
    """计算仓位"""
    if mode == "all_in":
        shares = int(capital / price / 100) * 100  # A 股 100 股一手
    elif mode == "equal_split":
        shares = int(capital / price / 3 / 100) * 100
    elif mode == "kelly":
        # 凯利公式: f = (bp - q) / b
        # b = 盈亏比, p = 胜率, q = 1 - 胜率
        kelly = max(0, (pl_ratio * win_rate - (1 - win_rate)) / pl_ratio)
        kelly = min(kelly, 0.25)  # 限制最大 25%
        shares = int(capital * kelly / price / 100) * 100
    elif mode == "fixed_fraction":
        shares = int(capital * 0.3 / price / 100) * 100
    else:
        shares = int(capital / price / 100) * 100
    return max(shares, 0)


# ============================================================
# 主回测引擎
# ============================================================
def backtest(strategy: str, code: str, costs: Dict = None, position_mode: str = "all_in",
              stop_loss: float = None, take_profit: float = None,
              capital: float = 100000) -> Dict:
    """专业回测"""
    if costs is None:
        costs = DEFAULT_COSTS.copy()

    df = get_kline(code, days=365)
    if df.empty:
        return {}

    df = generate_signals(df, strategy)

    cash = capital
    position = 0  # 持仓股数
    avg_cost = 0  # 持仓成本
    entry_price = 0
    trades = []
    equity_curve = [capital]

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        sig = df["signal"].iloc[i]

        # 止损止盈检查
        if position > 0 and stop_loss and price < entry_price * (1 - stop_loss):
            sig = -1  # 触发止损
        if position > 0 and take_profit and price > entry_price * (1 + take_profit):
            sig = -1  # 触发止盈

        # 买入
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

        # 卖出
        elif sig == -1 and position > 0:
            sell_price = apply_slippage(price, "sell", costs["slippage"])
            amount = position * sell_price
            cost = calc_sell_cost(amount, costs)
            profit = (sell_price - avg_cost) * position - cost
            profit_pct = (sell_price - avg_cost) / avg_cost
            trades.append({
                "entry": round(entry_price, 2),
                "exit": round(sell_price, 2),
                "shares": position,
                "profit": round(profit, 2),
                "profit_pct": round(profit_pct * 100, 2),
            })
            cash += (amount - cost)
            position = 0

        # 计算当前权益
        equity = cash + position * price
        equity_curve.append(equity)

    # 计算指标
    return calc_metrics(equity_curve, trades, capital)


def calc_metrics(equity_curve: List[float], trades: List[Dict], initial_capital: float) -> Dict:
    """计算回测指标"""
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
        wins = [t for t in trades if t["profit"] > 0]
        losses = [t for t in trades if t["profit"] <= 0]
        win_rate = len(wins) / len(trades) * 100
        avg_win = np.mean([t["profit_pct"] for t in wins]) if wins else 0
        avg_loss = np.mean([t["profit_pct"] for t in losses]) if losses else 0
        pl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        total_cost = sum(abs(t["profit"]) for t in trades) - sum(t["profit"] for t in trades)
    else:
        win_rate = avg_win = avg_loss = pl_ratio = total_cost = 0

    return {
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "pl_ratio": round(pl_ratio, 2),
        "trade_count": len(trades),
        "final_equity": round(float(eq.iloc[-1]), 2),
    }


# ============================================================
# 多股票对比
# ============================================================
def compare_stocks(strategy: str, codes: List[str], costs: Dict = None) -> pd.DataFrame:
    """多股票对比"""
    results = []
    for code in codes:
        r = backtest(strategy, code, costs=costs)
        if r:
            r["code"] = code
            results.append(r)
    return pd.DataFrame(results).sort_values("annual_return", ascending=False)


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="advanced-backtest")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("run", help="回测")
    p.add_argument("--code", required=True)
    p.add_argument("--strategy", default="ma_cross")
    p.add_argument("--commission", type=float, default=0.00025)
    p.add_argument("--stamp_tax", type=float, default=0.001)
    p.add_argument("--slippage", type=float, default=0.001)
    p.add_argument("--position_mode", default="all_in",
                   choices=["all_in", "equal_split", "kelly", "fixed_fraction"])
    p.add_argument("--stop_loss", type=float, help="止损比例 (0.05=5%)")
    p.add_argument("--take_profit", type=float, help="止盈比例")
    p.add_argument("--capital", type=float, default=100000)
    p.add_argument("--report", choices=["basic", "full"], default="full")
    p = sub.add_parser("compare", help="多股对比")
    p.add_argument("--codes", required=True)
    p.add_argument("--strategy", default="ma_cross")
    args = parser.parse_args()

    if args.cmd == "run":
        costs = {
            "commission": args.commission,
            "stamp_tax": args.stamp_tax,
            "transfer_fee": 0.00001,
            "slippage": args.slippage,
            "min_commission": 5.0,
        }
        r = backtest(args.strategy, args.code, costs=costs,
                     position_mode=args.position_mode,
                     stop_loss=args.stop_loss, take_profit=args.take_profit,
                     capital=args.capital)
        print(f"\n=== {args.code} 回测报告 ({args.strategy}) ===")
        print(f"  初始资金: {args.capital:,.0f} 元")
        print(f"  最终权益: {r.get('final_equity', 0):,.0f} 元")
        print(f"  总收益:   {r.get('total_return', 0):+.2f}%")
        print(f"  年化收益: {r.get('annual_return', 0):+.2f}%")
        print(f"  夏普:     {r.get('sharpe', 0):.2f}")
        print(f"  最大回撤: {r.get('max_drawdown', 0):.2f}%")
        print(f"  胜率:     {r.get('win_rate', 0):.2f}%")
        print(f"  盈亏比:   {r.get('pl_ratio', 0):.2f}")
        print(f"  交易次数: {r.get('trade_count', 0)}")
    elif args.cmd == "compare":
        codes = [c.strip() for c in args.codes.split(",")]
        df = compare_stocks(args.strategy, codes)
        if not df.empty:
            print(f"\n=== 多股对比 ({args.strategy}) ===")
            cols = ["code", "total_return", "annual_return", "sharpe", "max_drawdown", "win_rate"]
            print(df[cols].to_string())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
