---
name: capital-flow-analysis
description: A 股资金流向分析。当用户需要查看大盘资金流 (主力/超大单/大单/中单/小单 5 档分类)、北向资金 (沪股通/深股通)、个股资金流向、识别资金信号 (主力大幅流入/流入/流出) 时,Claude 应使用此 Skill。
---

# A 股资金流向分析 Skill

## 何时使用

- 用户需要查看大盘资金流
- 用户询问北向资金动态
- 用户要求个股资金流
- 用户需要识别资金信号
- 用户询问"主力是否在买入/卖出"

## 提供能力

### 大盘资金
- `get_market_fund_flow()` - 大盘整体资金 (沪/深)
- `analyze_fund_signal(flow_df)` - 资金信号识别

### 北向资金
- `get_north_bound_today()` - 北向资金今日实时
- `get_north_bound_flow(days)` - 北向资金历史

### 个股资金
- `get_stock_fund_flow(code, days)` - 个股资金流

## 使用方式

```bash
python main.py market                # 大盘资金流
python main.py north-today           # 北向今日
python main.py north-hist --days 30  # 北向历史
python main.py stock 000001 --days 10  # 个股资金
```

## Python API

```python
from skills.03-market-analysis.capital-flow-analysis.main import (
    get_market_fund_flow, get_north_bound_today, get_stock_fund_flow
)

# 大盘资金流
mf = get_market_fund_flow()
# {'上证': {...}, '深证': {...}}

# 北向资金
nb = get_north_bound_today()
nb_hist = get_north_bound_flow(days=30)

# 个股资金
flow = get_stock_fund_flow("000001", days=10)
```

## 资金分类

| 类别 | 单笔金额 |
|------|----------|
| 主力 | 主力 = 超大单 + 大单 |
| 超大单 | >= 100 万 |
| 大单 | 20-100 万 |
| 中单 | 4-20 万 |
| 小单 | < 4 万 |

## 资金信号

| 信号 | 条件 |
|------|------|
| 主力大幅流入 | 主力 + 超大单均流入 |
| 主力净流入 | 仅主力流入 |
| 主力净流出 | 仅主力流出 |
| 主力大幅流出 | 主力 + 超大单均流出 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
