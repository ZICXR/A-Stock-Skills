---
name: event-driven
description: A 股事件驱动策略。当用户需要基于事件 (财报披露/分红送股/限售解禁/股东大会/重大合同) 进行投资决策时,Claude 应使用此 Skill。支持事件识别、事件后股价表现分析、事件日历。
---

# A 股事件驱动策略 Skill

## 何时使用

- 用户需要关注财报披露
- 用户需要分红送股事件
- 用户需要限售解禁事件
- 用户需要事件后股价表现分析
- 用户需要事件日历

## 支持的事件类型

| 事件 | 含义 | 数据源 |
|------|------|--------|
| `earnings` | 财报/业绩快报/业绩预告 | 财报披露 |
| `dividend` | 分红/送股/转增 | 公告 |
| `unlock` | 限售解禁 | 解禁公告 |
| `shareholder` | 股东大会 | 公告 |
| `major_contract` | 重大合同/中标 | 公告 |
| `buyback` | 股份回购 | 公告 |
| `placement` | 增发/配股 | 公告 |

## 提供能力

- `get_event_calendar(days)` - 事件日历
- `analyze_event_impact(event_type)` - 事件影响分析
- `earnings_surprise_strategy()` - 业绩超预期策略
- `dividend_yield_screen()` - 高分红筛选
- `unlock_pressure()` - 解禁压力分析

## 使用方式

```bash
# 事件日历
python main.py calendar --days 30

# 业绩披露
python main.py earnings --days 7

# 分红送股
python main.py dividend --days 30

# 解禁
python main.py unlock --days 30

# 业绩超预期分析
python main.py surprise --code 000001

# 高分红筛选
python main.py high-dividend --top 30
```

## Python API

```python
from skills.05-quant.event-driven.main import (
    get_event_calendar, earnings_surprise, high_dividend_screen
)

# 事件日历
events = get_event_calendar(days=30)

# 业绩超预期
surprise = earnings_surprise("000001")

# 高分红
high_div = high_dividend_screen(top_n=30)
```

## 事件投资逻辑

### 业绩超预期
- 业绩 > 预期 20% → 上涨概率大
- 业绩 < 预期 20% → 下跌风险大
- 公告日次日表现最关键

### 分红送股
- 高股息率 (>=3%) → 长线价值
- 送股 > 5股 → 短期炒作
- 分红率 > 50% → 优质公司

### 限售解禁
- 解禁比例 > 10% → 抛压风险
- 解禁后 1 个月表现最差
- 关注股东减持意向

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
