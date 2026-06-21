---
name: portfolio-report
description: A 股持仓报告生成。当用户需要生成完整持仓分析报告 (5 大部分: 总览/盈亏明细/行业分布/风险敞口/调仓建议) 时,Claude 应使用此 Skill。与 watchlist-monitor 配合, 形成"监控+报告"完整闭环。
---

# A 股持仓报告 Skill

## 何时使用

- 用户需要查看持仓盈亏
- 用户需要行业分布分析
- 用户需要风险敞口评估
- 用户需要调仓建议
- 用户需要周度/月度持仓总结

## 报告内容

1. 📊 **总览** - 总市值/总盈亏/总收益率
2. 💰 **盈亏明细** - 每只股票的持仓盈亏
3. 🏭 **行业分布** - 持仓的行业分布
4. ⚠️ **风险敞口** - 集中度/单股最大亏损
5. 🎯 **调仓建议** - 风险点/优化建议
6. 📈 **业绩对比** - 与沪深 300 对比

## 配置文件

编辑 `portfolio.yaml`:

```yaml
name: 我的持仓
initial_capital: 100000  # 初始资金 (可选)

positions:
  - code: "000001"
    cost: 12.50
    shares: 1000
  - code: "600519"
    cost: 1650.00
    shares: 100
  - code: "300750"
    cost: 220.00
    shares: 500
  - code: "000858"
    cost: 145.00
    shares: 200

benchmark: "000300"  # 对标基准, 默认沪深300
```

## 使用方式

```bash
# 初始化模板
python main.py init

# 单次报告
python main.py report --config portfolio.yaml

# 简化盈亏查看
python main.py pnl --config portfolio.yaml

# 行业分布
python main.py sectors --config portfolio.yaml

# 调仓建议
python main.py advice --config portfolio.yaml
```

## Python API

```python
from skills.05-reports.portfolio-report.main import (
    load_portfolio, generate_report
)

# 加载持仓
positions = load_portfolio("./portfolio.yaml")

# 生成报告
report = generate_report("./portfolio.yaml", save=True)
```

## 输出示例

```
📊 持仓总览 (2024-12-30)
================================
总市值:    123,456 元
总成本:    100,000 元
总盈亏:    +23,456 元 (+23.46%)
沪深300:   +5.32%
跑赢基准:  +18.14%
```

## 调仓建议规则

| 情况 | 建议 |
|------|------|
| 单股仓位 > 30% | 减仓分散 |
| 单股亏损 > 20% | 评估基本面 |
| 行业集中度 > 50% | 跨行业配置 |
| 整体回撤 > 15% | 降低仓位 |
| 持仓 > 10 只 | 评估是否过于分散 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
pyyaml>=5.4.0
```
