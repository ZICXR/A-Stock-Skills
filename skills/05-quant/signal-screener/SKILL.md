---
name: signal-screener
description: A 股股票信号筛选器。当用户需要按特定条件筛选股票 (MACD 金叉 + 站上 20 日均线 + 放量 等) 时,Claude 应使用此 Skill。支持组合条件、技术形态筛选、自定义选股策略。
---

# A 股信号筛选器 Skill

## 何时使用

- 用户需要按条件选股
- 用户需要技术形态筛选
- 用户需要自定义选股策略
- 用户需要批量扫描信号

## 内置条件 (技术信号)

- `ma_cross` - 均线金叉
- `macd_golden` - MACD 金叉
- `macd_death` - MACD 死叉
- `above_ma20` - 站上 20 日均线
- `above_ma60` - 站上 60 日均线
- `volume_break` - 放量 (量比 > 1.5)
- `volume_shrink` - 缩量 (量比 < 0.7)
- `rsi_oversold` - RSI 超卖 (< 30)
- `rsi_overbought` - RSI 超买 (> 70)
- `kdj_golden` - KDJ 金叉
- `limit_up` - 涨停
- `new_high` - N 日新高

## 提供能力

- `screen(conditions, top_n)` - 条件筛选
- `add_condition(df, condition)` - 单条件判断
- `combine_signals(results)` - 多条件组合 (AND/OR)

## 使用方式

```bash
# 单条件
python main.py screen --signal macd_golden --top 30

# 多条件 (AND)
python main.py screen --signals "macd_golden,above_ma20,volume_break" --top 30

# 多条件 (OR)
python main.py screen --signals "limit_up,rsi_oversold" --mode or --top 30
```

## Python API

```python
from skills.05-quant.signal-screener.main import screen

# 组合条件筛选
result = screen(
    conditions=["macd_golden", "above_ma20", "volume_break"],
    mode="and",  # and / or
    top_n=30,
)
# [{'code', 'name', 'price', 'pct_change', 'signals': [...]}]
```

## 常用组合

### 短线强势股
- macd_golden + above_ma20 + volume_break

### 抄底反弹
- rsi_oversold + kdj_golden + volume_break

### 突破新高
- new_high_60 + above_ma60 + volume_break

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
