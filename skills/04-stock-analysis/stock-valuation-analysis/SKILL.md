---
name: stock-valuation-analysis
description: A 股个股估值分析。当用户需要深入分析某只股票的估值水平时,Claude 应使用此 Skill。支持 PE/PB/PS 历史分位、PEG 估值、行业相对估值、估值百分位排名。
---

# A 股个股估值分析 Skill

## 何时使用

- 用户需要深度估值分析
- 用户需要 PE/PB 历史分位
- 用户需要 PEG 估值
- 用户需要行业相对估值

## 提供能力

- `get_valuation_metrics(code)` - 估值指标
- `calc_pe_percentile(code)` - PE 历史分位
- `calc_peg(code, growth_rate)` - PEG 估值
- `industry_comparison(code)` - 行业相对估值
- `valuation_rating(code)` - 估值评级

## 使用方式

```bash
python main.py metrics 000001
python main.py percentile 000001
python main.py peg 000001 --growth 15
python main.py compare 000001
python main.py rating 000001
```

## Python API

```python
from skills.04-stock-analysis.stock-valuation-analysis.main import (
    get_valuation_metrics, calc_peg, valuation_rating
)

# 估值指标
v = get_valuation_metrics("000001")
# {pe_ttm, pe_static, pb, ps, ...}

# PEG
peg = calc_peg("000001", growth_rate=15)
# PEG = PE / 增长率

# 估值评级
rating = valuation_rating("000001")
# {'rating': '低估', 'score': 80}
```

## 估值评级标准

| 评级 | 条件 |
|------|------|
| 严重低估 | PE<0 且 PB<1 |
| 低估 | PE<15 或 PEG<0.5 |
| 合理偏低 | PE 15-25 |
| 合理 | PE 25-40 |
| 合理偏高 | PE 40-60 |
| 高估 | PE 60-100 |
| 严重高估 | PE>100 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
