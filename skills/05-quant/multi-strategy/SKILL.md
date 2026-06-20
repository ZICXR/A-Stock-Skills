---
name: multi-strategy
description: A 股多策略组合器。当用户需要使用多种经典量化策略 (双均线/海龟交易/布林带/网格/均值回归等) 时,Claude 应使用此 Skill。支持多策略组合投票、参数优化。
---

# A 股多策略组合器 Skill

## 何时使用

- 用户需要使用多种经典策略
- 用户需要多策略组合投票
- 用户需要参数优化
- 用户需要策略库

## 内置策略 (10 种)

| 策略 | 原理 | 适用 |
|------|------|------|
| `double_ma` | 双均线交叉 | 趋势市 |
| `turtle` | 海龟交易 (20日突破) | 趋势市 |
| `bollinger` | 布林带均值回归 | 震荡市 |
| `grid` | 网格交易 | 震荡市 |
| `mean_reversion` | 均值回归 | 震荡市 |
| `momentum` | 动量 | 强趋势 |
| `rsi` | RSI 反转 | 反弹/回调 |
| `kdj` | KDJ 金叉死叉 | 短线 |
| `macd` | MACD 趋势 | 中线 |
| `breakout` | 突破策略 | 突破行情 |

## 使用方式

```bash
# 单策略回测
python main.py backtest double_ma --code 000001
python main.py backtest turtle --code 600519
python main.py backtest bollinger --code 300750

# 多策略投票
python main.py vote --code 000001 --strategies double_ma,macd,kdj

# 参数优化
python main.py optimize double_ma --code 000001

# 列出所有策略
python main.py list
```

## Python API

```python
from skills.05-quant.multi-strategy.main import (
    list_strategies, run_strategy, multi_strategy_vote
)

# 列出所有策略
strategies = list_strategies()

# 单策略
signals = run_strategy("double_ma", "000001")

# 多策略投票
vote_result = multi_strategy_vote(["double_ma", "macd", "kdj"], "000001")
# {'buy': 2, 'sell': 1, 'signal': '买入'}
```

## 投票规则

- 多策略多数买入 → 强买入
- 多策略多数卖出 → 强卖出
- 票数相等 → 观望

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
