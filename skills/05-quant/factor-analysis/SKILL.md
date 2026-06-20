---
name: factor-analysis
description: A 股多因子选股分析。当用户需要进行多因子选股 (动量/价值/质量/成长/波动) 时,Claude 应使用此 Skill。支持 IC 计算、因子合成、因子有效性评估、Rank IC 等专业量化指标。
---

# A 股多因子分析 Skill

## 何时使用

- 用户需要多因子选股
- 用户需要因子有效性评估
- 用户需要因子 IC 计算
- 用户需要量化选股模型

## 因子库 (内置)

| 因子 | 类别 | 说明 |
|------|------|------|
| momentum_20 | 动量 | 20日涨跌幅 |
| momentum_60 | 动量 | 60日涨跌幅 |
| value_pe | 价值 | PE 倒数 |
| value_pb | 价值 | PB 倒数 |
| quality_roe | 质量 | ROE |
| growth_revenue | 成长 | 营收增长率 |
| growth_profit | 成长 | 净利润增长率 |
| volatility_20 | 波动 | 20日波动率 |
| turnover_20 | 流动性 | 20日均换手率 |

## 提供能力

- `calc_factor(stocks, factor_name)` - 计算单因子
- `calc_all_factors(stocks)` - 计算全因子
- `factor_ic(factor, returns)` - 计算 IC
- `factor_quantile(factor, n)` - 因子分组
- `multi_factor_score(factors)` - 多因子合成

## 使用方式

```bash
python main.py calc 000001 momentum_20
python main.py ic --factor momentum_20
python main.py score --top 20
```

## Python API

```python
from skills.05-quant.factor-analysis.main import (
    calc_factor, factor_ic, multi_factor_score
)

# 单因子
mom = calc_factor("000001", "momentum_20")

# 多因子评分
scores = multi_factor_score(stocks)
```

## IC (Information Coefficient)

衡量因子预测能力:
- |IC| > 0.05: 强有效
- 0.02 < |IC| < 0.05: 有效
- |IC| < 0.02: 弱有效

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
