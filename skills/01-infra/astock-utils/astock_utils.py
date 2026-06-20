"""
astock-utils: A股通用工具函数
================================

功能:
    - 日期处理 (交易日历、日期转换)
    - 复权处理
    - 股票代码校验与转换
    - 常用技术指标 (MA/MACD/KDJ/RSI/BOLL)
    - 数据清洗
"""

import re
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Union, Tuple


# ============================================================
# 1. 股票代码工具
# ============================================================
def normalize_stock_code(code: str) -> str:
    """规范化股票代码: 去除前缀, 补齐6位
    Args:
        code: 600000 / sh600000 / 000001.SZ / sz000001
    Returns:
        6位代码, 如 600000
    """
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
    """根据代码判断市场
    Returns:
        'sh' / 'sz' / 'bj'
    """
    code = normalize_stock_code(code)
    if code.startswith(("60", "68", "90")):
        return "sh"
    if code.startswith(("00", "30", "20")):
        return "sz"
    if code.startswith(("43", "83", "87", "88")):
        return "bj"
    return "sz"


def is_cyb(code: str) -> bool:
    """是否创业板 (30xxxx)"""
    return normalize_stock_code(code).startswith("30")


def is_kcb(code: str) -> bool:
    """是否科创板 (688xxx)"""
    return normalize_stock_code(code).startswith("688")


def is_bj(code: str) -> bool:
    """是否北交所 (8xxxxx)"""
    code = normalize_stock_code(code)
    return code.startswith(("43", "83", "87", "88"))


# ============================================================
# 2. 日期工具
# ============================================================
def today_str(fmt: str = "%Y-%m-%d") -> str:
    return datetime.now().strftime(fmt)


def date_str(dt: Union[datetime, str], fmt: str = "%Y-%m-%d") -> str:
    if isinstance(dt, str):
        return dt
    return dt.strftime(fmt)


def parse_date(s: str) -> datetime:
    """解析多种日期格式"""
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {s}")


def get_trade_dates(start: str, end: str) -> List[str]:
    """获取区间内所有交易日 (基于akshare交易日历)"""
    try:
        import akshare as ak
        df = ak.tool_trade_date_hist_sina()
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
        start_d = parse_date(start)
        end_d = parse_date(end)
        return df[(df["trade_date"] >= date_str(start_d)) & (df["trade_date"] <= date_str(end_d))]["trade_date"].tolist()
    except Exception as e:
        # 降级: 排除周末
        dates = pd.date_range(start, end, freq="B").strftime("%Y-%m-%d").tolist()
        return dates


def last_n_trade_days(n: int = 30, end: Optional[str] = None) -> List[str]:
    """最近N个交易日"""
    end = end or today_str()
    start = (parse_date(end) - timedelta(days=n * 2)).strftime("%Y-%m-%d")
    trades = get_trade_dates(start, end)
    return trades[-n:]


# ============================================================
# 3. 技术指标计算
# ============================================================
def calc_ma(df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60], col: str = "close") -> pd.DataFrame:
    """计算移动平均线"""
    df = df.copy()
    for p in periods:
        df[f"MA{p}"] = df[col].rolling(p).mean()
    return df


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """计算MACD
    Returns:
        增加 DIF, DEA, MACD 列
    """
    df = df.copy()
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["DIF"] = ema_fast - ema_slow
    df["DEA"] = df["DIF"].ewm(span=signal, adjust=False).mean()
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2
    return df


def calc_kdj(df: pd.DataFrame, n: int = 9, k_period: int = 3, d_period: int = 3) -> pd.DataFrame:
    """KDJ指标"""
    df = df.copy()
    low_n = df["low"].rolling(n).min()
    high_n = df["high"].rolling(n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    df["K"] = rsv.ewm(alpha=1/k_period, adjust=False).mean()
    df["D"] = df["K"].ewm(alpha=1/d_period, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]
    return df


def calc_rsi(df: pd.DataFrame, periods: List[int] = [6, 12, 24]) -> pd.DataFrame:
    """RSI指标"""
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


def calc_boll(df: pd.DataFrame, n: int = 20, k: float = 2) -> pd.DataFrame:
    """布林带"""
    df = df.copy()
    df["MID"] = df["close"].rolling(n).mean()
    std = df["close"].rolling(n).std()
    df["UPPER"] = df["MID"] + k * std
    df["LOWER"] = df["MID"] - k * std
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """一次性添加所有常用指标"""
    df = calc_ma(df)
    df = calc_macd(df)
    df = calc_kdj(df)
    df = calc_rsi(df)
    df = calc_boll(df)
    return df


# ============================================================
# 4. 复权与涨跌停
# ============================================================
def is_limit_up(price: float, prev_close: float, market: str = "sz") -> bool:
    """判断是否涨停
    A股规则:
        - 普通: 主板 ±10%
        - 创业板/科创板/北交所: ±20%
        - ST: ±5%
    """
    if prev_close <= 0:
        return False
    ratio = (price - prev_close) / prev_close
    code = ""  # 调用方应传code
    # 简化处理
    if ratio >= 0.099:
        return True
    return False


def pct_change(curr: float, prev: float) -> float:
    """涨跌幅 (%)"""
    if prev == 0:
        return 0.0
    return (curr - prev) / prev * 100


# ============================================================
# 5. 数据清洗
# ============================================================
def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """清洗K线数据"""
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    required = ["open", "high", "low", "close"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"缺少字段: {col}")
    if "volume" not in df.columns:
        df["volume"] = 0
    if "date" not in df.columns and "日期" in df.columns:
        df["date"] = df["日期"]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=required)
    df = df.sort_values("date" if "date" in df.columns else df.index.name or "date").reset_index(drop=True)
    return df


# ============================================================
# 6. 格式化输出
# ============================================================
def fmt_volume(vol) -> str:
    """格式化成交量"""
    if vol is None or pd.isna(vol):
        return "-"
    vol = float(vol)
    if vol >= 1e8:
        return f"{vol/1e8:.2f}亿"
    if vol >= 1e4:
        return f"{vol/1e4:.2f}万"
    return f"{vol:.0f}"


def fmt_money(money) -> str:
    """格式化金额"""
    if money is None or pd.isna(money):
        return "-"
    money = float(money)
    if money >= 1e8:
        return f"{money/1e8:.2f}亿"
    if money >= 1e4:
        return f"{money/1e4:.2f}万"
    return f"{money:.0f}"


def fmt_pct(p) -> str:
    """格式化百分比"""
    if p is None or pd.isna(p):
        return "-"
    return f"{float(p):.2f}%"


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    # 测试代码转换
    print("=== 代码测试 ===")
    for c in ["600000", "sh600000", "000001.SZ", "sz000001", "300750"]:
        print(f"  {c} -> {normalize_stock_code(c)}, market={get_market(c)}, 创业板={is_cyb(c)}")

    # 测试日期
    print("\n=== 日期测试 ===")
    print(f"  最近5个交易日: {last_n_trade_days(5)}")

    # 测试技术指标
    print("\n=== 技术指标测试 ===")
    np.random.seed(42)
    test_df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100),
        "open": np.random.randn(100).cumsum() + 10,
        "high": np.random.randn(100).cumsum() + 11,
        "low": np.random.randn(100).cumsum() + 9,
        "close": np.random.randn(100).cumsum() + 10,
        "volume": np.random.randint(1000, 10000, 100),
    })
    test_df = clean_ohlcv(test_df)
    test_df = add_all_indicators(test_df)
    print(test_df.tail(3))
