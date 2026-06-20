#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""strategy-backtest: 策略回测"""

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
def strategy_ma_cross(df: pd.DataFrame, short: int = 5, long: int = 20) -> pd.DataFrame:
    """均线交叉策略"""
    df = df.copy()
    df[f"MA{short}"] = df["close"].rolling(short).mean()
    df[f"MA{long}"] = df["close"].rolling(long).mean()
    df["signal"] = 0
    df.loc[df[f"MA{short}"] > df[f"MA{long}"], "signal"] = 1
    df.loc[df[f"MA{short}"] < df[f"MA{long}"], "signal"] = -1
    return df


def strategy_macd_cross(df: pd.DataFrame) -> pd.DataFrame:
    """MACD 策略"""
    df = df.copy()
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
    df["signal"] = 0
    df.loc[df["DIF"] > df["DEA"], "signal"] = 1
    df.loc[df["DIF"] < df["DEA"], "signal"] = -1
    return df


def strategy_momentum(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """动量策略"""
    df = df.copy()
    df["returns"] = df["close"].pct_change(lookback)
    df["signal"] = 0
    df.loc[df["returns"] > 0.05, "signal"] = 1
    df.loc[df["returns"] < -0.05, "signal"] = -1
    return df


# ============================================================
# 回测核心
# ============================================================
def run_backtest(df: pd.DataFrame) -> Dict:
    """运行回测, 返回交易明细和资金曲线"""
    if df.empty or "signal" not in df.columns:
        return {}

    capital = 1.0
    position = 0
    entry_price = 0
    trades = []
    equity = [1.0]

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        sig = df["signal"].iloc[i]
        # 买入
        if sig == 1 and position == 0:
            position = capital / price
            entry_price = price
            capital = 0
        # 卖出
        elif sig == -1 and position > 0:
            capital = position * price
            profit = (price - entry_price) / entry_price * 100
            trades.append({
                "entry_price": entry_price,
                "exit_price": price,
                "profit_pct": round(profit, 2),
            })
            position = 0

        # 计算当前权益
        if position > 0:
            equity.append(position * price)
        else:
            equity.append(capital if capital > 0 else 1.0)

    return {"equity": equity, "trades": trades, "df": df}


def calc_metrics(equity_curve: List[float]) -> Dict:
    """计算回测指标"""
    if not equity_curve or len(equity_curve) < 2:
        return {}

    eq = pd.Series(equity_curve)
    total_return = (eq.iloc[-1] - eq.iloc[0]) / eq.iloc[0]

    # 年化收益 (按 252 交易日)
    days = len(eq)
    annual_return = (1 + total_return) ** (252 / max(days, 1)) - 1

    # 最大回撤
    cummax = eq.cummax()
    drawdown = (eq - cummax) / cummax
    max_drawdown = drawdown.min()

    # 夏普
    daily_ret = eq.pct_change().dropna()
    sharpe = (daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0

    return {
        "total_return": round(total_return * 100, 2),
        "annual_return": round(annual_return * 100, 2),
        "max_drawdown": round(max_drawdown * 100, 2),
        "sharpe": round(sharpe, 2),
    }


def calc_trade_stats(trades: List[Dict]) -> Dict:
    """交易统计"""
    if not trades:
        return {"win_rate": 0, "trade_count": 0}
    wins = [t for t in trades if t["profit_pct"] > 0]
    losses = [t for t in trades if t["profit_pct"] <= 0]
    win_rate = len(wins) / len(trades) if trades else 0
    avg_profit = np.mean([t["profit_pct"] for t in wins]) if wins else 0
    avg_loss = np.mean([t["profit_pct"] for t in losses]) if losses else 0
    pl_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
    return {
        "win_rate": round(win_rate * 100, 2),
        "trade_count": len(trades),
        "avg_profit": round(avg_profit, 2),
        "avg_loss": round(avg_loss, 2),
        "pl_ratio": round(pl_ratio, 2),
    }


def backtest(strategy: str, code: str, params: Dict = None) -> Dict:
    """回测入口"""
    if params is None:
        params = {}
    df = get_kline(code, days=365)
    if df.empty:
        return {}

    if strategy == "ma_cross":
        df = strategy_ma_cross(df, params.get("short", 5), params.get("long", 20))
    elif strategy == "macd_cross":
        df = strategy_macd_cross(df)
    elif strategy == "momentum":
        df = strategy_momentum(df, params.get("lookback", 20))
    else:
        return {"error": f"未知策略: {strategy}"}

    result = run_backtest(df)
    metrics = calc_metrics(result.get("equity", []))
    stats = calc_trade_stats(result.get("trades", []))
    return {**metrics, **stats}


def batch_backtest(strategy: str, codes: List[str], params: Dict = None) -> List[Dict]:
    """批量回测"""
    results = []
    for code in codes:
        r = backtest(strategy, code, params)
        if r and "error" not in r:
            r["code"] = code
            results.append(r)
    return results


def main():
    parser = argparse.ArgumentParser(description="strategy-backtest")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("backtest", help="回测")
    p.add_argument("strategy", choices=["ma_cross", "macd_cross", "momentum"])
    p.add_argument("--code", required=True)
    p.add_argument("--short", type=int, default=5)
    p.add_argument("--long", type=int, default=20)
    p.add_argument("--lookback", type=int, default=20)
    p = sub.add_parser("batch", help="批量回测")
    p.add_argument("strategy", choices=["ma_cross", "macd_cross", "momentum"])
    p.add_argument("--codes", required=True)
    args = parser.parse_args()

    if args.cmd == "backtest":
        params = {}
        if args.strategy == "ma_cross":
            params = {"short": args.short, "long": args.long}
        elif args.strategy == "momentum":
            params = {"lookback": args.lookback}
        r = backtest(args.strategy, args.code, params)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "batch":
        codes = [c.strip() for c in args.codes.split(",")]
        results = batch_backtest(args.strategy, codes)
        for r in results:
            print(f"{r['code']}: 年化{r.get('annual_return', 0):.2f}%, 夏普{r.get('sharpe', 0):.2f}, 最大回撤{r.get('max_drawdown', 0):.2f}%")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
