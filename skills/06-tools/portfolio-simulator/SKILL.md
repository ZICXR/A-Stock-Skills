---
name: portfolio-simulator
description: A 股虚拟持仓模拟器。当用户需要虚拟交易 (不实际下单, 仅记录) 时,Claude 应使用此 Skill。支持买入/卖出记录、持仓跟踪、盈亏统计、交易历史、对标基准。
---

# A 股虚拟持仓模拟器 Skill

## 何时使用

- 用户需要虚拟交易
- 用户需要策略验证
- 用户需要学习股票交易
- 用户需要跟踪虚拟仓位

## vs portfolio-report 区别

| 特性 | portfolio-report | portfolio-simulator |
|------|------------------|---------------------|
| 数据源 | 真实持仓 | 虚拟交易 |
| 可买入/卖出 | ❌ | ✅ |
| 交易历史 | ❌ | ✅ |
| 策略回测 | ❌ | ✅ |
| 复盘 | 静态 | 动态 |

## 使用方式

### 1. 初始化

```bash
python main.py init --name "策略A" --capital 100000
```

### 2. 买入

```bash
python main.py buy --code 000001 --price 12.50 --shares 1000 --reason "金叉"
```

### 3. 卖出

```bash
python main.py sell --code 000001 --price 13.50 --reason "止盈"
```

### 4. 查看持仓

```bash
python main.py positions
```

### 5. 交易历史

```bash
python main.py history
```

### 6. 业绩统计

```bash
python main.py stats
```

## Python API

```python
from skills.06-tools.portfolio-simulator.main import (
    init, buy, sell, get_positions, get_history
)

# 初始化
init(name="策略A", capital=100000)

# 买入
buy(code="000001", price=12.50, shares=1000, reason="金叉买入")

# 卖出
sell(code="000001", price=13.50, reason="止盈")

# 持仓
positions = get_positions()
```

## 数据存储

- 默认: `~/.astock_skills/simulations/<name>.json`
- 可指定其他路径

## 业绩指标

- 总收益率
- 年化收益
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比
- 与基准对比 (默认沪深300)

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
