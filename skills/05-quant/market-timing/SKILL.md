---
name: market-timing
description: A 股市场择时模型。当用户需要判断大盘/个股的买卖时机 (趋势择时/反转择时/波动率择时/估值择时) 时,Claude 应使用此 Skill。综合 4 类择时模型给出综合建议。
---

# A 股市场择时模型 Skill

## 何时使用

- 用户需要判断买卖时机
- 用户需要趋势择时
- 用户需要反转择时
- 用户需要波动率择时
- 用户需要多模型综合

## 4 大择时模型

| 模型 | 原理 | 适用 |
|------|------|------|
| 趋势择时 | 均线 + MACD 判断趋势 | 强趋势市 |
| 反转择时 | RSI + 布林带 + 支撑压力 | 震荡市 |
| 波动率择时 | ATR + 历史波动率 | 任何市场 |
| 估值择时 | PE/PB 历史分位 | 长期布局 |

## 提供能力

- `trend_timing(df)` - 趋势择时
- `reversal_timing(df)` - 反转择时
- `volatility_timing(df)` - 波动率择时
- `valuation_timing(code)` - 估值择时
- `comprehensive_timing(code)` - 综合择时

## 使用方式

```bash
# 单模型择时
python main.py trend --code 000001
python main.py reversal --code 000001
python main.py volatility --code 000001
python main.py valuation --code 000001

# 综合择时
python main.py all --code 000001

# 大盘择时 (使用指数)
python main.py market
```

## Python API

```python
from skills.05-quant.market-timing.main import comprehensive_timing

result = comprehensive_timing("000001")
# {
#   'trend': {'signal': '买入', 'score': 2},
#   'reversal': {'signal': '观望', 'score': 0},
#   'volatility': {'signal': '低风险', 'level': 'low'},
#   'valuation': {'signal': '低估', 'level': 'undervalued'},
#   'comprehensive': '买入', 'confidence': 'high'
# }
```

## 综合评分

| 模型 | 权重 |
|------|------|
| 趋势 | 30% |
| 反转 | 25% |
| 波动率 | 20% |
| 估值 | 25% |

## 择时信号

| 综合信号 | 含义 |
|---------|------|
| **强烈买入** | 4 个模型多数买入 + 估值低估 |
| **买入** | 3 个模型买入 |
| **观望** | 信号不一致 |
| **卖出** | 3 个模型卖出 |
| **强烈卖出** | 4 个模型多数卖出 + 估值高估 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
