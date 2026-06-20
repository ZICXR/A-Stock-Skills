#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-screener-custom: 自定义条件筛选器"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


# ============================================================
# 内置策略模板
# ============================================================
BUILTIN_STRATEGIES = {
    "value": {
        "name": "价值低估",
        "description": "低估值 + 高 ROE",
        "conditions": [
            {"field": "pe", "op": "<", "value": 20, "opposite": False},
            {"field": "pb", "op": "<", "value": 2, "opposite": False},
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
    "low_pe_high_roe": {
        "name": "低估值高盈利",
        "conditions": [
            {"field": "pe", "op": "between", "value": [5, 25]},
            {"field": "pb", "op": "<", "value": 3},
            {"field": "roe", "op": ">", "value": 12},
        ],
        "sort_by": "pe", "top_n": 30,
    },
}


# ============================================================
# 策略加载
# ============================================================
def load_strategy(name_or_path: str) -> Dict:
    """加载策略"""
    # 内置策略
    if name_or_path in BUILTIN_STRATEGIES:
        return BUILTIN_STRATEGIES[name_or_path]
    # 文件策略
    if os.path.exists(name_or_path):
        try:
            if name_or_path.endswith((".yaml", ".yml")):
                import yaml
                with open(name_or_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            else:
                with open(name_or_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载策略失败: {e}", file=sys.stderr)
    return {}


def save_strategy(name: str, conditions: List[Dict], **kwargs):
    """保存策略"""
    strategy = {"name": name, "conditions": conditions}
    strategy.update(kwargs)
    path = f"./strategy_{name}.yaml"
    try:
        import yaml
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(strategy, f, allow_unicode=True, default_flow_style=False)
        print(f"策略已保存: {path}")
    except Exception as e:
        print(f"保存失败: {e}", file=sys.stderr)


# ============================================================
# 条件判断
# ============================================================
def check_condition(row: pd.Series, cond: Dict) -> bool:
    """单条件判断"""
    field = cond["field"]
    op = cond["op"]
    val = cond["value"]

    if field not in row.index or pd.isna(row[field]):
        return False

    v = row[field]
    if op == ">":
        return bool(v > val)
    elif op == "<":
        return bool(v < val)
    elif op == ">=":
        return bool(v >= val)
    elif op == "<=":
        return bool(v <= val)
    elif op == "==":
        return bool(v == val)
    elif op == "!=":
        return bool(v != val)
    elif op == "between":
        if isinstance(val, (list, tuple)) and len(val) == 2:
            return bool(val[0] <= v <= val[1])
    elif op == "in":
        return bool(v in val)
    elif op == "not in":
        return bool(v not in val)
    return False


# ============================================================
# 数据获取
# ============================================================
def get_stock_metrics(codes: List[str] = None) -> pd.DataFrame:
    """获取股票指标"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
    except Exception as e:
        print(f"获取数据失败: {e}", file=sys.stderr)
        return pd.DataFrame()

    if df.empty:
        return df

    # 标准化列名
    rename_map = {
        "代码": "code", "名称": "name",
        "最新价": "price", "涨跌幅": "pct_change", "涨跌额": "change",
        "成交量": "volume", "成交额": "amount", "换手率": "turnover",
        "市盈率-动态": "pe", "市净率": "pb", "市销率": "ps",
        "总市值": "total_mv", "流通市值": "circ_mv",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # 转换单位 (总市值: 元 -> 亿)
    if "total_mv" in df.columns:
        df["total_mv"] = df["total_mv"] / 1e8
    if "circ_mv" in df.columns:
        df["circ_mv"] = df["circ_mv"] / 1e8

    # 排除 ST
    if "name" in df.columns:
        df = df[~df["name"].astype(str).str.contains("ST", na=False)]

    # 计算 N 日涨幅
    if codes is None:
        codes = df["code"].astype(str).tolist()

    # 限制数量 (性能考虑)
    if len(codes) > 500:
        codes = codes[:500]

    # 批量计算 change_5d / change_20d
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

    df["change_5d"] = df["code"].astype(str).map(change_5d)
    df["change_20d"] = df["code"].astype(str).map(change_20d)

    return df


# ============================================================
# 筛选
# ============================================================
def screen_custom(conditions: List[Dict], sort_by: str = None, top_n: int = 30, scope_codes: List[str] = None) -> pd.DataFrame:
    """自定义筛选"""
    df = get_stock_metrics(scope_codes)
    if df.empty:
        return df

    # 应用条件
    mask = pd.Series([True] * len(df), index=df.index)
    for cond in conditions:
        cond_mask = df.apply(lambda row: check_condition(row, cond), axis=1)
        mask = mask & cond_mask

    result = df[mask].copy()

    # 排序
    if sort_by and sort_by in result.columns:
        result = result.sort_values(sort_by, ascending=True)
    elif "pct_change" in result.columns:
        result = result.sort_values("pct_change", ascending=False)

    return result.head(top_n)


# ============================================================
# 条件字符串解析
# ============================================================
def parse_condition(expr: str) -> Dict:
    """解析 'field<value' 格式"""
    for op in [">=", "<=", "!=", "==", ">", "<"]:
        if op in expr:
            parts = expr.split(op, 1)
            if len(parts) == 2:
                return {"field": parts[0].strip(), "op": op, "value": float(parts[1].strip())}
    # between
    if " between " in expr:
        parts = expr.split(" between ")
        if len(parts) == 2:
            vals = [float(x.strip()) for x in parts[1].split(",")]
            return {"field": parts[0].strip(), "op": "between", "value": vals}
    return {}


def parse_where_args(where_list: List[str]) -> List[Dict]:
    """解析多个 where 参数"""
    return [parse_condition(w) for w in where_list if w]


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="stock-screener-custom")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("screen", help="筛选")
    p.add_argument("--where", action="append", help="条件, 如 'pe<20'")
    p.add_argument("--strategy", help="策略名称或路径")
    p.add_argument("--sort", help="排序字段")
    p.add_argument("--top", type=int, default=30)
    p = sub.add_parser("save", help="保存策略")
    p.add_argument("--name", required=True)
    p.add_argument("--where", action="append")
    p = sub.add_parser("list", help="列出内置策略")
    p = sub.add_parser("show", help="显示策略")
    p.add_argument("name")
    args = parser.parse_args()

    if args.cmd == "list":
        print("内置策略:")
        for k, v in BUILTIN_STRATEGIES.items():
            print(f"  {k}: {v.get('name', k)}")
    elif args.cmd == "show":
        s = load_strategy(args.name)
        print(json.dumps(s, ensure_ascii=False, indent=2))
    elif args.cmd == "save":
        conds = parse_where_args(args.where or [])
        save_strategy(args.name, conds)
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
        if not conds:
            print("请提供 --where 条件或 --strategy 策略")
            return
        print(f"\n筛选条件: {len(conds)} 个")
        for c in conds:
            print(f"  - {c}")
        r = screen_custom(conds, sort_by=sort_by, top_n=top_n)
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
