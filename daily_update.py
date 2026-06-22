#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_update.py: 每天 15:30 跑一次, 更新全市场 K 线缓存

用法:
    python daily_update.py                  # 跑全市场
    python daily_update.py --codes 000001,600519   # 只更新指定
    python daily_update.py --days 60        # 60 日 K 线

建议 cron (Linux/Mac):
    30 15 * * 1-5 cd /path/to/A-Stock-Skills && python daily_update.py >> logs/daily.log 2>&1

建议 Windows 任务计划程序:
    触发器: 周一-周五 15:30
    操作: python D:\myCode\python\a_stock_skills\daily_update.py
"""

import sys
import time
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# 让 daily_update.py 可被项目外调用
SKILLS_DIR = Path(__file__).parent / "skills"
sys.path.insert(0, str(Path(__file__).parent))

from skills.01-infra.astock-data-source.main import get_realtime_all, get_kline, SOURCE_FAIL_COUNT
from skills.01-infra.astock-cache.main import kline_save, kline_stats


def get_all_codes():
    """拿全市场股票代码"""
    print("📡 拉取全市场代码列表...")
    df = get_realtime_all()
    if df is None or df.empty:
        print("❌ 拉取失败, 检查数据源")
        return []
    code_col = "代码" if "代码" in df.columns else df.columns[0]
    codes = df[code_col].astype(str).str.zfill(6).tolist()
    print(f"✅ 拿到 {len(codes)} 只股票")
    return codes


def update_one(code, days=60):
    """更新单只 K 线"""
    try:
        df = get_kline(code, days=days)
        if df is not None and not df.empty:
            kline_save(code, df, days=days)
            return True
    except Exception as e:
        print(f"  ⚠️ {code}: {e}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description="每日 K 线缓存更新")
    parser.add_argument("--codes", help="指定股票代码,逗号分隔")
    parser.add_argument("--days", type=int, default=60, help="K 线天数 (默认 60)")
    parser.add_argument("--workers", type=int, default=1, help="并发数 (默认 1, 稳)")
    args = parser.parse_args()

    print("=" * 60)
    print(f"📊 每日 K 线更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   K 线天数: {args.days}")
    print("=" * 60)

    if args.codes:
        codes = [c.strip().zfill(6) for c in args.codes.split(",")]
    else:
        codes = get_all_codes()

    if not codes:
        print("❌ 没有股票代码, 退出")
        return

    print(f"🔄 开始更新 {len(codes)} 只股票 K 线...")
    start = time.time()
    success = 0
    fail = 0

    for i, code in enumerate(codes, 1):
        if update_one(code, args.days):
            success += 1
        else:
            fail += 1

        # 每 100 只打印进度
        if i % 100 == 0:
            elapsed = time.time() - start
            speed = i / elapsed
            eta = (len(codes) - i) / speed
            print(f"  [{i}/{len(codes)}] 成功 {success} 失败 {fail} "
                  f"速度 {speed:.1f} 只/秒 剩余 {eta/60:.1f} 分钟")

    elapsed = time.time() - start
    print("=" * 60)
    print(f"✅ 完成! 成功 {success} / 失败 {fail}  耗时 {elapsed/60:.1f} 分钟")
    print(f"📦 缓存统计: {kline_stats()}")


if __name__ == "__main__":
    main()
