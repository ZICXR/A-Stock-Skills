#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""signal-screener: 信号筛选器"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta


def get_kline(code: str, days: int = 60) -> pd.DataFrame:
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
# 信号判断函数
# ============================================================
def check_macd_golden(df: pd.DataFrame) -> bool:
    if df.empty or len(df) < 30:
        return False
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    return bool(dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2])


def check_macd_death(df: pd.DataFrame) -> bool:
    if df.empty or len(df) < 30:
        return False
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    return bool(dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2])


def check_above_ma(df: pd.DataFrame, period: int = 20) -> bool:
    if df.empty or len(df) < period:
        return False
    ma = df["close"].rolling(period).mean().iloc[-1]
    return bool(df["close"].iloc[-1] > ma)


def check_volume_break(df: pd.DataFrame, ratio: float = 1.5) -> bool:
    if df.empty or len(df) < 6 or "volume" not in df.columns:
        return False
    return bool(df["volume"].iloc[-1] > df["volume"].tail(5).mean() * ratio)


def check_rsi(df: pd.DataFrame, threshold: float, mode: str = "oversold") -> bool:
    if df.empty or len(df) < 20:
        return False
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).iloc[-1]
    if mode == "oversold":
        return bool(rsi < threshold)
    return bool(rsi > threshold)


def check_kdj_golden(df: pd.DataFrame) -> bool:
    if df.empty or len(df) < 15:
        return False
    low_n = df["low"].rolling(9).min()
    high_n = df["high"].rolling(9).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    d = k.ewm(alpha=1/3, adjust=False).mean()
    return bool(k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2] and k.iloc[-1] < 50)


def check_new_high(df: pd.DataFrame, n: int = 60) -> bool:
    if df.empty or len(df) < n:
        return False
    return bool(df["close"].iloc[-1] >= df["high"].tail(n).max())


def check_ma_cross(df: pd.DataFrame, short: int = 5, long: int = 20) -> bool:
    if df.empty or len(df) < long + 1:
        return False
    ma_s = df["close"].rolling(short).mean()
    ma_l = df["close"].rolling(long).mean()
    return bool(ma_s.iloc[-1] > ma_l.iloc[-1] and ma_s.iloc[-2] <= ma_l.iloc[-2])


# 信号注册表
SIGNAL_FUNCS = {
    "ma_cross": lambda df: check_ma_cross(df),
    "macd_golden": lambda df: check_macd_golden(df),
    "macd_death": lambda df: check_macd_death(df),
    "above_ma20": lambda df: check_above_ma(df, 20),
    "above_ma60": lambda df: check_above_ma(df, 60),
    "volume_break": lambda df: check_volume_break(df, 1.5),
    "volume_shrink": lambda df: check_volume_break(df, 0.7) and not check_volume_break(df, 0.7),
    "rsi_oversold": lambda df: check_rsi(df, 30, "oversold"),
    "rsi_overbought": lambda df: check_rsi(df, 70, "overbought"),
    "kdj_golden": lambda df: check_kdj_golden(df),
    "new_high_60": lambda df: check_new_high(df, 60),
}


# ============================================================
# 筛选
# ============================================================
def get_all_stocks() -> List[str]:
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        return df["代码"].astype(str).tolist()
    except Exception:
        return []


def screen(conditions: List[str], mode: str = "and", top_n: int = 30, scope: List[str] = None) -> List[Dict]:
    """筛选"""
    if scope is None:
        scope = get_all_stocks()[:200]  # 默认扫描前 200 (避免太慢)

    results = []
    for code in scope:
        try:
            df = get_kline(code, days=60)
            if df.empty:
                continue
            triggered = []
            for cond in conditions:
                func = SIGNAL_FUNCS.get(cond)
                if func and func(df):
                    triggered.append(cond)
            if not triggered:
                continue
            # 判断是否符合
            if mode == "and" and len(triggered) != len(conditions):
                continue
            # 获取基础信息
            try:
                import akshare as ak
                spot = ak.stock_zh_a_spot_em()
                target = spot[spot["代码"].astype(str) == code]
                if not target.empty:
                    row = target.iloc[0]
                    results.append({
                        "code": code,
                        "name": row.get("名称", ""),
                        "price": float(row.get("最新价", 0)),
                        "pct_change": float(row.get("涨跌幅", 0)),
                        "signals": triggered,
                    })
            except Exception:
                results.append({"code": code, "signals": triggered})
        except Exception:
            continue
    return results[:top_n]


def main():
    parser = argparse.ArgumentParser(description="signal-screener")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("screen", help="筛选")
    p.add_argument("--signal", help="单信号")
    p.add_argument("--signals", help="多信号, 逗号分隔")
    p.add_argument("--mode", default="and", choices=["and", "or"])
    p.add_argument("--top", type=int, default=30)
    args = parser.parse_args()

    if args.cmd == "screen":
        if args.signal:
            conditions = [args.signal]
        elif args.signals:
            conditions = [s.strip() for s in args.signals.split(",")]
        else:
            parser.print_help()
            return
        r = screen(conditions, mode=args.mode, top_n=args.top)
        print(f"\n=== 筛选结果 ({len(r)} 只) ===")
        for i, item in enumerate(r, 1):
            print(f"{i}. {item['code']} {item.get('name', '')} "
                  f"{item.get('price', 0):.2f} ({item.get('pct_change', 0):+.2f}%) "
                  f"[{', '.join(item['signals'])}]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
