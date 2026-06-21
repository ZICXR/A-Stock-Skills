---
name: backtest
description: A 股策略回测 (3合1统一版)。当用户需要对某个交易策略进行历史回测时,Claude 应使用此 Skill。支持 3 种回测模式: basic (基础) / advanced (含交易成本+仓位管理+止损) / multi-signal (多信号组合 + 自动优化)。是 strategy-backtest + advanced-backtest + multi-signal-backtest 合并的统一版本。
---

# A 股策略回测 Skill (统一版)

## 何时使用

- 用户需要回测策略
- 用户需要含交易成本的真实回测
- 用户需要多信号组合回测
- 用户需要自动优化信号组合

## 3 大回测模式

| 模式 | 适用 | 特点 |
|------|------|------|
| `basic` | 快速验证 | 满仓, 无成本 |
| `advanced` | 实战评估 | 含佣金/印花税/滑点/仓位/止损 |
| `multi-signal` | 选股策略 | 多信号 AND 组合 + 自动优化 |

## 使用方式

```bash
# 基础
python main.py basic --code 000001 --strategy ma_cross

# 专业 (含成本)
python main.py advanced --code 000001 --strategy ma_cross \
    --position-mode kelly --stop-loss 0.05 --take-profit 0.15

# 多信号
python main.py multi-signal \
    --signals "macd_golden,above_ma20,volume_break" --hold-days 5

# 多信号自动优化
python main.py multi-signal --optimize \
    --candidates "macd_golden,above_ma20,volume_break,rsi_oversold,kdj_golden"

# 批量对比
python main.py batch --codes 000001,600519,300750
```

## Python API

```python
from skills.05-quant.backtest.main import (
    basic_backtest, advanced_backtest, multi_signal_backtest
)

# 基础
result = basic_backtest("ma_cross", "000001")

# 专业
result = advanced_backtest("ma_cross", "000001",
                          stop_loss=0.05, take_profit=0.15)

# 多信号
result = multi_signal_backtest(["macd_golden", "above_ma20"], hold_days=5)
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```

## 合并历史

本 Skill 由原 `strategy-backtest` + `advanced-backtest` + `multi-signal-backtest` 合并而成, 节省 2 个 Skill。
