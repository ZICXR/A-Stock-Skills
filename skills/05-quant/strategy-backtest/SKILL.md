---
name: strategy-backtest
description: A 股量化策略回测。当用户需要对某个交易策略 (均线交叉/MACD/涨停打板等) 进行历史回测时,Claude 应使用此 Skill。支持年化收益、夏普比率、最大回撤、胜率等关键指标计算。
---

# A 股策略回测 Skill

## 何时使用

- 用户需要回测某个交易策略
- 用户需要计算夏普/最大回撤
- 用户需要评估策略表现
- 用户需要对比策略

## 支持的策略

- `ma_cross` - 均线交叉策略
- `macd_cross` - MACD 金叉死叉
- `momentum` - 动量策略
- `limit_up_follow` - 涨停板次日策略

## 提供能力

- `backtest(strategy, code, params)` - 单股回测
- `batch_backtest(strategy, codes)` - 批量回测
- `calc_metrics(equity_curve)` - 计算回测指标

## 使用方式

```bash
python main.py backtest ma_cross --code 000001
python main.py backtest macd_cross --code 600519 --short 5 --long 30
python main.py batch ma_cross --codes 000001,600519,300750
```

## Python API

```python
from skills.05-quant.strategy-backtest.main import (
    backtest, calc_metrics
)

# 回测
result = backtest("ma_cross", "000001", {"short": 5, "long": 20})
# {annual_return, sharpe, max_drawdown, win_rate, trades}

# 批量回测
results = batch_backtest("ma_cross", ["000001", "600519"])
```

## 回测指标

| 指标 | 说明 |
|------|------|
| 年化收益 | 策略年化收益率 |
| 夏普比率 | 风险调整后收益 (>=1 为佳) |
| 最大回撤 | 历史最大亏损幅度 (越小越好) |
| 胜率 | 盈利交易占比 |
| 盈亏比 | 平均盈利/平均亏损 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
