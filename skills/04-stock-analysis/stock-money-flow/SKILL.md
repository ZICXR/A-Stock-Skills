---
name: stock-money-flow
description: A 股个股资金流向深度分析。当用户需要分析某只股票的资金流入流出 (大单/中单/小单)、主力净流入趋势、买卖盘口数据时,Claude 应使用此 Skill。
---

# A 股个股资金流分析 Skill

## 何时使用

- 用户需要个股资金流分析
- 用户需要主力动向
- 用户需要买卖盘口数据
- 用户需要大单/小单拆分

## 提供能力

- `get_money_flow(code, days)` - 个股资金流历史
- `analyze_main_force(code)` - 主力动向
- `get_buy_sell(code)` - 买卖盘口
- `money_flow_signal(code)` - 资金信号

## 使用方式

```bash
python main.py flow 000001 --days 10
python main.py main 000001
python main.py buy-sell 000001
python main.py signal 000001
```

## Python API

```python
from skills.04-stock-analysis.stock-money-flow.main import (
    get_money_flow, analyze_main_force, money_flow_signal
)

# 资金流历史
flow = get_money_flow("000001", days=10)

# 主力动向
main = analyze_main_force("000001")
# {'main_net_5d': 5.2e8, 'main_net_10d': 8.1e8, 'trend': '流入'}

# 资金信号
sig = money_flow_signal("000001")
# {'signal': '主力大幅流入', 'score': 2}
```

## 资金分类

- 主力 = 超大单 + 大单
- 超大单 >= 100 万
- 大单 20-100 万
- 中单 4-20 万
- 小单 < 4 万

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
