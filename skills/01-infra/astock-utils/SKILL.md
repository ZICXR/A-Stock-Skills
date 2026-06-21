---
name: astock-utils
description: A 股通用工具函数库。当 Claude 需要处理股票代码转换 (如 "sh600000" → "600000")、判断市场归属 (沪/深/北)、解析交易日历、计算技术指标 (MA/MACD/KDJ/RSI/BOLL)、格式化数字 (成交量/金额/百分比) 时,应使用此 Skill。这是其他 Skill 的基础工具库。
---

# A 股通用工具 Skill

## 何时使用

- 处理股票代码格式转换
- 判断股票所属市场
- 计算技术指标
- 格式化输出
- 解析交易日

## 提供能力

### 代码处理
- `normalize_code(code)` - 规范化代码 (统一 6 位)
- `get_market(code)` - 判断市场 (sh/sz/bj)
- `is_cyb(code)` - 是否创业板
- `is_kcb(code)` - 是否科创板
- `is_bj(code)` - 是否北交所
- `is_st(name)` - 是否 ST 股

### 日期工具
- `today_str()` - 今天
- `parse_date(s)` - 解析日期
- `last_n_trade_days(n)` - 最近 N 个交易日
- `date_str(dt)` - 日期转字符串

### 技术指标 (输入: DataFrame, 输出: 增加列后的 DataFrame)
- `add_ma(df, [5,10,20,60])` - 均线
- `add_macd(df)` - MACD
- `add_kdj(df)` - KDJ
- `add_rsi(df)` - RSI
- `add_boll(df)` - 布林带
- `add_all_indicators(df)` - 一次性添加所有

### 格式化
- `fmt_volume(v)` - 成交量 (1.23亿)
- `fmt_money(v)` - 金额
- `fmt_pct(v)` - 百分比

## 使用方式

```bash
# 命令行
python main.py normalize-code sh600000
python main.py market 300750
python main.py is-cyb 300750
python main.py trade-days 5
```

## Python API

```python
from skills.01-infra.astock-utils.main import (
    normalize_code, get_market, add_all_indicators,
    fmt_volume, fmt_pct
)

code = normalize_code("sh600000")  # "600000"
market = get_market("300750")  # "sz"
df_with_indicators = add_all_indicators(df)
print(fmt_volume(123456789))  # "1.23亿"
```

## 依赖

```
pandas>=1.5.0
numpy>=1.22.0
akshare>=1.12.0  # 交易日历
```
