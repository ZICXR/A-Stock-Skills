# astock-utils

> A股通用工具函数库

## 功能模块

- 股票代码处理 (规范化、市场判断)
- 日期工具 (交易日历、日期解析)
- 技术指标 (MA/MACD/KDJ/RSI/BOLL)
- 数据清洗与格式化
- 复权与涨跌停判断

## 快速开始

```python
from skills.01-infra.astock-utils.astock_utils import (
    normalize_stock_code, get_market,
    add_all_indicators, last_n_trade_days,
    fmt_volume, fmt_pct
)

# 代码转换
code = normalize_stock_code("sh600000")  # '600000'
market = get_market("300750")  # 'sz'

# 技术指标
df = add_all_indicators(df)  # 自动加 MA/MACD/KDJ/RSI/BOLL

# 格式化
print(fmt_volume(123456789))  # '1.23亿'
```
