---
name: market-data-collector
description: A 股大盘数据采集。当用户需要查看主要指数实时行情 (上证/深成/创业板/科创50/沪深300/中证500/中证1000/上证50)、指数历史 K 线、市场广度 (涨跌家数/涨停跌停数)、市场情绪强度评分、最近 N 日两市成交额趋势时,Claude 应使用此 Skill。
---

# A 股大盘数据采集 Skill

## 何时使用

- 用户要求查看主要指数行情
- 用户询问大盘整体表现
- 用户需要市场广度/情绪数据
- 用户询问今日涨停/跌停数量
- 用户需要分析成交额趋势

## 提供能力

### 指数数据
- `get_major_indices()` - 主要指数实时 (上证/深成/创业板/科创50/沪深300/中证500/中证1000/上证50)
- `get_index_kline(symbol, days)` - 指数 K 线
- `get_shanghai_summary()` - 上证指数详细盘口

### 市场广度
- `get_market_breadth()` - 上涨/下跌/平/涨停/跌停家数
- `calc_market_strength(breadth)` - 市场强度评分 (-2 ~ 2)

### 成交数据
- `get_amount_trend(days)` - 两市成交额趋势

## 使用方式

```bash
python main.py indices              # 主要指数
python main.py breadth              # 市场广度
python main.py strength             # 市场强度
python main.py kline 000001 --days 60  # 指数K线
python main.py shanghai             # 上证详细
python main.py amount --days 30     # 成交额趋势
```

## Python API

```python
from skills.02-data-collection.market-data-collector.main import (
    get_major_indices, get_market_breadth, calc_market_strength
)

# 主要指数
df = get_major_indices()
# 包含: 上证/深成/创业板/科创50/沪深300/中证500/中证1000/上证50

# 市场广度
breadth = get_market_breadth()
# {'up': 3421, 'down': 1523, 'limit_up': 56, 'limit_down': 8, ...}

# 强度评分
strength = calc_market_strength(breadth)
# {'score': 0.8, 'level': 'neutral', 'desc': '震荡偏强'}
```

## 指数代码映射

```
000001 上证指数     399001 深证成指
399006 创业板指     000688 科创50
000300 沪深300     000905 中证500
000852 中证1000    000016 上证50
```

## 强度评分规则

| 上涨比例 | 等级 | 描述 |
|---------|------|------|
| < 30% | 极度弱势 | 极弱 |
| 30-50% | 弱势 | 弱势震荡 |
| 50-70% | 偏强 | 震荡偏强 |
| > 70% | 强势 | 强势 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
