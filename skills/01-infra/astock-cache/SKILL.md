---
name: astock-cache
description: A 股数据磁盘缓存。当用户需要持久化缓存 A 股数据、避免重复请求、提升数据获取速度、降低 API 限流风险时,Claude 应使用此 Skill。支持 TTL 过期、Key-Value 存储、文件持久化,可作为高频调用 Skill 的底层加速组件。
---

# A 股数据缓存 Skill

## 何时使用

- 用户需要缓存数据, 减少 API 请求
- 用户需要长期保存数据
- 用户遇到 API 限流
- 批量分析时避免重复请求

## 提供能力

- `cache_set(key, value, ttl)` - 设置缓存
- `cache_get(key)` - 获取缓存
- `cache_delete(key)` - 删除缓存
- `cache_clear()` - 清空所有
- `cached(key, ttl)` - 装饰器
- `cache_stats()` - 缓存统计

## 使用方式

```bash
python main.py set 000001_realtime '{"price": 12.34, ...}' --ttl 300
python main.py get 000001_realtime
python main.py stats
python main.py clear
```

## Python API

```python
from skills.01-infra.astock-cache.main import cache_get, cache_set, cached

# 直接使用
cache_set("test", {"data": 123}, ttl=300)
data = cache_get("test")

# 装饰器
@cached("stock_kline_000001", ttl=600)
def fetch_kline():
    import akshare as ak
    return ak.stock_zh_a_hist(symbol="000001")
```

## 缓存策略

- 默认 TTL: 300 秒 (5 分钟)
- 存储位置: `~/.astock_skills/cache/`
- 格式: JSON / pickle

## 依赖

```
无 (纯标准库)
```
