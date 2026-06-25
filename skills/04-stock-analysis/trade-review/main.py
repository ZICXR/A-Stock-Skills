#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trade-review: 交割单操作分析诊断

从券商交割单出发，全面分析交易操作问题并给出改进建议。
支持多种券商格式（CSV/Excel），自动识别列名。

5 维诊断: 盈亏统计 / 持仓周期 / 操作行为 / 仓位管理 / 买卖时机
"""

import os
import re
import sys
import json
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd

warnings.filterwarnings("ignore")

# 复用 astock-utils (importlib 因为目录名含连字符)
import importlib.util

def _import_sibling(rel_path: str, attr: str = None):
    """动态导入兄弟 skill 模块 (目录含连字符，无法直接 import)"""
    base = Path(__file__).resolve().parents[2]
    mod_path = base / (rel_path.replace(".", "/") + ".py")
    if not mod_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("_sibling", mod_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    if attr:
        return getattr(mod, attr, None)
    return mod

_utils = _import_sibling("skills/01-infra/astock-utils/main")
if _utils:
    normalize_code = getattr(_utils, "normalize_code", None)
    parse_date = getattr(_utils, "parse_date", None)
if "normalize_code" not in dir() or normalize_code is None:
    def normalize_code(code: str) -> str:
        code = str(code).strip().lower()
        code = re.sub(r"^(sh|sz|bj)\.?", "", code)
        return code.zfill(6)
if "parse_date" not in dir() or parse_date is None:
    def parse_date(s: str) -> datetime:
        s = str(s).strip()
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValueError(f"无法解析日期: {s}")


# ============================================================
# 标准字段定义
# ============================================================
STANDARD_FIELDS = {
    "date":      {"label": "成交日期", "keywords": ["成交日期", "交易日期", "日期", "odate", "trade_date", "date"]},
    "code":      {"label": "证券代码", "keywords": ["证券代码", "股票代码", "代码", "scode", "stock_code", "code"]},
    "name":      {"label": "证券名称", "keywords": ["证券名称", "股票名称", "名称", "sname", "stock_name", "name"]},
    "direction": {"label": "买卖方向", "keywords": ["买卖方向", "操作", "方向", "类型", "direction", "buy_sell", "bs_flag"]},
    "price":     {"label": "成交价格", "keywords": ["成交价格", "成交价", "均价", "价格", "price", "deal_price"]},
    "quantity":  {"label": "成交数量", "keywords": ["成交数量", "数量", "成交量", "quantity", "volume", "qty"]},
    "amount":    {"label": "成交金额", "keywords": ["成交金额", "金额", "amount", "turnover"]},
    "fee":       {"label": "佣金手续费", "keywords": ["佣金", "手续费", "费用", "commission", "fee", "cost"]},
    "tax":       {"label": "印花税",   "keywords": ["印花税", "税费", "stamp_tax", "tax"]},
}


# ============================================================
# 交割单解析
# ============================================================
def detect_format(columns: List[str]) -> str:
    """识别券商交割单格式"""
    cols_lower = [str(c).lower().strip() for c in columns]
    cols_str = " ".join(str(c) for c in columns)

    # 华泰证券特征
    if any("成交日期" in c for c in cols_str.split(",")) or \
       any("股东代码" in c for c in cols_str.split(",")):
        return "huatai"

    # 东方财富
    if any("配" in c for c in cols_str) and any("代码" in c for c in cols_str):
        return "eastmoney"

    # 英文格式
    if all(c.isascii() for c in columns if c.strip()):
        return "english"

    return "generic"


def map_columns(df_columns: List[str]) -> Dict[str, str]:
    """将交割单列名映射到标准字段

    Returns: {标准字段名: 原始列名}
    """
    mapping = {}
    used = set()

    for std_field, info in STANDARD_FIELDS.items():
        best_match = None
        best_score = 0

        for col in df_columns:
            if col in used:
                continue
            col_str = str(col).strip()

            for kw in info["keywords"]:
                if kw == col_str:
                    score = 100  # 精确匹配
                elif kw in col_str or col_str in kw:
                    score = 80  # 包含匹配
                elif any(c in col_str for c in kw):
                    score = 50  # 字符重叠
                else:
                    score = 0

                if score > best_score:
                    best_score = score
                    best_match = col

        if best_match and best_score >= 50:
            mapping[std_field] = best_match
            used.add(best_match)

    return mapping


def normalize_direction(val: str) -> str:
    """统一买卖方向: 'buy' / 'sell'"""
    val = str(val).strip().lower()
    if val in ("买", "买入", "证券买入", "buy", "b", "1"):
        return "buy"
    if val in ("卖", "卖出", "证券卖出", "sell", "s", "2"):
        return "sell"
    return val


def parse_settlement(path: str, encoding: str = None) -> pd.DataFrame:
    """解析交割单文件

    Args:
        path: 文件路径 (CSV 或 Excel)
        encoding: 文件编码，默认自动检测

    Returns:
        标准字段 DataFrame (date/code/name/direction/price/quantity/amount/fee/tax)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    # 读取文件
    ext = path.suffix.lower()
    if ext in (".xls", ".xlsx"):
        try:
            df = pd.read_excel(path, dtype=str)
        except Exception:
            df = pd.read_excel(path, dtype=str, engine="openpyxl")
    elif ext == ".csv":
        # 尝试多种编码
        for enc in [encoding, "utf-8", "gbk", "gb2312", "gb18030", "utf-8-sig"]:
            if enc is None:
                continue
            try:
                df = pd.read_csv(path, dtype=str, encoding=enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            raise ValueError("无法识别文件编码，请用 --encoding 参数指定")
    else:
        raise ValueError(f"不支持的文件格式: {ext}，支持 .csv / .xls / .xlsx")

    if df.empty:
        raise ValueError("文件为空")

    # 跳过标题行（有些交割单前几行是说明文字）
    # 检测实际数据行
    for i in range(min(10, len(df))):
        row_vals = [str(v).strip() for v in df.iloc[i].values]
        # 找到包含日期或代码的行
        if any(re.match(r"\d{6}", v) for v in row_vals) or \
           any(re.match(r"\d{4}[-/]", v) for v in row_vals):
            if i > 0:
                df.columns = df.iloc[i - 1].values
                df = df.iloc[i:]
            break

    df = df.dropna(how="all").reset_index(drop=True)

    # 映射列名
    col_mapping = map_columns(list(df.columns))
    if "date" not in col_mapping or "code" not in col_mapping:
        print(f"当前列名: {list(df.columns)}")
        print(f"映射结果: {col_mapping}")
        raise ValueError(
            "无法识别交割单格式。请确认文件包含 '日期' 和 '代码' 列。\n"
            "支持格式: 华泰/中信/国泰君安/招商/东方财富/通用 CSV"
        )

    # 重命名列
    rename_map = {v: k for k, v in col_mapping.items()}
    df = df.rename(columns=rename_map)

    # 只保留标准字段
    keep_cols = [c for c in STANDARD_FIELDS.keys() if c in df.columns]
    df = df[keep_cols].copy()

    # 数据类型转换
    if "date" in df.columns:
        df["date"] = df["date"].astype(str).apply(_parse_date_flexible)
    if "code" in df.columns:
        df["code"] = df["code"].astype(str).apply(normalize_code)
    if "direction" in df.columns:
        df["direction"] = df["direction"].apply(normalize_direction)
    for col in ("price", "quantity", "amount", "fee", "tax"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(),
                                    errors="coerce").fillna(0)

    # 补算缺失字段
    if "amount" not in df.columns and "price" in df.columns and "quantity" in df.columns:
        df["amount"] = df["price"] * df["quantity"]
    if "fee" not in df.columns:
        df["fee"] = 0
    if "tax" not in df.columns:
        df["tax"] = 0

    # 过滤掉非交易记录（如分红、配股、利息等）
    if "direction" in df.columns:
        df = df[df["direction"].isin(["buy", "sell"])].copy()

    df = df.sort_values("date").reset_index(drop=True)
    return df


def _parse_date_flexible(val: str) -> Optional[datetime]:
    """灵活解析多种日期格式"""
    val = str(val).strip()
    for fmt in (
        "%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y.%m.%d",
        "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
        "%Y%m%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    # 尝试 pandas 兜底
    try:
        return pd.to_datetime(val)
    except Exception:
        return None


# ============================================================
# 交易配对 (FIFO)
# ============================================================
def pair_trades(df: pd.DataFrame) -> pd.DataFrame:
    """将买卖记录 FIFO 配对为完整交易轮次

    Returns:
        DataFrame: code, name, buy_date, sell_date, buy_price, sell_price,
                   quantity, amount_buy, amount_sell, fee_total, pnl, pnl_pct, hold_days
    """
    if df.empty or "direction" not in df.columns:
        return pd.DataFrame()

    trades = []
    # 按股票代码分组
    for code, group in df.groupby("code"):
        group = group.sort_values("date")
        buy_queue = []  # FIFO 队列: [(date, price, quantity, name, fee)]

        for _, row in group.iterrows():
            direction = row["direction"]
            qty = int(row.get("quantity", 0))
            price = float(row.get("price", 0))
            date = row.get("date")
            name = row.get("name", "")
            fee = float(row.get("fee", 0)) + float(row.get("tax", 0))

            if direction == "buy":
                buy_queue.append({
                    "date": date, "price": price, "quantity": qty,
                    "name": name, "fee": fee,
                })
            elif direction == "sell":
                remaining = qty
                sell_fee = fee
                while remaining > 0 and buy_queue:
                    buy = buy_queue[0]
                    match_qty = min(remaining, buy["quantity"])

                    buy_cost = buy["price"] * match_qty
                    sell_income = price * match_qty
                    total_fee = (buy["fee"] * match_qty / buy["quantity"]) + \
                                (sell_fee * match_qty / remaining) if remaining > 0 else 0
                    # 简化费用分摊
                    total_fee = buy["fee"] * match_qty / buy["quantity"] + sell_fee * match_qty / qty
                    pnl = sell_income - buy_cost - total_fee
                    pnl_pct = (price - buy["price"]) / buy["price"] * 100 if buy["price"] > 0 else 0

                    # 持仓天数
                    hold_days = 0
                    if buy["date"] and date:
                        try:
                            hold_days = (pd.to_datetime(date) - pd.to_datetime(buy["date"])).days
                        except Exception:
                            pass

                    trades.append({
                        "code": code,
                        "name": buy["name"] or name,
                        "buy_date": buy["date"],
                        "sell_date": date,
                        "buy_price": buy["price"],
                        "sell_price": price,
                        "quantity": match_qty,
                        "amount_buy": buy_cost,
                        "amount_sell": sell_income,
                        "fee_total": total_fee,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "hold_days": hold_days,
                    })

                    remaining -= match_qty
                    buy["quantity"] -= match_qty
                    if buy["quantity"] <= 0:
                        buy_queue.pop(0)

    result = pd.DataFrame(trades)
    if not result.empty:
        result = result.sort_values("sell_date").reset_index(drop=True)
    return result


# ============================================================
# 5 维分析
# ============================================================
def analyze_pnl(trades: pd.DataFrame) -> Dict:
    """维度 1: 盈亏统计"""
    if trades.empty:
        return {"total_pnl": 0, "win_rate": 0, "profit_loss_ratio": 0}

    total_pnl = trades["pnl"].sum()
    total_cost = trades["amount_buy"].sum()
    total_return = total_pnl / total_cost * 100 if total_cost > 0 else 0

    win_trades = trades[trades["pnl"] > 0]
    lose_trades = trades[trades["pnl"] < 0]
    even_trades = trades[trades["pnl"] == 0]

    win_count = len(win_trades)
    lose_count = len(lose_trades)
    total_count = len(trades)
    win_rate = win_count / total_count * 100 if total_count > 0 else 0

    avg_win = win_trades["pnl_pct"].mean() if not win_trades.empty else 0
    avg_lose = abs(lose_trades["pnl_pct"].mean()) if not lose_trades.empty else 0
    profit_loss_ratio = avg_win / avg_lose if avg_lose > 0 else (10 if avg_win > 0 else 0)

    max_win = trades.loc[trades["pnl"].idxmax()] if not trades.empty else None
    max_lose = trades.loc[trades["pnl"].idxmin()] if not trades.empty else None

    # 收益分布
    bins = [(-100, -20), (-20, -10), (-10, -5), (-5, 0), (0, 5), (5, 10), (10, 20), (20, 100)]
    distribution = []
    for lo, hi in bins:
        count = len(trades[(trades["pnl_pct"] >= lo) & (trades["pnl_pct"] < hi)])
        distribution.append({"range": f"{lo}%~{hi}%", "count": count})

    return {
        "total_pnl": total_pnl,
        "total_return": total_return,
        "win_count": win_count,
        "lose_count": lose_count,
        "even_count": len(even_trades),
        "total_count": total_count,
        "win_rate": win_rate,
        "avg_win_pct": avg_win,
        "avg_lose_pct": avg_lose,
        "profit_loss_ratio": profit_loss_ratio,
        "max_win": {
            "code": max_win["code"], "name": max_win["name"],
            "pnl": max_win["pnl"], "pnl_pct": max_win["pnl_pct"],
        } if max_win is not None else None,
        "max_lose": {
            "code": max_lose["code"], "name": max_lose["name"],
            "pnl": max_lose["pnl"], "pnl_pct": max_lose["pnl_pct"],
        } if max_lose is not None else None,
        "distribution": distribution,
    }


def analyze_holding_period(trades: pd.DataFrame) -> Dict:
    """维度 2: 持仓周期分析"""
    if trades.empty:
        return {"avg_days": 0}

    avg_days = trades["hold_days"].mean()
    min_days = int(trades["hold_days"].min())
    max_days = int(trades["hold_days"].max())
    median_days = trades["hold_days"].median()

    win_trades = trades[trades["pnl"] > 0]
    lose_trades = trades[trades["pnl"] < 0]

    avg_hold_win = win_trades["hold_days"].mean() if not win_trades.empty else 0
    avg_hold_lose = lose_trades["hold_days"].mean() if not lose_trades.empty else 0

    # 日内交易（T+0 嫌疑，持仓 0 天）
    day_trades = len(trades[trades["hold_days"] == 0])

    # 超短线（1-3天）
    ultra_short = len(trades[(trades["hold_days"] >= 1) & (trades["hold_days"] <= 3)])

    # 短线（4-20天）
    short_term = len(trades[(trades["hold_days"] >= 4) & (trades["hold_days"] <= 20)])

    # 中线（21-60天）
    mid_term = len(trades[(trades["hold_days"] >= 21) & (trades["hold_days"] <= 60)])

    # 长线（>60天）
    long_term = len(trades[trades["hold_days"] > 60])

    return {
        "avg_days": avg_days,
        "median_days": median_days,
        "min_days": min_days,
        "max_days": max_days,
        "avg_hold_win": avg_hold_win,
        "avg_hold_lose": avg_hold_lose,
        "day_trades": day_trades,
        "ultra_short": ultra_short,
        "short_term": short_term,
        "mid_term": mid_term,
        "long_term": long_term,
    }


def analyze_behavior(trades: pd.DataFrame) -> Dict:
    """维度 3: 操作行为诊断"""
    if trades.empty:
        return {}

    issues = []

    # 1. 坐电梯: 曾盈利但最终亏损
    elevator_count = 0
    elevator_cases = []
    for _, t in trades.iterrows():
        if t["pnl"] < 0 and t["pnl_pct"] < -2:
            # 检查是否曾盈利（简单判断：如果买卖价差为正但加上费用后亏损）
            price_diff = t["sell_price"] - t["buy_price"]
            if price_diff > 0 and t["pnl"] < 0:
                elevator_count += 1
                elevator_cases.append({
                    "code": t["code"], "name": t["name"],
                    "buy_price": t["buy_price"], "sell_price": t["sell_price"],
                    "pnl": t["pnl"],
                })

    # 2. 不止损: 大亏 (>20%)
    no_stoploss = trades[trades["pnl_pct"] < -20]
    no_stoploss_cases = []
    for _, t in no_stoploss.iterrows():
        no_stoploss_cases.append({
            "code": t["code"], "name": t["name"],
            "pnl_pct": t["pnl_pct"], "pnl": t["pnl"],
        })

    # 3. 频繁交易: 同一股票交易次数
    trade_freq = trades.groupby("code").size().reset_index(name="count")
    frequent_stocks = trade_freq[trade_freq["count"] >= 5]

    # 4. 追涨杀跌: 亏损卖出占比
    panic_sell = trades[(trades["pnl"] < 0) & (trades["hold_days"] <= 3)]

    # 5. 赚小亏大
    win_avg = trades[trades["pnl"] > 0]["pnl"].mean() if (trades["pnl"] > 0).any() else 0
    lose_avg = abs(trades[trades["pnl"] < 0]["pnl"].mean()) if (trades["pnl"] < 0).any() else 0

    # 6. 分散度
    unique_stocks = trades["code"].nunique()

    # 7. 同一股票反复亏
    code_pnl = trades.groupby("code")["pnl"].sum()
    repeat_losers = code_pnl[code_pnl < -1000].sort_values()

    return {
        "elevator_count": elevator_count,
        "elevator_cases": elevator_cases[:5],
        "no_stoploss_count": len(no_stoploss_cases),
        "no_stoploss_cases": no_stoploss_cases[:5],
        "frequent_stocks": frequent_stocks.to_dict("records") if not frequent_stocks.empty else [],
        "panic_sell_count": len(panic_sell),
        "win_avg": win_avg,
        "lose_avg": lose_avg,
        "earn_small_lose_big": win_avg > 0 and lose_avg > win_avg,
        "unique_stocks": unique_stocks,
        "repeat_losers": [{"code": k, "total_pnl": v} for k, v in repeat_losers.items()][:5],
    }


def analyze_position(trades: pd.DataFrame) -> Dict:
    """维度 4: 仓位管理"""
    if trades.empty:
        return {}

    # 按交易金额分析集中度
    total_amount = trades["amount_buy"].sum()
    code_amount = trades.groupby("code")["amount_buy"].sum()
    max_stock = code_amount.idxmax() if not code_amount.empty else ""
    max_amount = code_amount.max() if not code_amount.empty else 0
    max_pct = max_amount / total_amount * 100 if total_amount > 0 else 0

    # 平均单笔金额
    avg_trade_amount = trades["amount_buy"].mean()

    # 最大单笔占比
    max_single = trades["amount_buy"].max()
    max_single_pct = max_single / total_amount * 100 if total_amount > 0 else 0

    # 加仓分析: 同一天同一股票多次买入
    if "buy_date" in trades.columns:
        daily_buys = trades.groupby(["code", "buy_date"]).size()
        add_positions = daily_buys[daily_buys > 1]
    else:
        add_positions = pd.Series(dtype=int)

    # 持仓只数分布
    unique_per_period = trades["code"].nunique()

    # 估算同时持仓数（按日期窗口）
    daily_activity = defaultdict(set)
    for _, t in trades.iterrows():
        if t.get("buy_date"):
            try:
                bd = pd.to_datetime(t["buy_date"])
                sd = pd.to_datetime(t.get("sell_date", t["buy_date"]))
                for d in pd.date_range(bd, sd, freq="D"):
                    daily_activity[d.strftime("%Y-%m-%d")].add(t["code"])
            except Exception:
                pass

    if daily_activity:
        avg_concurrent = sum(len(v) for v in daily_activity.values()) / len(daily_activity)
        max_concurrent = max(len(v) for v in daily_activity.values())
    else:
        avg_concurrent = 0
        max_concurrent = 0

    return {
        "total_amount": total_amount,
        "max_stock_code": max_stock,
        "max_stock_pct": max_pct,
        "max_single_pct": max_single_pct,
        "avg_trade_amount": avg_trade_amount,
        "unique_stocks": unique_per_period,
        "avg_concurrent": avg_concurrent,
        "max_concurrent": max_concurrent,
        "add_position_count": len(add_positions),
    }


def analyze_timing(trades: pd.DataFrame, fetch_kline: bool = False) -> Dict:
    """维度 5: 买卖时机分析

    如果 fetch_kline=True，拉取行情数据判断买卖点位置
    """
    if trades.empty:
        return {}

    result = {
        "fetch_kline": fetch_kline,
        "trades_analyzed": 0,
        "buy_at_high": 0,     # 买入时接近阶段高点
        "sell_at_low": 0,     # 卖出时接近阶段低点
        "vs_market_win": 0,   # 跑赢大盘
        "vs_market_lose": 0,  # 跑输大盘
    }

    if not fetch_kline:
        return result

    # 尝试拉取行情
    ds_mod = _import_sibling("skills/01-infra/astock-data-source/main")
    if ds_mod is None:
        print("⚠️ 无法加载 astock-data-source，跳过行情分析")
        return result
    get_kline = getattr(ds_mod, "get_kline", None)
    if get_kline is None:
        print("⚠️ 无法加载 astock-data-source，跳过行情分析")
        return result

    # 获取沪深300基准
    benchmark_return = 0
    try:
        import akshare as ak
        if not trades.empty and "buy_date" in trades.columns:
            first_date = trades["buy_date"].min()
            last_date = trades["sell_date"].max()
            if first_date and last_date:
                d1 = pd.to_datetime(first_date).strftime("%Y%m%d")
                d2 = pd.to_datetime(last_date).strftime("%Y%m%d")
                hs300 = ak.stock_zh_index_daily_em(symbol="sh000300")
                if not hs300.empty:
                    hs300["date"] = pd.to_datetime(hs300["date"])
                    start_price = hs300[hs300["date"] >= d1]["close"].iloc[0] if len(hs300[hs300["date"] >= d1]) > 0 else 0
                    end_price = hs300[hs300["date"] <= d2]["close"].iloc[-1] if len(hs300[hs300["date"] <= d2]) > 0 else 0
                    if start_price > 0:
                        benchmark_return = (end_price - start_price) / start_price * 100
    except Exception:
        pass

    result["benchmark_return"] = benchmark_return

    # 逐笔分析
    for _, t in trades.iterrows():
        code = t["code"]
        buy_date = t.get("buy_date")
        if not buy_date:
            continue

        try:
            start = (pd.to_datetime(buy_date) - timedelta(days=60)).strftime("%Y%m%d")
            end = (pd.to_datetime(buy_date) + timedelta(days=30)).strftime("%Y%m%d")
            kline = get_kline(code, days=90)
            if kline is None or kline.empty:
                continue

            result["trades_analyzed"] += 1
            kline.columns = [c.lower() for c in kline.columns]

            if "close" in kline.columns and len(kline) >= 20:
                buy_price = t["buy_price"]
                high_20 = kline["close"].tail(20).max()
                low_20 = kline["close"].tail(20).min()

                # 买入位置：接近 20 日高点 = 追高
                if high_20 > 0 and (buy_price / high_20) > 0.95:
                    result["buy_at_high"] += 1

                sell_price = t["sell_price"]
                # 卖出位置：接近 20 日低点 = 杀跌
                if low_20 > 0 and (sell_price / low_20) < 1.05:
                    result["sell_at_low"] += 1

            # 对比大盘
            if t["pnl_pct"] > benchmark_return:
                result["vs_market_win"] += 1
            else:
                result["vs_market_lose"] += 1

        except Exception:
            continue

    return result


# ============================================================
# AI 信号对比
# ============================================================
def compare_with_ai(trades: pd.DataFrame) -> Dict:
    """对比 trade-journal 中的 AI 建议 vs 实际操作"""
    journal_dir = Path("./journal")
    if not journal_dir.exists():
        return {"available": False, "message": "未找到 trade-journal 数据"}

    # 读取 journal 文件
    ai_signals = []
    for f in sorted(journal_dir.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            # 简单解析 AI 信号
            for line in content.split("\n"):
                if "代码:" in line and "AI 信号" not in line:
                    code_match = re.search(r"(\d{6})", line)
                    if code_match:
                        ai_signals.append({
                            "date": f.stem,
                            "code": code_match.group(1),
                            "line": line.strip(),
                        })
        except Exception:
            continue

    if not ai_signals:
        return {"available": False, "message": "trade-journal 中无 AI 信号记录"}

    # 对比
    match_count = 0
    mismatch_count = 0
    match_trades = []

    for _, t in trades.iterrows():
        for sig in ai_signals:
            if sig["code"] == t["code"] and sig["date"] == str(t.get("buy_date", ""))[:10]:
                match_count += 1
                match_trades.append({
                    "code": t["code"], "date": sig["date"],
                    "pnl": t["pnl"], "pnl_pct": t["pnl_pct"],
                })
                break

    # 统计听 AI vs 不听 AI
    follow_pnl = sum(m["pnl"] for m in match_trades)
    unfollow_pnl = trades["pnl"].sum() - follow_pnl

    return {
        "available": True,
        "total_signals": len(ai_signals),
        "matched": match_count,
        "mismatched": len(trades) - match_count,
        "follow_pnl": follow_pnl,
        "unfollow_pnl": unfollow_pnl,
    }


# ============================================================
# 建议生成
# ============================================================
def generate_suggestions(pnl: Dict, holding: Dict, behavior: Dict,
                         position: Dict, timing: Dict) -> List[Dict]:
    """基于分析结果生成改进建议

    Returns: [{priority, issue, suggestion, severity}]
    """
    suggestions = []

    # 1. 赚小亏大
    if pnl.get("profit_loss_ratio", 0) < 1:
        suggestions.append({
            "priority": 1,
            "severity": "critical",
            "issue": "赚小亏大",
            "detail": f"盈亏比 {pnl['profit_loss_ratio']:.1f}，平均盈利 +{pnl.get('avg_win_pct', 0):.1f}%，平均亏损 -{pnl.get('avg_lose_pct', 0):.1f}%",
            "suggestion": "设定止损线（如 -7%），让利润奔跑。盈利时不要急于止盈，亏损时果断止损。",
        })

    # 2. 胜率过低
    if pnl.get("win_rate", 0) < 40:
        suggestions.append({
            "priority": 2,
            "severity": "critical",
            "issue": "胜率过低",
            "detail": f"胜率 {pnl['win_rate']:.1f}%（{pnl.get('win_count', 0)}/{pnl.get('total_count', 0)}）",
            "suggestion": "减少出手次数，提高选股质量。宁可错过，不要做错。",
        })

    # 3. 不止损
    if behavior.get("no_stoploss_count", 0) > 0:
        suggestions.append({
            "priority": 3,
            "severity": "critical",
            "issue": "不止损",
            "detail": f"{behavior['no_stoploss_count']} 笔亏损超 20% 未止损",
            "suggestion": "严格执行止损纪律，建议 -7% 无条件止损。亏损 20% 需要翻倍才能回本。",
        })

    # 4. 坐电梯
    if behavior.get("elevator_count", 0) > 3:
        suggestions.append({
            "priority": 4,
            "severity": "high",
            "issue": "坐电梯",
            "detail": f"{behavior['elevator_count']} 次曾盈利但最终亏损卖出",
            "suggestion": "设定动态止盈：盈利 >5% 后，回撤 3% 则出场。保护已有利润。",
        })

    # 5. 频繁交易
    if holding.get("avg_days", 0) < 3 and holding.get("avg_days", 0) > 0:
        suggestions.append({
            "priority": 5,
            "severity": "high",
            "issue": "交易过于频繁",
            "detail": f"平均持仓 {holding['avg_days']:.1f} 天，手续费侵蚀利润",
            "suggestion": "降低交易频率，每周最多 1-2 笔。买入前多研究，减少冲动交易。",
        })

    # 6. 集中度过高
    if position.get("max_stock_pct", 0) > 50:
        suggestions.append({
            "priority": 6,
            "severity": "high",
            "issue": "仓位集中度过高",
            "detail": f"单股 {position['max_stock_code']} 占比 {position['max_stock_pct']:.1f}%",
            "suggestion": "分散到 3-5 只股票，单股仓位不超 30%。避免单点风险。",
        })

    # 7. 追涨
    if timing.get("buy_at_high", 0) > 0 and timing.get("trades_analyzed", 0) > 0:
        high_pct = timing["buy_at_high"] / timing["trades_analyzed"] * 100
        if high_pct > 50:
            suggestions.append({
                "priority": 7,
                "severity": "medium",
                "issue": "追涨买入",
                "detail": f"{high_pct:.0f}% 的买入接近阶段高点",
                "suggestion": "避免追高，尝试回调到均线支撑位附近再买入。",
            })

    # 8. 恐慌卖出
    if behavior.get("panic_sell_count", 0) > len(pnl.get("distribution", [])) * 0.3:
        suggestions.append({
            "priority": 8,
            "severity": "medium",
            "issue": "恐慌性卖出",
            "detail": f"{behavior['panic_sell_count']} 笔在 3 天内亏损卖出",
            "suggestion": "买入前做好计划，设定止损和止盈位。盘中不因情绪改变计划。",
        })

    # 9. 跑输大盘
    if timing.get("benchmark_return") is not None and pnl.get("total_return", 0) is not None:
        benchmark = timing.get("benchmark_return", 0)
        total_ret = pnl.get("total_return", 0)
        if total_ret < benchmark - 10:
            suggestions.append({
                "priority": 9,
                "severity": "medium",
                "issue": "跑输大盘",
                "detail": f"收益率 {total_ret:.1f}% vs 沪深300 {benchmark:.1f}%，跑输 {benchmark - total_ret:.1f}%",
                "suggestion": "考虑减少个股操作，配置部分指数基金（如沪深300ETF）。",
            })

    # 10. 反复亏同一只
    if behavior.get("repeat_losers"):
        suggestions.append({
            "priority": 10,
            "severity": "low",
            "issue": "反复亏损",
            "detail": f"有 {len(behavior['repeat_losers'])} 只股票反复亏损",
            "suggestion": "如果一只股票反复亏，说明你不适合它的风格，果断放弃。",
        })

    # 排序
    suggestions.sort(key=lambda x: x["priority"])

    # 无问题时的正向反馈
    if not suggestions:
        suggestions.append({
            "priority": 0,
            "severity": "good",
            "issue": "操作良好",
            "detail": "未发现明显问题",
            "suggestion": "继续保持当前的交易纪律！",
        })

    return suggestions


# ============================================================
# 报告生成
# ============================================================
def generate_report(result: Dict) -> str:
    """生成 Markdown 格式的诊断报告"""
    pnl = result.get("pnl", {})
    holding = result.get("holding", {})
    behavior = result.get("behavior", {})
    position = result.get("position", {})
    timing = result.get("timing", {})
    suggestions = result.get("suggestions", [])
    ai_compare = result.get("ai_compare", {})
    trades = result.get("trades", pd.DataFrame())
    date_range = result.get("date_range", "")

    md = f"# 📊 交割单操作诊断报告\n\n"
    md += f"**分析区间**: {date_range}\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

    # 1. 总览
    md += "## 💰 一、盈亏总览\n\n"
    total_pnl = pnl.get("total_pnl", 0)
    emoji = "📈" if total_pnl >= 0 else "📉"
    md += f"- {emoji} 总盈亏: **{total_pnl:+,.0f}** 元 ({pnl.get('total_return', 0):+.2f}%)\n"
    md += f"- 🎯 胜率: **{pnl.get('win_rate', 0):.1f}%** ({pnl.get('win_count', 0)}/{pnl.get('total_count', 0)})\n"
    md += f"- ⚖️ 盈亏比: **{pnl.get('profit_loss_ratio', 0):.1f}**\n"
    md += f"- 📊 平均盈利: +{pnl.get('avg_win_pct', 0):.1f}% / 平均亏损: -{pnl.get('avg_lose_pct', 0):.1f}%\n"

    if pnl.get("max_win"):
        mw = pnl["max_win"]
        md += f"- 🏆 最大盈利: {mw['code']} {mw['name']} {mw['pnl']:+,.0f} ({mw['pnl_pct']:+.1f}%)\n"
    if pnl.get("max_lose"):
        ml = pnl["max_lose"]
        md += f"- 💔 最大亏损: {ml['code']} {ml['name']} {ml['pnl']:+,.0f} ({ml['pnl_pct']:+.1f}%)\n"
    md += "\n"

    # 收益分布
    dist = pnl.get("distribution", [])
    if dist:
        md += "**收益分布**:\n\n"
        for d in dist:
            bar = "█" * min(d["count"], 20)
            md += f"- {d['range']:>10s}: {bar} {d['count']}笔\n"
        md += "\n"

    # 2. 持仓周期
    md += "## ⏱️ 二、持仓周期\n\n"
    md += f"- 平均持仓: **{holding.get('avg_days', 0):.1f}** 天\n"
    md += f"- 中位数: {holding.get('median_days', 0):.0f} 天\n"
    md += f"- 盈利平均持仓: {holding.get('avg_hold_win', 0):.1f} 天\n"
    md += f"- 亏损平均持仓: {holding.get('avg_hold_lose', 0):.1f} 天\n\n"

    md += "**持仓风格**:\n\n"
    md += f"- 日内: {holding.get('day_trades', 0)} 笔\n"
    md += f"- 超短线 (1-3天): {holding.get('ultra_short', 0)} 笔\n"
    md += f"- 短线 (4-20天): {holding.get('short_term', 0)} 笔\n"
    md += f"- 中线 (21-60天): {holding.get('mid_term', 0)} 笔\n"
    md += f"- 长线 (>60天): {holding.get('long_term', 0)} 笔\n\n"

    # 3. 操作问题诊断
    md += "## 🔍 三、操作问题诊断\n\n"

    diag_count = 0
    if behavior.get("earn_small_lose_big"):
        diag_count += 1
        md += f"### ❌ {diag_count}. 赚小亏大\n\n"
        md += f"- 平均盈利 {behavior.get('win_avg', 0):+,.0f} 元 vs 平均亏损 {behavior.get('lose_avg', 0):,.0f} 元\n"
        md += f"- 盈亏比 < 1，说明每笔赚的比亏的少\n\n"

    if behavior.get("elevator_count", 0) > 0:
        diag_count += 1
        md += f"### ❌ {diag_count}. 坐电梯 ({behavior['elevator_count']} 次)\n\n"
        md += "曾盈利但最终亏损的交易:\n\n"
        md += "| 代码 | 名称 | 买入价 | 卖出价 | 盈亏 |\n"
        md += "|------|------|--------|--------|------|\n"
        for c in behavior.get("elevator_cases", []):
            md += f"| {c['code']} | {c['name']} | {c['buy_price']:.2f} | {c['sell_price']:.2f} | {c['pnl']:+,.0f} |\n"
        md += "\n"

    if behavior.get("no_stoploss_count", 0) > 0:
        diag_count += 1
        md += f"### ❌ {diag_count}. 不止损 ({behavior['no_stoploss_count']} 笔)\n\n"
        md += "亏损超 20% 的交易:\n\n"
        md += "| 代码 | 名称 | 亏损比例 | 亏损金额 |\n"
        md += "|------|------|----------|----------|\n"
        for c in behavior.get("no_stoploss_cases", []):
            md += f"| {c['code']} | {c['name']} | {c['pnl_pct']:.1f}% | {c['pnl']:+,.0f} |\n"
        md += "\n"

    if behavior.get("frequent_stocks"):
        diag_count += 1
        md += f"### ⚠️ {diag_count}. 频繁交易同一股票\n\n"
        for s in behavior["frequent_stocks"][:5]:
            md += f"- {s['code']}: {s['count']} 次\n"
        md += "\n"

    if behavior.get("panic_sell_count", 0) > 0:
        diag_count += 1
        md += f"### ⚠️ {diag_count}. 恐慌性卖出\n\n"
        md += f"- {behavior['panic_sell_count']} 笔在 3 天内亏损卖出\n\n"

    if diag_count == 0:
        md += "✅ 未发现明显操作问题\n\n"

    # 4. 仓位管理
    md += "## 📦 四、仓位管理\n\n"
    md += f"- 总成交金额: {position.get('total_amount', 0):,.0f} 元\n"
    md += f"- 交易股票数: {position.get('unique_stocks', 0)} 只\n"
    md += f"- 平均同时持仓: {position.get('avg_concurrent', 0):.1f} 只\n"
    md += f"- 最大单股占比: {position.get('max_stock_pct', 0):.1f}%\n"
    if position.get("max_stock_code"):
        md += f"  - ({position['max_stock_code']})\n"
    md += f"- 最大单笔占比: {position.get('max_single_pct', 0):.1f}%\n\n"

    # 5. 买卖时机
    if timing.get("fetch_kline"):
        md += "## 🎯 五、买卖时机\n\n"
        md += f"- 分析笔数: {timing.get('trades_analyzed', 0)}\n"
        md += f"- 追高买入: {timing.get('buy_at_high', 0)} 笔\n"
        md += f"- 杀跌卖出: {timing.get('sell_at_low', 0)} 笔\n"
        bm = timing.get("benchmark_return")
        if bm is not None:
            md += f"- 同期沪深300: {bm:+.1f}%\n"
            md += f"- 跑赢大盘: {timing.get('vs_market_win', 0)} 笔\n"
            md += f"- 跑输大盘: {timing.get('vs_market_lose', 0)} 笔\n"
        md += "\n"

    # 6. AI 信号对比
    if ai_compare.get("available"):
        md += "## 🤖 六、AI 信号对比\n\n"
        md += f"- AI 信号总数: {ai_compare.get('total_signals', 0)}\n"
        md += f"- 与实际操作匹配: {ai_compare.get('matched', 0)} 笔\n"
        follow = ai_compare.get("follow_pnl", 0)
        unfollow = ai_compare.get("unfollow_pnl", 0)
        md += f"- 听 AI 的盈亏: {follow:+,.0f} 元\n"
        md += f"- 不听 AI 的盈亏: {unfollow:+,.0f} 元\n\n"

    # 7. 改进建议
    md += "## 💡 改进建议\n\n"
    severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "good": "✅"}
    for s in suggestions:
        sev = severity_emoji.get(s.get("severity", ""), "⚪")
        md += f"### {sev} {s['issue']}\n\n"
        if s.get("detail"):
            md += f"**问题**: {s['detail']}\n\n"
        md += f"**建议**: {s['suggestion']}\n\n"

    md += "---\n\n"
    md += "⚠️ 本报告由 A-Stock-Skills 自动生成，仅供学习研究，不构成投资建议。\n"

    return md


# ============================================================
# 全流程分析
# ============================================================
def analyze_trades(df_or_path, fetch_kline: bool = False,
                   date_from: str = None, date_to: str = None) -> Dict:
    """一键全流程分析

    Args:
        df_or_path: DataFrame 或文件路径
        fetch_kline: 是否拉取行情分析买卖点
        date_from: 起始日期
        date_to: 截止日期

    Returns:
        完整分析结果字典
    """
    # 解析
    if isinstance(df_or_path, (str, Path)):
        df = parse_settlement(str(df_or_path))
    else:
        df = df_or_path.copy()

    # 日期过滤
    if date_from or date_to:
        if "date" in df.columns:
            if date_from:
                df = df[df["date"] >= pd.to_datetime(date_from)]
            if date_to:
                df = df[df["date"] <= pd.to_datetime(date_to)]

    if df.empty:
        return {"error": "无交易记录"}

    # 日期范围
    date_range = ""
    if "date" in df.columns and not df.empty:
        min_date = df["date"].min()
        max_date = df["date"].max()
        date_range = f"{min_date} ~ {max_date}"

    # 配对
    trades = pair_trades(df)
    if trades.empty:
        return {"error": "无法配对交易，请检查交割单是否包含完整的买卖记录"}

    # 5 维分析
    pnl = analyze_pnl(trades)
    holding = analyze_holding_period(trades)
    behavior = analyze_behavior(trades)
    position = analyze_position(trades)
    timing = analyze_timing(trades, fetch_kline=fetch_kline)

    # AI 对比
    ai_compare = compare_with_ai(trades)

    # 建议
    suggestions = generate_suggestions(pnl, holding, behavior, position, timing)

    return {
        "date_range": date_range,
        "raw_records": len(df),
        "paired_trades": len(trades),
        "trades": trades,
        "pnl": pnl,
        "holding": holding,
        "behavior": behavior,
        "position": position,
        "timing": timing,
        "ai_compare": ai_compare,
        "suggestions": suggestions,
    }


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="trade-review - 交割单操作分析诊断",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py analyze settlement.csv
  python main.py analyze settlement.csv --from 2025-01-01 --to 2025-06-30
  python main.py analyze settlement.csv --kline --save
  python main.py fields
        """,
    )
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("analyze", help="分析交割单")
    p.add_argument("file", help="交割单文件路径 (CSV/Excel)")
    p.add_argument("--from", dest="date_from", help="起始日期 (YYYY-MM-DD)")
    p.add_argument("--to", dest="date_to", help="截止日期 (YYYY-MM-DD)")
    p.add_argument("--kline", action="store_true", help="结合行情分析买卖点（较慢）")
    p.add_argument("--save", action="store_true", help="保存报告到文件")
    p.add_argument("--encoding", help="文件编码 (默认自动检测)")

    sub.add_parser("fields", help="查看标准字段说明")

    args = parser.parse_args()

    if args.cmd == "fields":
        print("标准字段说明:\n")
        for field, info in STANDARD_FIELDS.items():
            print(f"  {field:12s} - {info['label']}")
            print(f"  {'':12s}   识别: {', '.join(info['keywords'][:4])}")
        return

    if args.cmd == "analyze":
        print(f"📊 正在分析: {args.file}")
        print("=" * 60)

        try:
            result = analyze_trades(
                args.file,
                fetch_kline=args.kline,
                date_from=args.date_from,
                date_to=args.date_to,
            )
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return

        if "error" in result:
            print(f"❌ {result['error']}")
            return

        # 生成报告
        report = generate_report(result)
        print(report)

        if args.save:
            path = f"trade_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n📄 报告已保存: {path}")

        return

    parser.print_help()


if __name__ == "__main__":
    main()
