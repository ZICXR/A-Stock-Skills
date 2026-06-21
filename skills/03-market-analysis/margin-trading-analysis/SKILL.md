---
name: margin-trading-analysis
description: A 股两融分析。当用户需要查看融资融券余额变化、融资买入额、融券卖出量、两融余额占流通市值比、识别杠杆资金动向 (过热/恐慌/偏多/偏空) 时,Claude 应使用此 Skill。
---

# A 股两融分析 Skill

## 何时使用

- 用户需要查询两融余额
- 用户询问融资买入额
- 用户需要识别杠杆资金动向
- 用户需要分析市场情绪(两融维度)

## 提供能力

- `get_margin_summary()` - 两融总览
- `get_margin_history(days)` - 两融历史
- `get_margin_individual(code)` - 个股两融
- `analyze_margin_sentiment()` - 两融情绪分析

## 使用方式

```bash
python main.py summary
python main.py history --days 30
python main.py stock 000001
python main.py sentiment
```

## Python API

```python
from skills.03-market-analysis.margin-trading-analysis.main import (
    get_margin_summary, get_margin_history, analyze_margin_sentiment
)

# 两融总览
summary = get_margin_summary()
# {融资余额, 融券余额, 融资买入额, ...}

# 历史
hist = get_margin_history(days=30)

# 情绪分析
sent = analyze_margin_sentiment()
# {'level': '偏多', 'change_pct': 1.2, 'signal': '杠杆资金流入'}
```

## 情绪判断

| 变化 | 信号 |
|------|------|
| 余额增加 > 1% | 杠杆资金流入, 偏多 |
| 余额持平 | 中性 |
| 余额减少 > 1% | 杠杆资金流出, 偏空 |
| 余额大幅增加 > 3% | 警惕过热 |
| 余额大幅减少 > 3% | 警惕恐慌 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
