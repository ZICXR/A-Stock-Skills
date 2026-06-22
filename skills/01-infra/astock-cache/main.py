#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""astock-cache: 磁盘缓存 (K线 parquet + Key-Value)"""

import os
import sys
import json
import time
import pickle
import argparse
import hashlib
import pandas as pd
from pathlib import Path
from functools import wraps
from typing import Any, Optional
from datetime import datetime

CACHE_DIR = Path(os.path.expanduser("~/.astock_skills/cache"))
KLINE_DIR = CACHE_DIR / "kline"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
KLINE_DIR.mkdir(exist_ok=True)


# ============================================================
# 通用 Key-Value 缓存 (兼容旧 API)
# ============================================================
def _hash_key(key: str) -> str:
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def _file_path(key: str) -> str:
    return str(CACHE_DIR / (_hash_key(key) + ".pkl"))


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    try:
        data = {"value": value, "expire": time.time() + ttl, "ts": time.time()}
        with open(_file_path(key), "wb") as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        print(f"缓存设置失败: {e}")
        return False


def cache_get(key: str) -> Optional[Any]:
    path = _file_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        if time.time() > data.get("expire", 0):
            os.remove(path)
            return None
        return data.get("value")
    except Exception:
        return None


def cache_delete(key: str) -> bool:
    path = _file_path(key)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def cache_clear() -> int:
    cnt = 0
    for f in CACHE_DIR.iterdir():
        if f.suffix == ".pkl":
            f.unlink()
            cnt += 1
    return cnt


def cache_stats() -> dict:
    total_size = 0
    cnt = 0
    for f in CACHE_DIR.iterdir():
        if f.suffix == ".pkl":
            cnt += 1
            total_size += f.stat().st_size
    return {"count": cnt, "size_mb": round(total_size / 1024 / 1024, 2)}


def cached(key: str, ttl: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key}:{args}:{kwargs}"
            cached_val = cache_get(cache_key)
            if cached_val is not None:
                return cached_val
            result = func(*args, **kwargs)
            cache_set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


# ============================================================
# K线 parquet 缓存 (新) - 性能核心
# ============================================================
def kline_path(code: str, days: int = 60) -> Path:
    """获取 K 线缓存路径"""
    return KLINE_DIR / f"{code}_{days}d.parquet"


def kline_save(code: str, df: pd.DataFrame, days: int = 60) -> bool:
    """保存 K 线到 parquet"""
    try:
        path = kline_path(code, days)
        df.to_parquet(path)
        return True
    except Exception as e:
        print(f"保存 K 线失败: {e}", file=sys.stderr)
        return False


def kline_load(code: str, days: int = 60, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
    """从 parquet 读取 K 线 (24 小时内的缓存有效)"""
    path = kline_path(code, days)
    if not path.exists():
        return None
    # 检查文件年龄
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    if age_hours > max_age_hours:
        return None
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def kline_get_or_fetch(code: str, fetch_fn, days: int = 60, max_age_hours: int = 24) -> pd.DataFrame:
    """智能获取 K 线: 缓存命中直接返回, 否则调 fetch_fn"""
    df = kline_load(code, days, max_age_hours)
    if df is not None:
        return df
    df = fetch_fn(code, days)
    if df is not None and not df.empty:
        kline_save(code, df, days)
    return df


def kline_stats() -> dict:
    """K 线缓存统计"""
    total_size = 0
    cnt = 0
    if KLINE_DIR.exists():
        for f in KLINE_DIR.iterdir():
            if f.suffix == ".parquet":
                cnt += 1
                total_size += f.stat().st_size
    return {"count": cnt, "size_mb": round(total_size / 1024 / 1024, 2)}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="astock-cache")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("set", help="设置 KV")
    p.add_argument("key")
    p.add_argument("value")
    p.add_argument("--ttl", type=int, default=300)

    p = sub.add_parser("get", help="获取 KV")
    p.add_argument("key")

    sub.add_parser("delete", help="删除").add_argument("key")
    sub.add_parser("stats", help="KV 缓存统计")
    sub.add_parser("clear", help="清空 KV 缓存")

    p = sub.add_parser("kline-stats", help="K线缓存统计")
    p = sub.add_parser("kline-clear", help="清空K线缓存")
    p.add_argument("--code", help="只清空指定股票")

    args = parser.parse_args()

    if args.cmd == "set":
        try:
            val = json.loads(args.value)
        except:
            val = args.value
        ok = cache_set(args.key, val, args.ttl)
        print("OK" if ok else "FAIL")
    elif args.cmd == "get":
        v = cache_get(args.key)
        print(json.dumps(v, ensure_ascii=False, default=str) if v is not None else "(空)")
    elif args.cmd == "delete":
        cache_delete(args.key)
        print("OK")
    elif args.cmd == "stats":
        print(json.dumps(cache_stats(), ensure_ascii=False))
    elif args.cmd == "clear":
        n = cache_clear()
        print(f"已清除 {n} 个")
    elif args.cmd == "kline-stats":
        print(json.dumps(kline_stats(), ensure_ascii=False))
    elif args.cmd == "kline-clear":
        if args.code:
            p = kline_path(args.code)
            if p.exists():
                p.unlink()
                print(f"已删除 {p}")
            else:
                print("不存在")
        else:
            n = 0
            for f in KLINE_DIR.iterdir():
                if f.suffix == ".parquet":
                    f.unlink()
                    n += 1
            print(f"已清空 {n} 个 K 线缓存")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
