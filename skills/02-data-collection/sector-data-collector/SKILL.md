---
name: sector-data-collector
description: A 股板块数据采集。当用户需要查看行业板块行情、概念板块行情、板块资金流入流出、板块成分股时,Claude 应使用此 Skill。覆盖申万行业、概念板块、地域板块等多个维度。
---

# A 股板块数据采集 Skill

## 何时使用

- 用户要求查看行业板块涨跌
- 用户询问概念板块热点
- 用户需要板块资金流数据
- 用户需要查看某板块的成分股

## 提供能力

### 板块行情
- `get_industry_sectors()` - 行业板块行情
- `get_concept_sectors()` - 概念板块行情
- `get_sector_stocks(code, type)` - 板块成分股

### 资金流
- `get_sector_fund_flow(period)` - 行业资金流 (今日/3日/5日/10日)
- `get_concept_fund_flow(period)` - 概念资金流

## 使用方式

```bash
python main.py industry
python main.py concept --top 20
python main.py industry-flow --period 5日
python main.py concept-flow --period 今日
python main.py stocks BK0420 --type industry
```

## Python API

```python
from skills.02-data-collection.sector-data-collector.main import (
    get_industry_sectors, get_concept_sectors,
    get_sector_fund_flow, get_sector_stocks
)

# 行业板块
industries = get_industry_sectors()

# 资金流入榜
flow = get_sector_fund_flow("今日")
top_inflow = flow.nlargest(10, "main_net")

# 成分股
stocks = get_sector_stocks("BK0420", "industry")
```

## 资金流周期

- 今日 (当日)
- 3日 (3 日累计)
- 5日 (5 日累计)
- 10日 (10 日累计)

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
