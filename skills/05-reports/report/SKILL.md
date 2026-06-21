---
name: report
description: A 股报告生成器 (3合1统一版)。当用户需要生成 A 股相关报告 (Markdown 格式) 时,Claude 应使用此 Skill。支持 3 种报告: daily (每日大盘复盘) / stock (个股深度研报) / portfolio (持仓报告)。是 daily-market-report + stock-research-report + portfolio-report 合并的统一版本。
---

# A 股报告生成器 Skill (统一版)

## 何时使用

- 用户需要每日 A 股复盘
- 用户需要个股深度研究
- 用户需要持仓报告

## 3 种报告

| 子命令 | 功能 | 内容 |
|--------|------|------|
| `daily` | 每日大盘复盘 | 指数/广度/板块/涨停/资金 |
| `stock` | 个股研报 | 公司/技术/资金/舆情 |
| `portfolio` | 持仓报告 | 盈亏/行业/调仓 |

## 使用方式

```bash
# 每日复盘
python main.py daily
python main.py daily --date 2024-12-30 --save

# 个股研报
python main.py stock 000001
python main.py stock 000001 --save

# 持仓报告
python main.py portfolio --config portfolio.yaml --save
```

## Python API

```python
from skills.05-reports.report.main import (
    report_daily, report_stock, report_portfolio
)

# 每日
md = report_daily(date="2024-12-30", save=True)

# 个股
md = report_stock("000001", save=True)

# 持仓
md = report_portfolio(config_path="./portfolio.yaml", save=True)
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
pyyaml>=5.4.0
```

## 合并历史

本 Skill 由原 `daily-market-report` + `stock-research-report` + `portfolio-report` 合并而成, 节省 2 个 Skill。
