---
name: screener
description: A 股股票筛选器 (内置信号 + 自定义条件 2合1)。当用户需要按条件筛选股票时,Claude 应使用此 Skill。支持 12 种内置技术信号 (ma_cross/macd/above_ma/volume/rsi/kdj 等) + 任意自定义条件 (PE/PB/ROE/市值等, 9 种操作符) + AND/OR 组合 + 4 个内置策略模板 (value/growth/small_cap/momentum)。
---

# A 股股票筛选器 Skill (统一版)

## 何时使用

- 用户需要技术信号筛选
- 用户需要自定义条件筛选
- 用户需要多条件 AND/OR 组合
- 用户需要保存常用策略

## 提供能力

- **内置信号**: 12 种 (ma_cross/macd/above_ma/volume/rsi/kdj 等)
- **自定义条件**: 11 字段 × 9 操作符
- **AND/OR 组合**
- **策略保存**: YAML 文件复用

## 使用方式

```bash
# 内置信号
python main.py screen --signals "macd_golden,above_ma20" --mode and

# 自定义条件
python main.py screen --where "pe<20" --where "roe>15"

# 组合
python main.py screen --where "pe<20" --signals "above_ma20,volume_break"

# 内置策略
python main.py screen --strategy value

# 列出策略
python main.py list
```

## Python API

```python
from skills.05-quant.screener.main import screen

# 自定义 + 信号
result = screen(
    conditions=[{"field": "pe", "op": "<", "value": 20}],
    signals=["macd_golden", "above_ma20"],
    mode="and",
    top_n=30,
)
```

## 内置信号

`ma_cross` / `macd_golden` / `macd_death` / `above_ma20` / `above_ma60` /
`volume_break` / `volume_shrink` / `rsi_oversold` / `rsi_overbought` /
`kdj_golden` / `new_high_60` / `limit_up`

## 字段

`pe` / `pb` / `ps` / `total_mv` / `circ_mv` / `roe` / `pct_change` /
`turnover` / `volume_ratio` / `price` / `change_5d` / `change_20d`

## 操作符

`>` `<` `>=` `<=` `==` `!=` `between(a,b)` `in` `not in`

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
pyyaml>=5.4.0
```

## 合并历史

本 Skill 由原 `signal-screener` + `stock-screener-custom` 合并而成, 节省 1 个 Skill。
