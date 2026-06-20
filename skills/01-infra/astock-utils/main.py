#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""astock-utils: A股通用工具"""

import sys
import re
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Union


# ============================================================
# 代码处理
# ============================================================
def normalize_code(code: str) -> str:
    """规范化股票代码: 去除前缀, 补齐6位"""
    if not code:
        raise ValueError("股票代码不能为空")
    code = str(code).strip().lower()
    code = re.sub(r"^(sh|sz|bj)\.", "", code)
    code = re.sub(r"^(sh|sz|bj)", "", code)
    code = re.sub(r"\.s[h|z]+$", "", code)
    if not code.isdigit() or len(code) > 6:
        raise ValueError(f"无效的股票代码: {code}")
    return code.zfill(6)


def get_market(code: str) -> str:
    """判断市场: sh/sz/bj"""
    code = normalize_code(code)
    if code.startswith(("60", "68", "90")):
        return "sh"
    if code.startswith(("00", "30", "20")):
        return "sz"
    if code.startswith(("43", "83", "87", "88")):
        return "bj"
    return "sz"


def is_cyb(code: str) -> bool:
    """是否创业板 (30xxxx)"""
    return normalize_code(code).startswith("30")


def is_kcb(code: str) -> bool:
    """是否科创板 (688xxx)"""
    return normalize_code(code).startswith("688")


def is_bj(code: str) -> bool:
    """是否北交所"""
    code = normalize_code(code)
    return code.startswith(("43", "83", "87", "88"))


def is_st(name: str) -> bool:
    """是否ST股票"""
    if not name:
        return False
    return "ST" in str(name).upper() or "*ST" in str(name)


# ============================================================
# 日期工具
# ============================================================
def today_str(fmt: str = "%Y-%m-%d") -> str:
    return datetime.now().strftime(fmt)


def parse_date(s: str) -> datetime:
    """解析多种日期格式"""
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {s}")


def date_str(dt, fmt: str = "%Y-%m-%d") -> str:
    if isinstance(dt, str):
        return dt
    return dt.strftime(fmt)


def last_n_trade_days(n: int = 30, end: Optional[str] = None) -> List[str]:
    """最近N个交易日"""
    end = end or today_str()
    start = (parse_date(end) - timedelta(days=n * 2)).strftime("%Y-%m-%d")
    try:
        import akshare as ak
        df = ak.tool_trade_date_hist_sina()
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
        start_d = parse_date(start)
        end_d = parse_date(end)
        trades = df[(df["trade_date"] >= date_str(start_d)) & (df["trade_date"] <= date_str(end_d))]["trade_date"].tolist()
        return trades[-n:]
    except Exception:
        # 降级: 排除周末
        return pd.date_range(start, end, freq="B").strftime("%Y-%m-%d").tolist()[-n:]


# ============================================================
# 技术指标
# ============================================================
def add_ma(df: pd.DataFrame, periods: List[int] = None, col: str = "close") -> pd.DataFrame:
    if periods is None:
        periods = [5, 10, 20, 60]
    df = df.copy()
    for p in periods:
        df[f"MA{p}"] = df[col].rolling(p).mean()
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    df = df.copy()
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["DIF"] = ema_fast - ema_slow
    df["DEA"] = df["DIF"].ewm(span=signal, adjust=False).mean()
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2
    return df


def add_kdj(df: pd.DataFrame, n: int = 9, k_period: int = 3, d_period: int = 3) -> pd.DataFrame:
    df = df.copy()
    low_n = df["low"].rolling(n).min()
    high_n = df["high"].rolling(n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    df["K"] = rsv.ewm(alpha=1/k_period, adjust=False).mean()
    df["D"] = df["K"].ewm(alpha=1/d_period, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]
    return df


def add_rsi(df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
    if periods is None:
        periods = [6, 12, 24]
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    for p in periods:
        avg_gain = gain.rolling(p).mean()
        avg_loss = loss.rolling(p).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df[f"RSI{p}"] = 100 - (100 / (1 + rs))
    return df


def add_boll(df: pd.DataFrame, n: int = 20, k: float = 2) -> pd.DataFrame:
    df = df.copy()
    df["MID"] = df["close"].rolling(n).mean()
    std = df["close"].rolling(n).std()
    df["UPPER"] = df["MID"] + k * std
    df["LOWER"] = df["MID"] - k * std
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_ma(df)
    df = add_macd(df)
    df = add_kdj(df)
    df = add_rsi(df)
    df = add_boll(df)
    return df


# ============================================================
# 格式化
# ============================================================
def fmt_volume(vol) -> str:
    if vol is None or pd.isna(vol):
        return "-"
    vol = float(vol)
    if vol >= 1e8:
        return f"{vol/1e8:.2f}亿"
    if vol >= 1e4:
        return f"{vol/1e4:.2f}万"
    return f"{vol:.0f}"


def fmt_money(money) -> str:
    if money is None or pd.isna(money):
        return "-"
    money = float(money)
    if money >= 1e8:
        return f"{money/1e8:.2f}亿"
    if money >= 1e4:
        return f"{money/1e4:.2f}万"
    return f"{money:.0f}"


def fmt_pct(p) -> str:
    if p is None or pd.isna(p):
        return "-"
    return f"{float(p):.2f}%"


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="astock-utils")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("normalize-code")
    p.add_argument("code")
    p = sub.add_parser("market")
    p.add_argument("code")
    p = sub.add_parser("is-cyb")
    p.add_argument("code")
    p = sub.add_parser("is-kcb")
    p.add_argument("code")
    p = sub.add_parser("is-st")
    p.add_argument("name")
    p = sub.add_parser("today")
    p = sub.add_parser("trade-days")
    p.add_argument("n", type=int)
    p = sub.add_parser("fmt-volume")
    p.add_argument("v", type=float)
    p = sub.add_parser("fmt-money")
    p.add_argument("v", type=float)
    p = sub.add_parser("fmt-pct")
    p.add_argument("v", type=float)

    args = parser.parse_args()
    if args.cmd == "normalize-code":
        print(normalize_code(args.code))
    elif args.cmd == "market":
        print(get_market(args.code))
    elif args.cmd == "is-cyb":
        print(is_cyb(args.code))
    elif args.cmd == "is-kcb":
        print(is_kcb(args.code))
    elif args.cmd == "is-st":
        print(is_st(args.name))
    elif args.cmd == "today":
        print(today_str())
    elif args.cmd == "trade-days":
        print(last_n_trade_days(args.n))
    elif args.cmd == "fmt-volume":
        print(fmt_volume(args.v))
    elif args.cmd == "fmt-money":
        print(fmt_money(args.v))
    elif args.cmd == "fmt-pct":
        print(fmt_pct(args.v))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
