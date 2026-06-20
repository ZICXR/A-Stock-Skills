---
name: astock-data-source
description: A 股多源数据源统一管理。当用户需要获取股票行情、K 线、财务数据、新闻、公告、资金流等数据时,Claude 应优先使用此 Skill 作为数据访问入口。它封装了 akshare、tushare、东方财富三大主流数据源,提供自动重试、限流控制、失败降级、内存缓存等机制,确保稳定可靠的数据获取。
---

# A 股多源数据源管理 Skill

## 何时使用

- 用户要求获取股票数据 (行情/K 线/财务等)
- 用户提到使用 akshare、tushare 或类似数据接口
- 任何需要稳定获取 A 股数据的场景
- 需要数据源故障时自动降级

## 数据源策略

1. **akshare** (默认主源) - 免费、覆盖全、社区活跃
2. **tushare** (辅助源) - 高质量数据,需 token
3. **东方财富直连** (备选) - 实时性好

## 提供能力

### 行情数据
- `get_realtime_all()` - 全 A 股实时行情
- `get_realtime(code)` - 单只股票实时行情
- `get_index_realtime()` - 主要指数实时行情

### K 线数据
- `get_kline(code, days, adjust)` - 个股历史 K 线 (前复权/后复权/不复权)
- `get_index_kline(symbol, days)` - 指数历史 K 线

### 基本面数据
- `get_stock_info(code)` - 个股基本信息
- `get_financial(code)` - 财务指标
- `get_holders(code)` - 前十大股东

### 资金/题材
- `get_fund_flow(code)` - 个股资金流
- `get_sector_flow()` - 板块资金流
- `get_news(code)` - 个股新闻
- `get_announcement(code)` - 个股公告
- `get_zt_pool()` - 涨停板池
- `get_lhb(date)` - 龙虎榜
- `get_north_bound()` - 北向资金

## 工作流程

```
用户请求 → 检查缓存 (5min TTL) → 调用 akshare (主) 
    ↓ 失败
调用 tushare (辅) → 调用东财直连 (备) → 抛出异常
```

## 使用方式

```bash
# 列出所有可用方法
python main.py --list

# 调用具体方法
python main.py get_realtime 000001
python main.py get_kline 000001 --days 60 --adjust qfq
python main.py get_zt_pool
```

## Python API

```python
from skills.01-infra.astock-data-source.main import get_source

source = get_source()
df = source.get_realtime("000001")
print(df)
```

## 依赖

```
akshare>=1.12.0
tushare>=1.4.0
requests>=2.28.0
pandas>=1.5.0
```

## 配置

```bash
# 可选: 配置 tushare token 提高数据质量
export TUSHARE_TOKEN="your_token_here"
```

## 注意事项

1. 交易时段接口压力大,建议错峰请求
2. 大量请求会自动限流 (默认 2 次/秒)
3. 重复请求走内存缓存 (5 分钟)
4. 所有方法都有 3 次自动重试
5. 数据失败会自动降级到其他数据源
