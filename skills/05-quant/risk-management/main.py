#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""risk-management: 风险管理"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


def get_kline(code: str, days: int = 120) -> pd.DataFrame:
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


def calc_var(returns: List[float], confidence: float = 0.95) -> Dict:
    """VaR (Value at Risk)"""
    arr = np.array(returns)
    if len(arr) == 0:
        return {}
    var = np.quantile(arr, 1 - confidence)
    var_pct = abs(var) * 100
    if var_pct < 1:
        level = "低风险"
    elif var_pct < 3:
        level = "中低风险"
    elif var_pct < 5:
        level = "中等风险"
    elif var_pct < 10:
        level = "高风险"
    else:
        level = "极高风险"
    return {
        "var_95": round(var * 100, 2),
        "confidence": confidence,
        "level": level,
    }


def calc_max_drawdown(equity_curve: List[float]) -> Dict:
    """最大回撤"""
    if not equity_curve or len(equity_curve) < 2:
        return {}
    eq = pd.Series(equity_curve)
    cummax = eq.cummax()
    drawdown = (eq - cummax) / cummax
    mdd = drawdown.min()
    # 找到回撤区间
    end_idx = drawdown.idxmin()
    start_idx = eq[:end_idx + 1].idxmax()
    return {
        "max_drawdown": round(mdd * 100, 2),
        "start_idx": int(start_idx),
        "end_idx": int(end_idx),
    }


def calc_sharpe(returns: List[float], risk_free: float = 0.03) -> Dict:
    """夏普比率"""
    arr = np.array(returns)
    if len(arr) == 0 or arr.std() == 0:
        return {"sharpe": 0}
    excess = arr - risk_free / 252
    sharpe = excess.mean() / arr.std() * np.sqrt(252)
    level = "优秀" if sharpe > 2 else "良好" if sharpe > 1 else "一般" if sharpe > 0 else "差"
    return {"sharpe": round(sharpe, 2), "level": level}


def calc_volatility(returns: List[float], annual: bool = True) -> Dict:
    """波动率"""
    arr = np.array(returns)
    if len(arr) == 0:
        return {}
    vol = arr.std()
    if annual:
        vol = vol * np.sqrt(252)
    return {"volatility": round(vol * 100, 2), "annual": annual}


def position_suggestion(capital: float, risk_per_trade: float = 0.02, stop_loss: float = 0.05) -> Dict:
    """仓位建议 (凯利公式简化版)"""
    if stop_loss <= 0 or risk_per_trade <= 0:
        return {}
    risk_amount = capital * risk_per_trade
    position_value = risk_amount / stop_loss
    if position_value > capital:
        position_value = capital
    position_pct = position_value / capital
    return {
        "capital": capital,
        "risk_per_trade": risk_per_trade,
        "stop_loss": stop_loss,
        "risk_amount": round(risk_amount, 2),
        "position_value": round(position_value, 2),
        "position_pct": round(position_pct * 100, 2),
    }


def stop_loss_strategy(code: str, days: int = 60, atr_multiplier: float = 2) -> Dict:
    """ATR 止损策略"""
    df = get_kline(code, days=days)
    if df.empty or len(df) < 20:
        return {}
    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        abs(df["high"] - df["close"].shift()),
        abs(df["low"] - df["close"].shift()),
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    last_close = df["close"].iloc[-1]
    return {
        "code": code,
        "price": round(float(last_close), 2),
        "ATR": round(float(atr), 2),
        "stop_loss": round(float(last_close - atr * atr_multiplier), 2),
        "stop_loss_pct": round((atr * atr_multiplier / last_close) * 100, 2),
        "take_profit": round(float(last_close + atr * atr_multiplier * 1.5), 2),
    }


def full_risk_report(code: str, days: int = 90) -> Dict:
    """完整风险报告"""
    df = get_kline(code, days=days)
    if df.empty:
        return {}
    returns = df["close"].pct_change().dropna().tolist()
    equity = [1.0]
    for r in returns:
        equity.append(equity[-1] * (1 + r))
    return {
        "code": code,
        "var": calc_var(returns),
        "max_drawdown": calc_max_drawdown(equity),
        "sharpe": calc_sharpe(returns),
        "volatility": calc_volatility(returns),
    }


def main():
    parser = argparse.ArgumentParser(description="risk-management")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("var", help="VaR")
    p.add_argument("code")
    p.add_argument("--days", type=int, default=90)
    p = sub.add_parser("position", help="仓位建议")
    p.add_argument("--capital", type=float, required=True)
    p.add_argument("--risk", type=float, default=0.02)
    p.add_argument("--stop", type=float, default=0.05)
    p = sub.add_parser("stop", help="止损")
    p.add_argument("code")
    p.add_argument("--strategy", default="atr", choices=["atr"])
    p = sub.add_parser("report", help="风险报告")
    p.add_argument("code")
    p.add_argument("--days", type=int, default=90)
    args = parser.parse_args()

    if args.cmd == "var":
        df = get_kline(args.code, days=args.days)
        if not df.empty:
            returns = df["close"].pct_change().dropna().tolist()
            r = calc_var(returns)
            for k, v in r.items():
                print(f"  {k}: {v}")
    elif args.cmd == "position":
        r = position_suggestion(args.capital, args.risk, args.stop)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "stop":
        r = stop_loss_strategy(args.code)
        for k, v in r.items():
            print(f"  {k}: {v}")
    elif args.cmd == "report":
        r = full_risk_report(args.code, args.days)
        import json
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
