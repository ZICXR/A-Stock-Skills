---
name: risk-management
description: A 股风险管理。当用户需要计算组合风险指标 (VaR/最大回撤/夏普/波动率)、仓位管理建议、止损止盈设置时,Claude 应使用此 Skill。
---

# A 股风险管理 Skill

## 何时使用

- 用户需要计算 VaR
- 用户需要最大回撤
- 用户需要仓位管理
- 用户需要止损止盈建议

## 提供能力

- `calc_var(returns, confidence)` - VaR 计算
- `calc_max_drawdown(equity_curve)` - 最大回撤
- `calc_sharpe(returns, rf)` - 夏普比率
- `position_suggestion(capital, risk_per_trade, stop_loss)` - 仓位建议
- `stop_loss_strategy(code, days)` - 止损策略

## 使用方式

```bash
python main.py var 000001 --days 90
python main.py position --capital 100000 --risk 0.02 --stop 0.05
python main.py stop 000001 --strategy atr
```

## Python API

```python
from skills.05-quant.risk-management.main import (
    calc_var, calc_max_drawdown, position_suggestion
)

# VaR
var = calc_var(returns, confidence=0.95)

# 最大回撤
mdd = calc_max_drawdown(equity_curve)

# 仓位建议
pos = position_suggestion(capital=100000, risk_per_trade=0.02, stop_loss=0.05)
# {shares, position_value, risk_amount}
```

## 仓位管理规则

- 单笔风险 <= 总资金 2%
- 止损 5% 时, 仓位 40%
- 止损 10% 时, 仓位 20%
- 止损 2% 时, 仓位 100% (满仓)

## 风险等级

| VaR (95%) | 等级 |
|-----------|------|
| < 1% | 低风险 |
| 1-3% | 中低风险 |
| 3-5% | 中等风险 |
| 5-10% | 高风险 |
| > 10% | 极高风险 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
