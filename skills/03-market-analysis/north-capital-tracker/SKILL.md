---
name: north-capital-tracker
description: A 股北向资金追踪。当用户需要查看沪股通/深股通实时资金流入流出、北向资金历史趋势、北向资金重仓股、北向资金异动信号时,Claude 应使用此 Skill。
---

# A 股北向资金追踪 Skill

## 何时使用

- 用户询问北向资金动态
- 用户需要北向资金实时数据
- 用户询问北向重仓股
- 用户需要北向资金异动信号

## 提供能力

- `get_north_realtime()` - 北向资金今日实时
- `get_north_history(days)` - 北向资金历史
- `get_north_holdings(top_n)` - 北向重仓股
- `detect_north_signal()` - 异动信号识别

## 使用方式

```bash
python main.py realtime
python main.py history --days 30
python main.py holdings --top 20
python main.py signal
```

## Python API

```python
from skills.03-market-analysis.north-capital-tracker.main import (
    get_north_realtime, get_north_history, detect_north_signal
)

# 实时北向
nb = get_north_realtime()
# {'沪股通': 5.2亿, '深股通': 3.1亿, '合计': 8.3亿}

# 历史
hist = get_north_history(days=30)

# 异动信号
signal = detect_north_signal()
# {'signal': '大幅流入', 'amount': 50e8}
```

## 异动信号阈值

| 信号 | 阈值 |
|------|------|
| 大幅流入 | > 50 亿 |
| 明显流入 | 20-50 亿 |
| 小幅流入 | 0-20 亿 |
| 持平 | 0 |
| 流出 | < 0 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
