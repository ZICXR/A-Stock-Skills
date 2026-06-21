#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""screener: 股票筛选器 (内置 + 自定义 2合1)

合并: signal-screener + stock-screener-custom
"""

import os
import sys
import json
import argparse
import warnings
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")


# ============================================================
# 内置策略模板
# ============================================================
BUILTIN_STRATEGIES = {
    "value": {
        "name": "价值低估",
        "conditions": [
            {"field": "pe", "op": "<", "value": 20},
            {"field": "pb", "op": "<", "value": 2},
            {"field": "total_mv", "op": "between", "value": [50, 500]},
        ],
        "sort_by": "pe", "top_n": 30,
    },
    "growth": {
        "name": "成长",
        "conditions": [
            {"field": "roe", "op": ">", "value": 15},
            {"field": "pe", "op": "between", "value": [10, 50]},
        ],
        "sort_by": "roe", "top_n": 30,
    },
    "small_cap": {
        "name": "小市值",
        "conditions": [
            {"field": "total_mv", "op": "<", "value": 100},
        ],
        "sort_by": "total_mv", "top_n": 50,
    },
    "momentum": {
        "name": "动量",
        "conditions": [
            {"field": "change_5d", "op": ">", "value": 5},
            {"field": "change_20d", "op": ">", "value": 0},
        ],
        "sort_by": "change_5d", "top_n": 30,
    },
}


# ============================================================
# 数据获取
# ============================================================
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


def get_stock_metrics(codes: List[str] = None) -> pd.DataFrame:
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df

    rename_map = {
        "代码": "code", "名称": "name", "最新价": "price",
        "涨跌幅": "pct_change", "涨跌额": "change",
        "成交量": "volume", "成交额": "amount", "换手率": "turnover",
        "市盈率-动态": "pe", "市净率": "pb", "市销率": "ps",
        "总市值": "total_mv", "流通市值": "circ_mv",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "total_mv" in df.columns:
        df["total_mv"] = df["total_mv"] / 1e8
    if "circ_mv" in df.columns:
        df["circ_mv"] = df["circ_mv"] / 1e8
    if "name" in df.columns:
        df = df[~df["name"].astype(str).str.contains("ST", na=False)]
    if "code" in df.columns:
        df["code"] = df["code"].astype(str)

    # 计算 N 日涨幅
    if codes is None and "code" in df.columns:
        codes = df["code"].tolist()[:500]
    if codes:
        change_5d, change_20d = {}, {}
        for code in codes:
            try:
                end = datetime.now().strftime("%Y%m%d")
                start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                hist = ak.stock_zh_a_hist(symbol=code.zfill(6), period="daily",
                                           start_date=start, end_date=end, adjust="qfq")
                if hist.empty or len(hist) < 6:
                    continue
                hist.columns = [c.lower() for c in hist.columns]
                if "close" in hist.columns:
                    close = hist["close"].iloc[-1]
                    if len(hist) >= 6:
                        change_5d[code] = (close - hist["close"].iloc[-6]) / hist["close"].iloc[-6] * 100
                    if len(hist) >= 21:
                        change_20d[code] = (close - hist["close"].iloc[-21]) / hist["close"].iloc[-21] * 100
            except Exception:
                continue
        if "code" in df.columns:
            df["change_5d"] = df["code"].map(change_5d)
            df["change_20d"] = df["code"].map(change_20d)

    return df


# ============================================================
# 信号定义
# ============================================================
def check_signal_for_code(code: str, signal: str) -> bool:
    """检查单只股票是否触发信号"""
    df = get_kline(code, days=60)
    if df.empty or len(df) < 30:
        return False
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    if signal == "ma_cross":
        ma5_last = df["close"].tail(5).mean()
        ma20_last = df["close"].tail(20).mean()
        return bool(ma5_last > ma20_last)
    elif signal == "macd_golden":
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        return bool(dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2])
    elif signal == "macd_death":
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        return bool(dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2])
    elif signal == "above_ma20":
        return bool(last["close"] > df["close"].tail(20).mean())
    elif signal == "above_ma60":
        return bool(last["close"] > df["close"].tail(60).mean()) if len(df) >= 60 else False
    elif signal == "volume_break":
        if "volume" not in df.columns or len(df) < 6:
            return False
        return bool(last["volume"] > df["volume"].tail(5).mean() * 1.5)
    elif signal == "volume_shrink":
        if "volume" not in df.columns or len(df) < 6:
            return False
        return bool(last["volume"] < df["volume"].tail(5).mean() * 0.7)
    elif signal == "rsi_oversold":
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(6).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = (100 - 100 / (1 + rs)).iloc[-1]
        return bool(rsi < 30)
    elif signal == "rsi_overbought":
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(6).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = (100 - 100 / (1 + rs)).iloc[-1]
        return bool(rsi > 70)
    elif signal == "kdj_golden":
        low_n = df["low"].rolling(9).min()
        high_n = df["high"].rolling(9).max()
        rsv = (df["close"] - low_n) / (high_n - low_n) * 100
        k = rsv.ewm(alpha=1/3, adjust=False).mean()
        d = k.ewm(alpha=1/3, adjust=False).mean()
        return bool(k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2] and k.iloc[-1] < 50)
    elif signal == "new_high_60":
        if len(df) < 60:
            return False
        return bool(df["close"].iloc[-1] >= df["high"].tail(60).max())
    return False


# ============================================================
# 条件检查 (自定义)
# ============================================================
def check_condition(row: pd.Series, cond: Dict) -> bool:
    field = cond["field"]
    op = cond["op"]
    val = cond["value"]
    if field not in row.index:
        return False
    v = row[field]
    if v is None or (hasattr(pd, 'isna') and pd.isna(v)):
        return False
    try:
        if op == ">":
            return bool(v > val)
        elif op == "<":
            return bool(v < val)
        elif op == ">=":
            return bool(v >= val)
        elif op == "<=":
            return bool(v <= val)
        elif op == "between":
            if isinstance(val, (list, tuple)) and len(val) == 2:
                return bool(val[0] <= v <= val[1])
        elif op == "==":
            return bool(v == val)
        elif op == "!=":
            return bool(v != val)
    except Exception:
        return False
    return False


# ============================================================
# 筛选核心
# ============================================================
def screen(conditions: List[Dict] = None, signals: List[str] = None,
          mode: str = "and", sort_by: str = None, top_n: int = 30,
          scope: List[str] = None) -> pd.DataFrame:
    """统一筛选入口
    Args:
        conditions: 自定义条件列表 (例如 [{"field": "pe", "op": "<", "value": 20}])
        signals: 内置信号列表 (例如 ["macd_golden", "above_ma20"])
        mode: and / or
    """
    df = get_stock_metrics(scope)
    if df.empty:
        return df

    mask = pd.Series([True] * len(df), index=df.index)

    # 应用自定义条件
    if conditions:
        for cond in conditions:
            cond_mask = df.apply(lambda row: check_condition(row, cond), axis=1)
            mask = mask & cond_mask

    # 应用内置信号
    if signals:
        if scope is None and "code" in df.columns:
            scope_codes = df["code"].tolist()[:500]
        else:
            scope_codes = scope or []
        triggered_map = {}
        for code in scope_codes:
            triggered = []
            for sig in signals:
                if check_signal_for_code(code, sig):
                    triggered.append(sig)
            triggered_map[code] = triggered

        def has_signals(code):
            trig = triggered_map.get(code, [])
            if mode == "and":
                return len(trig) == len(signals)
            else:
                return len(trig) > 0

        sig_mask = df["code"].apply(lambda c: has_signals(str(c)))
        mask = mask & sig_mask

    result = df[mask].copy()

    # 排序
    if sort_by and sort_by in result.columns:
        result = result.sort_values(sort_by, ascending=True)
    elif "pct_change" in result.columns:
        result = result.sort_values("pct_change", ascending=False)

    return result.head(top_n)


def parse_condition(expr: str) -> Dict:
    """解析 'field<value' 格式"""
    for op in [">=", "<=", "!=", "==", ">", "<"]:
        if op in expr:
            parts = expr.split(op, 1)
            if len(parts) == 2:
                return {"field": parts[0].strip(), "op": op, "value": float(parts[1].strip())}
    if " between " in expr:
        parts = expr.split(" between ")
        if len(parts) == 2:
            vals = [float(x.strip()) for x in parts[1].split(",")]
            return {"field": parts[0].strip(), "op": "between", "value": vals}
    return {}


def parse_where_args(where_list: List[str]) -> List[Dict]:
    return [parse_condition(w) for w in where_list if w]


def load_strategy(name_or_path: str) -> Dict:
    if name_or_path in BUILTIN_STRATEGIES:
        return BUILTIN_STRATEGIES[name_or_path]
    if os.path.exists(name_or_path):
        try:
            if name_or_path.endswith((".yaml", ".yml")):
                import yaml
                with open(name_or_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            with open(name_or_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="screener (2合1)")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("screen", help="筛选")
    p.add_argument("--where", action="append", help="自定义条件: 'pe<20'")
    p.add_argument("--signals", help="内置信号: 'macd_golden,above_ma20'")
    p.add_argument("--mode", default="and", choices=["and", "or"])
    p.add_argument("--strategy", help="策略名/文件")
    p.add_argument("--sort", help="排序字段")
    p.add_argument("--top", type=int, default=30)

    sub.add_parser("list", help="列出内置策略")
    p = sub.add_parser("show", help="显示策略")
    p.add_argument("name")
    args = parser.parse_args()

    if args.cmd == "list":
        print("内置策略:")
        for k, v in BUILTIN_STRATEGIES.items():
            print(f"  {k}: {v['name']}")
    elif args.cmd == "show":
        s = load_strategy(args.name)
        print(json.dumps(s, ensure_ascii=False, indent=2))
    elif args.cmd == "screen":
        if args.strategy:
            s = load_strategy(args.strategy)
            conds = s.get("conditions", [])
            sort_by = s.get("sort_by")
            top_n = s.get("top_n", args.top)
        else:
            conds = parse_where_args(args.where or [])
            sort_by = args.sort
            top_n = args.top
        signals = [s.strip() for s in (args.signals or "").split(",")] if args.signals else None

        if not conds and not signals:
            print("请提供 --where 或 --signals 或 --strategy")
            return

        r = screen(conditions=conds, signals=signals, mode=args.mode,
                  sort_by=sort_by, top_n=top_n)
        if r.empty:
            print("无符合条件")
        else:
            print(f"\n=== 筛选结果 ({len(r)} 只) ===")
            cols = [c for c in ["code", "name", "price", "pct_change", "pe", "pb", "total_mv", "turnover", "change_5d"] if c in r.columns]
            print(r[cols].to_string())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
