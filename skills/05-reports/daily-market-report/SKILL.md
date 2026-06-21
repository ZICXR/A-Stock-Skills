---
name: daily-market-report
description: A 股每日复盘报告生成。当用户需要生成每日 A 股复盘报告 (Markdown 格式, 5 大部分: 大盘表现/板块热点/涨停板/资金流向/龙虎榜) 时,Claude 应使用此 Skill。整合所有 Layer 1-4 数据,自动保存为 daily_report_YYYY-MM-DD.md。
---

# A 股每日复盘报告 Skill

## 何时使用

- 用户要求生成每日 A 股复盘报告
- 用户需要盘后市场总结
- 用户需要完整的全市场分析报告
- 用户需要 Markdown 格式的分析报告

## 报告结构

报告包含 5 大部分:

1. 📊 **大盘表现** - 主要指数/市场广度/趋势研判
2. 🔥 **板块热点** - 行业涨幅榜/资金榜/主线识别
3. 🚀 **涨停板** - 涨停统计/连板梯队/原因分布/Top10
4. 💰 **资金流向** - 大盘资金/北向资金
5. 🐉 **龙虎榜** - 游资动向/机构席位

## 提供能力

- `generate_daily_report(date, save_path)` - 一键生成完整报告
- `build_market_section()` - 单独构建大盘部分
- `build_sector_section()` - 单独构建板块部分
- `build_zt_section(date)` - 单独构建涨停部分
- `build_capital_section()` - 单独构建资金部分
- `build_lhb_section()` - 单独构建龙虎榜部分

## 使用方式

```bash
# 生成今日报告
python main.py

# 指定日期
python main.py --date 2024-12-30

# 指定保存路径
python main.py --save ./report.md
```

## Python API

```python
from skills.05-reports.daily-market-report.main import generate_daily_report

# 生成报告 (自动保存为 daily_report_YYYY-MM-DD.md)
report = generate_daily_report()

# 指定日期
report = generate_daily_report(date="2024-12-30")

# 自定义保存路径
report = generate_daily_report(save_path="./my_report.md")
```

## 报告示例

```markdown
# 📈 A股每日复盘报告

**日期**: 2024-12-30

## 📊 一、大盘表现
...

## 🔥 二、板块热点
...

## 🚀 三、涨停板分析
...
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```

## 依赖的其他 Skill (可选)

- astock-utils
- market-data-collector
- sector-data-collector
- sector-analysis
- capital-flow-analysis
- dragon-tiger-analysis
- limit-up-tracker
- market-analysis

> 注: 本 Skill 独立可用, 内部直接调用 akshare, 不强制依赖其他 Skill。
