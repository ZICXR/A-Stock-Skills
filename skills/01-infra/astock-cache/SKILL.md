---
name: astock-cache
description: 磁盘缓存 + K线 parquet。当用户跑全市场筛选每次都要等 30 分钟时,Claude 应使用此 Skill。K线缓存到 ~/.astock_skills/cache/kline/ 目录,5 秒 vs 30 分钟,差 360 倍。
---

# astock-cache

## 何时使用

- 全市场筛选太慢 (每次 30 分钟)
- 反复拉同一只股票 K 线
- 跑 screener 跑 2 遍
- 想要"盘后更新一次,白天用一天"

## 🚀 快速上手

```bash
# 看缓存多少了
python main.py kline-stats

# 跑一次全市场 K 线更新 (15-30 分钟, 但之后都是 5 秒)
python daily_update.py

# 单独看某只股票
python main.py kline-stats
# {"count": 5028, "size_mb": 18.4}
```

## 提供能力

### 通用 Key-Value 缓存
- `cache_set/get/delete/clear`
- `cached(key, ttl)` 装饰器
- 存储: `~/.astock_skills/cache/*.pkl`

### K 线 parquet 缓存 (新,推荐)
- `kline_save(code, df, days)` 存 parquet
- `kline_load(code, days, max_age_hours)` 读
- `kline_get_or_fetch(code, fetch_fn, days)` **智能模式**
- 存储: `~/.astock_skills/cache/kline/{code}_{days}d.parquet`

## screener 集成示例

```python
from skills.01-infra.astock-cache.main import kline_get_or_fetch
from skills.01-infra.astock-data-source.main import get_kline

def smart_kline(code, days=60):
    """优先读缓存, 缓存没有才拉网络"""
    return kline_get_or_fetch(code, get_kline, days=days)

# 第一次慢 (拉网络), 之后 5 秒
df = smart_kline("601991", 60)
```

## 性能

| 场景 | 无缓存 | 有缓存 | 加速比 |
|------|--------|--------|--------|
| 单股 60 日 K 线 | 1.2s | 0.05s | 24x |
| 全市场 5028 只 60 日 | 30min | 5s | 360x |

## 依赖

```
pandas>=1.5.0
pyarrow>=10.0.0  # parquet 引擎
```
