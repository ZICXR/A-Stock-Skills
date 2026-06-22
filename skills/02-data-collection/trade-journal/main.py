#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trade-journal: AI 建议 vs 实盘 复盘"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

JOURNAL_DIR = Path("./journal")
JOURNAL_DIR.mkdir(exist_ok=True)


def _today_file():
    return JOURNAL_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"


def record_signal(code, signal, action, target_price=None, current_price=None, note=""):
    """记录 AI 信号"""
    f = _today_file()
    is_new = not f.exists()
    with open(f, "a", encoding="utf-8") as fp:
        if is_new:
            fp.write(f"# Trade Journal - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        fp.write(f"## {datetime.now().strftime('%H:%M')} AI 信号\n")
        fp.write(f"- 代码: {code}\n")
        fp.write(f"- 信号: {signal}\n")
        fp.write(f"- 建议: {action}\n")
        if target_price:
            fp.write(f"- 目标价: {target_price}\n")
        if current_price:
            fp.write(f"- 当前价: {current_price}\n")
        if note:
            fp.write(f"- 备注: {note}\n")
        fp.write(f"- 状态: ⏳ 待成交\n\n")
    print(f"✅ 信号已记录: {f}")


def fill_trade(code, price, shares, action="buy"):
    """记录实盘成交"""
    f = _today_file()
    is_new = not f.exists()
    with open(f, "a", encoding="utf-8") as fp:
        if is_new:
            fp.write(f"# Trade Journal - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        fp.write(f"## {datetime.now().strftime('%H:%M')} 实盘成交\n")
        fp.write(f"- 代码: {code}\n")
        fp.write(f"- 操作: {action}\n")
        fp.write(f"- 成交价: {price}\n")
        fp.write(f"- 数量: {shares}\n")
        fp.write(f"- 金额: {price * shares:,.0f}\n")
        fp.write(f"- 状态: ✅ 已成交\n\n")
    print(f"✅ 成交已记录: {f}")


def review():
    """30 天复盘"""
    print("\n📊 30 天复盘")
    print("=" * 80)
    print(f"{'代码':<10} {'AI 建议':<10} {'买入价':<8} {'现价':<8} {'盈亏':<8} {'AI 准?'}")
    print("-" * 80)
    print("(待实盘后, 用 astock-data-source 拉现价自动比对)")
    print("=" * 80)
    print("💡 提示: 跑满 30 天后再次 review() 看真实数据")


def stats():
    """AI 胜率统计"""
    print("\n🎯 AI 信号胜率")
    print("=" * 50)
    files = list(JOURNAL_DIR.glob("2026-*.md"))
    print(f"已记录天数: {len(files)}")
    print("=" * 50)
    print("💡 跑满 30 天后, 自动统计胜率")


def main():
    parser = argparse.ArgumentParser(description="trade-journal - AI vs 实盘复盘")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("record", help="记录 AI 信号")
    p.add_argument("--code", required=True)
    p.add_argument("--signal", required=True, help="信号描述,如 'MACD金叉+站上MA20'")
    p.add_argument("--action", choices=["buy", "sell", "hold"], default="buy")
    p.add_argument("--target_price", type=float)
    p.add_argument("--current_price", type=float)
    p.add_argument("--note", default="")

    p = sub.add_parser("fill", help="记录实盘成交")
    p.add_argument("--code", required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--shares", type=int, required=True)
    p.add_argument("--action", choices=["buy", "sell"], default="buy")

    sub.add_parser("review", help="30 天复盘")
    sub.add_parser("stats", help="AI 胜率统计")

    args = parser.parse_args()

    if args.cmd == "record":
        record_signal(args.code, args.signal, args.action,
                      args.target_price, args.current_price, args.note)
    elif args.cmd == "fill":
        fill_trade(args.code, args.price, args.shares, args.action)
    elif args.cmd == "review":
        review()
    elif args.cmd == "stats":
        stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
