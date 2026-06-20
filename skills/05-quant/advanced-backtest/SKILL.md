---
name: advanced-backtest
description: A 股专业级回测引擎。当用户需要进行更真实的回测 (含交易成本/滑点/印花税/手续费/仓位管理/止盈止损) 时,Claude 应使用此 Skill。支持 T+1、佣金、印花税、滑点等真实交易约束。
---

# A 股专业回测引擎 Skill

## 何时使用

- 用户需要更真实的回测
- 用户需要考虑交易成本
- 用户需要仓位管理
- 用户需要止盈止损
- 用户需要对比不同成本假设

## vs 基础 strategy-backtest

| 特性 | strategy-backtest | advanced-backtest |
|------|-------------------|-------------------|
| 交易成本 | ❌ | ✅ (佣金+印花税+滑点) |
| 仓位管理 | 满仓 | ✅ (固定/金字塔/凯利) |
| 止盈止损 | ❌ | ✅ |
| T+1 规则 | ❌ | ✅ |
| 最大回撤 | 自动 | 自动 + 控制 |
| 分批建仓 | ❌ | ✅ |
| 报告详细度 | 基础 | 详细 |

## 交易成本 (A 股标准)

| 成本 | 费率 | 说明 |
|------|------|------|
| 佣金 | 0.025% (单边, 最低5元) | 券商收取 |
| 印花税 | 0.1% (卖出) | 国家收取 |
| 过户费 | 0.001% | 中登收取 |
| 滑点 | 0.05-0.2% (可配置) | 实际成交偏差 |

## 仓位管理模式

| 模式 | 说明 |
|------|------|
| `all_in` | 满仓 (单只) |
| `equal_split` | 等分建仓 (3次) |
| `pyramid` | 金字塔加仓 |
| `kelly` | 凯利公式 |
| `fixed_fraction` | 固定比例 |

## 使用方式

```bash
# 基础回测
python main.py run --code 000001 --strategy ma_cross

# 自定义成本
python main.py run --code 000001 --strategy ma_cross \
    --commission 0.00025 --slippage 0.001 --stamp_tax 0.001

# 仓位管理
python main.py run --code 000001 --strategy ma_cross \
    --position_mode kelly --stop_loss 0.05 --take_profit 0.15

# 详细报告
python main.py run --code 000001 --strategy turtle --report full

# 多股对比
python main.py compare --codes 000001,600519,300750
```

## Python API

```python
from skills.05-quant.advanced-backtest.main import (
    backtest, run_with_costs
)

# 基础
result = backtest("ma_cross", "000001")

# 含成本
result = run_with_costs(
    strategy="ma_cross",
    code="000001",
    commission=0.00025,
    stamp_tax=0.001,
    slippage=0.001,
    stop_loss=0.05,
    take_profit=0.15,
)
# {total_return, annual_return, sharpe, max_drawdown, win_rate, ...}
```

## 报告字段

| 字段 | 说明 |
|------|------|
| total_return | 总收益率 |
| annual_return | 年化收益 |
| sharpe | 夏普比率 |
| max_drawdown | 最大回撤 |
| win_rate | 胜率 |
| avg_win | 平均盈利 |
| avg_loss | 平均亏损 |
| pl_ratio | 盈亏比 |
| trade_count | 交易次数 |
| total_cost | 总交易成本 |
| net_profit | 净利润 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
