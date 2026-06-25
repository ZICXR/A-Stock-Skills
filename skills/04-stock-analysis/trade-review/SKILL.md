---
name: trade-review
description: A 股交割单分析诊断工具。当用户说"分析我的交割单"、"看看我的操作问题"、"交易复盘"、"我的操作哪里有问题"、"帮我诊断交易"时，Claude 应使用此 Skill。支持多种券商交割单格式（CSV/Excel）自动识别，从盈亏统计、持仓周期、操作行为、仓位管理、买卖时机 5 个维度诊断问题，结合行情数据 + AI 信号给出改进建议。**核心价值: 让交割单变成教科书**。
---

# 交割单操作分析诊断 Skill

## 何时使用

- 用户有券商交割单（CSV/Excel），想分析自己的操作问题
- 用户想知道"我到底亏在哪里"、"我的交易习惯有什么问题"
- 用户想做交易复盘，但不是简单的盈亏统计，而是行为诊断
- 用户想对比 AI 建议 vs 实际操作

## 核心理念

```
交割单 → 解析 → 配对 → 5 维诊断 → 建议
                                    ↓
                     不只是"赚了还是亏了"
                     而是"为什么亏、怎么改"
```

## 提供能力

### 交割单解析
- `parse_settlement(path)` - 自动识别券商格式，解析为标准 DataFrame
- `detect_format(df)` - 识别券商格式（华泰/中信/东财/通用）

### 交易配对
- `pair_trades(df)` - FIFO 配对，生成完整交易轮次

### 5 维分析
- `analyze_pnl(trades)` - 盈亏统计（胜率/盈亏比/最大盈亏）
- `analyze_holding_period(trades)` - 持仓周期分析
- `analyze_behavior(trades, klines)` - 操作行为诊断（追涨杀跌/坐电梯/频繁交易）
- `analyze_position(trades)` - 仓位管理分析
- `analyze_timing(trades, klines)` - 买卖时机分析（结合行情）

### AI 信号对比
- `compare_with_ai(trades)` - 对比 trade-journal 中的 AI 建议 vs 实际操作

### 综合
- `analyze_trades(path, fetch_kline)` - 一键全流程分析
- `generate_report(result)` - 生成 Markdown 诊断报告
- `generate_suggestions(result)` - 生成改进建议

## 使用方式

```bash
# 分析交割单
python main.py analyze path/to/settlement.csv

# 指定日期范围
python main.py analyze settlement.csv --from 2025-01-01 --to 2025-12-31

# 结合行情分析买卖点（需要网络，较慢）
python main.py analyze settlement.csv --kline

# 保存报告
python main.py analyze settlement.csv --save

# 查看支持的字段
python main.py fields
```

## Python API

```python
from skills.04-stock-analysis.trade-review.main import (
    parse_settlement, analyze_trades, generate_report
)

# 解析交割单
df = parse_settlement("settlement.csv")

# 全流程分析
result = analyze_trades(df, fetch_kline=False)

# 生成报告
report = generate_report(result)
print(report)
```

## 5 维诊断

| 维度 | 分析内容 | 诊断问题 |
|------|---------|---------|
| 盈亏统计 | 胜率/盈亏比/收益分布 | 赚小亏大？胜率太低？ |
| 持仓周期 | 平均天数/盈利vs亏损对比 | 拿不住？套牢装死？ |
| 操作行为 | 追涨杀跌/坐电梯/频繁交易 | 管不住手？ |
| 仓位管理 | 集中度/加减仓模式 | 一把梭？ |
| 买卖时机 | 均线位置/支撑压力/对比大盘 | 买在山顶？ |

## 操作问题诊断规则

| 问题 | 判定条件 | 建议 |
|------|---------|------|
| 赚小亏大 | 盈亏比 < 1 | 设定止损线，让利润奔跑 |
| 胜率过低 | 胜率 < 40% | 减少出手次数，提高选股质量 |
| 频繁交易 | 平均持仓 < 3 天 | 降低交易频率，手续费侵蚀利润 |
| 坐电梯 | 曾盈利 >5% 但亏损卖出 > 3 次 | 设定动态止盈（如回撤 3% 出场） |
| 不止损 | 最大单笔亏损 > 20% | 严格执行止损（如 -7%） |
| 集中度过高 | 单股仓位 > 50% | 分散到 3-5 只，单股不超 30% |
| 追涨杀跌 | 追涨比例 > 50% | 尝试回调买入，避免情绪化 |
| 跑输大盘 | 收益率 vs 沪深300 < -10% | 考虑指数基金或降低操作频率 |

## 输出示例

```markdown
📊 交割单操作诊断报告
========================================
📅 分析区间: 2025-01-01 ~ 2025-06-30
💰 总盈亏: -12,500 元 (-8.3%)
🎯 胜率: 35% (7/20)
⚖️ 盈亏比: 0.6 (赚小亏大)

🔍 操作问题诊断:
1. ❌ 赚小亏大 - 平均盈利 +3.2%, 平均亏损 -5.3%
2. ❌ 坐电梯 - 601991 曾盈利 8% 但亏损 3% 卖出
3. ❌ 频繁交易 - 平均持仓 2.1 天，交易 20 笔
4. ⚠️ 不止损 - 300750 亏损 22% 才卖出

💡 改进建议:
1. 设定止损线: 建议 -7% 无条件止损
2. 动态止盈: 盈利 >5% 后，回撤 3% 则出场
3. 降低频率: 每周最多 1-2 笔交易
4. 仓位控制: 单股不超 30%
========================================
```

## 支持的交割单格式

- 华泰证券（默认格式）
- 中信证券
- 国泰君安
- 招商银行证券
- 东方财富
- 通用 CSV/Excel（自动识别列名）

## 依赖

```
pandas>=1.5.0
openpyxl>=3.0.0
akshare>=1.12.0    # 可选，用于拉取行情分析买卖点
```

## 关联 Skill

- `astock-data-source` - 拉取 K 线分析买卖时机
- `astock-utils` - 代码标准化、日期解析
- `trade-journal` - 对比 AI 信号 vs 实际操作
- `stock-technical-analysis` - 技术分析支撑压力位
