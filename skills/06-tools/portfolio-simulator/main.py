#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""portfolio-simulator: 虚拟持仓模拟器"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

SIM_DIR = os.path.expanduser("~/.astock_skills/simulations")
os.makedirs(SIM_DIR, exist_ok=True)


def _sim_path(name: str) -> str:
    return os.path.join(SIM_DIR, f"{name}.json")


def _load(name: str) -> Dict:
    path = _sim_path(name)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(name: str, data: Dict):
    with open(_sim_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def get_quote(code: str) -> Dict:
    """获取实时行情"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return {}
        row = target.iloc[0]
        return {
            "price": float(row.get("最新价", 0)),
            "pct_change": float(row.get("涨跌幅", 0)),
            "name": row.get("名称", ""),
        }
    except Exception:
        return {}


# ============================================================
# 核心操作
# ============================================================
def init(name: str, capital: float = 100000, benchmark: str = "000300") -> Dict:
    """初始化"""
    data = {
        "name": name,
        "initial_capital": capital,
        "current_cash": capital,
        "benchmark": benchmark,
        "positions": {},  # {code: {shares, cost, ...}}
        "trades": [],     # 交易历史
        "created_at": datetime.now().isoformat(),
    }
    _save(name, data)
    return data


def buy(name: str, code: str, price: float, shares: int, reason: str = "") -> Dict:
    """买入"""
    data = _load(name)
    if not data:
        return {"error": f"模拟账户 {name} 不存在, 请先 init"}

    cost = price * shares
    if cost > data["current_cash"]:
        return {"error": f"资金不足, 需要 {cost}, 现金 {data['current_cash']}"}

    data["current_cash"] -= cost

    if code in data["positions"]:
        pos = data["positions"][code]
        total_shares = pos["shares"] + shares
        total_cost = pos["cost"] * pos["shares"] + price * shares
        pos["shares"] = total_shares
        pos["cost"] = total_cost / total_shares
    else:
        data["positions"][code] = {
            "shares": shares,
            "cost": price,
            "name": get_quote(code).get("name", ""),
        }

    data["trades"].append({
        "type": "buy",
        "code": code,
        "price": price,
        "shares": shares,
        "amount": cost,
        "reason": reason,
        "time": datetime.now().isoformat(),
    })

    _save(name, data)
    return {"ok": True, "cash": data["current_cash"]}


def sell(name: str, code: str, price: float, shares: int = None, reason: str = "") -> Dict:
    """卖出"""
    data = _load(name)
    if not data:
        return {"error": f"模拟账户 {name} 不存在"}

    if code not in data["positions"]:
        return {"error": f"未持有 {code}"}

    pos = data["positions"][code]
    if shares is None:
        shares = pos["shares"]
    if shares > pos["shares"]:
        return {"error": f"持仓不足, 持有 {pos['shares']}, 卖出 {shares}"}

    revenue = price * shares
    profit = (price - pos["cost"]) * shares
    data["current_cash"] += revenue
    pos["shares"] -= shares

    if pos["shares"] == 0:
        del data["positions"][code]

    data["trades"].append({
        "type": "sell",
        "code": code,
        "price": price,
        "shares": shares,
        "amount": revenue,
        "profit": profit,
        "profit_pct": (price - pos["cost"]) / pos["cost"] * 100,
        "reason": reason,
        "time": datetime.now().isoformat(),
    })

    _save(name, data)
    return {"ok": True, "profit": profit, "cash": data["current_cash"]}


def get_positions(name: str) -> List[Dict]:
    """获取持仓 (含实时盈亏)"""
    data = _load(name)
    if not data:
        return []
    result = []
    for code, pos in data["positions"].items():
        quote = get_quote(code)
        current_price = quote.get("price", pos["cost"])
        market_value = current_price * pos["shares"]
        cost_value = pos["cost"] * pos["shares"]
        profit = market_value - cost_value
        result.append({
            "code": code,
            "name": pos.get("name") or quote.get("name", ""),
            "shares": pos["shares"],
            "cost": round(pos["cost"], 2),
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "profit": round(profit, 2),
            "profit_pct": round((current_price - pos["cost"]) / pos["cost"] * 100, 2),
            "pct_change_today": quote.get("pct_change", 0),
        })
    return result


def get_history(name: str) -> List[Dict]:
    """交易历史"""
    data = _load(name)
    if not data:
        return []
    return data.get("trades", [])


def get_stats(name: str) -> Dict:
    """业绩统计"""
    data = _load(name)
    if not data:
        return {}
    positions = get_positions(name)
    total_mv = sum(p["market_value"] for p in positions)
    total_assets = data["current_cash"] + total_mv
    total_profit = total_assets - data["initial_capital"]
    profit_pct = total_profit / data["initial_capital"] * 100

    trades = [t for t in data.get("trades", []) if t["type"] == "sell"]
    wins = [t for t in trades if t.get("profit", 0) > 0]
    losses = [t for t in trades if t.get("profit", 0) <= 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_win = np.mean([t["profit"] for t in wins]) if wins else 0
    avg_loss = np.mean([t["profit"] for t in losses]) if losses else 0

    return {
        "name": name,
        "initial_capital": data["initial_capital"],
        "current_cash": round(data["current_cash"], 2),
        "market_value": round(total_mv, 2),
        "total_assets": round(total_assets, 2),
        "total_profit": round(total_profit, 2),
        "profit_pct": round(profit_pct, 2),
        "position_count": len(positions),
        "trade_count": len(trades),
        "win_rate": round(win_rate, 2),
        "avg_win": round(float(avg_win), 2),
        "avg_loss": round(float(avg_loss), 2),
    }


def list_simulations() -> List[str]:
    """列出所有模拟账户"""
    if not os.path.exists(SIM_DIR):
        return []
    return [f.replace(".json", "") for f in os.listdir(SIM_DIR) if f.endswith(".json")]


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="portfolio-simulator")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("init", help="初始化")
    p.add_argument("--name", required=True)
    p.add_argument("--capital", type=float, default=100000)
    p.add_argument("--benchmark", default="000300")

    p = sub.add_parser("buy", help="买入")
    p.add_argument("--name", required=True)
    p.add_argument("--code", required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--shares", type=int, required=True)
    p.add_argument("--reason", default="")

    p = sub.add_parser("sell", help="卖出")
    p.add_argument("--name", required=True)
    p.add_argument("--code", required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--shares", type=int)
    p.add_argument("--reason", default="")

    p = sub.add_parser("positions", help="持仓")
    p.add_argument("--name", required=True)

    p = sub.add_parser("history", help="历史")
    p.add_argument("--name", required=True)

    p = sub.add_parser("stats", help="业绩")
    p.add_argument("--name", required=True)

    sub.add_parser("list", help="所有账户")
    args = parser.parse_args()

    if args.cmd == "init":
        init(args.name, args.capital, args.benchmark)
        print(f"✅ 初始化 {args.name} (资金 {args.capital:,.0f})")
    elif args.cmd == "buy":
        r = buy(args.name, args.code, args.price, args.shares, args.reason)
        print(r)
    elif args.cmd == "sell":
        r = sell(args.name, args.code, args.price, args.shares, args.reason)
        print(r)
    elif args.cmd == "positions":
        positions = get_positions(args.name)
        if not positions:
            print("无持仓")
        else:
            print(f"\n=== {args.name} 持仓 ===")
            for p in positions:
                print(f"  {p['code']} {p['name']}: {p['shares']}股 "
                      f"@ {p['cost']} -> {p['current_price']} "
                      f"盈亏 {p['profit']:+,.0f} ({p['profit_pct']:+.2f}%)")
    elif args.cmd == "history":
        trades = get_history(args.name)
        for t in trades:
            print(f"  {t['time'][:10]} {t['type']} {t['code']} "
                  f"{t['shares']}股 @ {t['price']} "
                  f"({t.get('profit', '')}) {t.get('reason', '')}")
    elif args.cmd == "stats":
        s = get_stats(args.name)
        for k, v in s.items():
            print(f"  {k}: {v}")
    elif args.cmd == "list":
        for n in list_simulations():
            print(f"  {n}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
