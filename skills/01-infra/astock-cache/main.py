#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""astock-cache: 磁盘缓存"""

import os
import json
import time
import pickle
import argparse
import hashlib
from functools import wraps
from typing import Any, Optional

CACHE_DIR = os.path.expanduser("~/.astock_skills/cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _hash_key(key: str) -> str:
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def _file_path(key: str) -> str:
    return os.path.join(CACHE_DIR, _hash_key(key) + ".pkl")


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """设置缓存"""
    try:
        data = {"value": value, "expire": time.time() + ttl, "ts": time.time()}
        with open(_file_path(key), "wb") as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        print(f"缓存设置失败: {e}")
        return False


def cache_get(key: str) -> Optional[Any]:
    """获取缓存"""
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
    """删除缓存"""
    path = _file_path(key)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def cache_clear() -> int:
    """清空所有缓存"""
    cnt = 0
    for f in os.listdir(CACHE_DIR):
        if f.endswith(".pkl"):
            os.remove(os.path.join(CACHE_DIR, f))
            cnt += 1
    return cnt


def cache_stats() -> dict:
    """缓存统计"""
    total_size = 0
    cnt = 0
    for f in os.listdir(CACHE_DIR):
        if f.endswith(".pkl"):
            cnt += 1
            total_size += os.path.getsize(os.path.join(CACHE_DIR, f))
    return {"count": cnt, "size_mb": round(total_size / 1024 / 1024, 2)}


def cached(key: str, ttl: int = 300):
    """装饰器"""
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


def main():
    parser = argparse.ArgumentParser(description="astock-cache")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("set", help="设置")
    p.add_argument("key")
    p.add_argument("value")
    p.add_argument("--ttl", type=int, default=300)
    p = sub.add_parser("get", help="获取")
    p.add_argument("key")
    sub.add_parser("delete", help="删除").add_argument("key")
    sub.add_parser("stats", help="统计")
    sub.add_parser("clear", help="清空")
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
