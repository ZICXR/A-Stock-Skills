---
name: stock-basic-info
description: A 股个股基本信息采集。当用户需要获取某只股票的基本信息 (公司名/行业/上市日期/总股本)、实时行情 (现价/涨跌幅/换手率/PE/PB/总市值)、前十大股东、主营业务构成、业绩快报时,Claude 应使用此 Skill。
---

# A 股个股基本信息 Skill

## 何时使用

- 用户询问某只股票的基本信息
- 用户需要股票实时行情
- 用户要求查看股东信息
- 用户询问主营业务/财务摘要

## 提供能力

### 基础信息
- `get_stock_info(code)` - 公司信息 (名/行业/上市日期/股本)
- `get_realtime(code)` - 实时行情 (价/PE/PB/市值)

### 深度信息
- `get_top_holders(code, top_n)` - 前十大股东
- `get_main_business(code)` - 主营业务构成
- `get_financial_summary(code)` - 业绩快报

### 完整信息卡
- `get_stock_card(code)` - 整合基础+实时信息

## 使用方式

```bash
python main.py info 000001
python main.py realtime 000001
python main.py holders 000001 --top 10
python main.py business 000001
python main.py card 000001
```

## Python API

```python
from skills.02-data-collection.stock-basic-info.main import (
    get_stock_info, get_realtime, get_top_holders, get_stock_card
)

# 实时行情
rt = get_realtime("000001")
# {code, name, price, pct_change, volume, pe, pb, total_mv, ...}

# 公司信息
info = get_stock_info("000001")
# {股票简称, 行业, 上市日期, 总股本, ...}

# 完整信息卡
card = get_stock_card("000001")
```

## 实时行情字段

| 字段 | 说明 |
|------|------|
| code/name | 代码/名称 |
| price/change/pct_change | 现价/涨跌额/涨跌幅 |
| open/high/low/pre_close | 开/高/低/昨收 |
| volume/amount | 成交量/额 |
| turnover | 换手率 |
| pe/pb | 市盈率/市净率 |
| total_mv/circ_mv | 总市值/流通市值 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
