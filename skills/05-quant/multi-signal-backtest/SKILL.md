---
name: multi-signal-backtest
description: A 股选股组合回测。当用户需要测试多个技术信号 (如 MA5 金叉 + MACD 金叉 + 放量) 组合的历史表现时,Claude 应使用此 Skill。支持 N 信号 AND/OR 组合、命中后持仓 N 日、调仓频率,生成组合胜率和年化收益。
---

# A 股选股组合回测 Skill

## 何时使用

- 用户需要测试信号组合
- 用户需要选股策略回测
- 用户需要评估联合信号
- 用户需要对比不同信号组合

## vs strategy-backtest

| 维度 | strategy-backtest | multi-signal-backtest |
|------|-------------------|----------------------|
| 信号类型 | 单一策略 | 多信号 AND/OR 组合 |
| 选股范围 | 单股 | 全市场扫描 |
| 调仓 | 持续持仓 | N 日调仓 |
| 评估 | 收益率 | 命中率 + 收益 |

## 核心概念

- **信号组合**: `signal_a AND signal_b AND signal_c`
- **持仓周期**: 命中后持有 N 日卖出
- **调仓频率**: 每日扫描 / 每周调仓
- **收益计算**: 持有 N 日的收益率

## 使用方式

```bash
# 简单组合
python main.py backtest \
    --signals "macd_golden,above_ma20,volume_break" \
    --hold-days 5 \
    --start 2024-01-01 \
    --end 2024-12-30

# 加载策略文件
python main.py backtest --strategy combo.yaml

# 优化信号组合
python main.py optimize \
    --candidate "macd_golden,above_ma20,volume_break,rsi_oversold,kdj_golden" \
    --top 5
```

## Python API

```python
from skills.05-quant.multi-signal-backtest.main import (
    backtest_combo, optimize_combo
)

# 组合回测
result = backtest_combo(
    signals=["macd_golden", "above_ma20", "volume_break"],
    hold_days=5,
    start="2024-01-01",
    end="2024-12-30",
)
# {hit_count, win_rate, avg_return, total_return, ...}

# 优化 (尝试所有 N 信号组合)
results = optimize_combo(
    candidates=["macd_golden", "above_ma20", "volume_break", "rsi_oversold"],
    top_n=5,
)
```

## 输出示例

```
=== 多信号组合回测 ===
信号: macd_golden + above_ma20 + volume_break (AND)
持仓周期: 5 日
回测区间: 2024-01-01 ~ 2024-12-30
命中次数: 28 次
命中率: 12.5%
平均收益: +3.2%
胜率: 67.8%
累计收益: +89.6%
年化收益: +89.6%
```

## 内置信号

- `ma_cross` / `macd_golden` / `macd_death`
- `above_ma20` / `above_ma60`
- `volume_break` / `volume_shrink`
- `rsi_oversold` / `rsi_overbought`
- `kdj_golden` / `limit_up` / `new_high_60`

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
