---
name: start-here
description: 30 秒上手指南。A-Stock-Skills 入门必读,5 个实战场景覆盖 90% 的使用需求。当用户问"我该用哪个 skill"、"怎么开始"、"有什么例子" 时,Claude 应优先激活此 Skill。
---

# 🚀 start-here: 30 秒上手

## A-Stock-Skills 只有 10 个 Skill

| # | Skill | 解决什么问题 |
|---|-------|------------|
| 1 | **astock-data-source** | 拿实时行情 / K 线 (多源 fallback) |
| 2 | **astock-cache** | K 线 parquet 缓存 (5 秒 vs 30 分钟) |
| 3 | **astock-utils** | 代码转换 / 交易日历 / 工具函数 |
| 4 | **watchlist-monitor** | 监控自选股 + 涨跌幅告警 |
| 5 | **screener** | 全市场筛选 (PE / 涨幅 / MACD 等) |
| 6 | **stock-technical-analysis** | MA / MACD / KDJ / RSI / BOLL |
| 7 | **report** | 每日复盘 + 个股研报 |
| 8 | **alerter** | 钉钉 / 微信 / 飞书 推送 |
| 9 | **trade-journal** | 🆕 AI 建议 vs 实盘 复盘 |
| 10 | **start-here** | 🆕 本文档 |

## 🎯 5 个真实场景

### 场景 1: 拿一只股票的行情

```bash
python skills/01-infra/astock-data-source/main.py get-realtime --code 601991
```

### 场景 2: 拿 60 日 K 线 + 算 MACD

```python
from skills.Stock_Analysis.stock_technical_analysis.main import calc_macd
from skills.Stock_Infrastructure.astock_data_source.main import get_kline

df = get_kline("601991", days=60)
macd = calc_macd(df)
print(macd.tail())
```

### 场景 3: 全市场筛选 PE<20 + 涨幅>5%

```bash
python skills/05-quant/screener/main.py screen --pe-max 20 --pct-change-min 5
```

### 场景 4: 监控自选股

```bash
# 1. 生成配置模板
python skills/02-data-collection/watchlist-monitor/main.py init

# 2. 编辑 watchlist.yaml
# 3. 启动监控
python skills/02-data-collection/watchlist-monitor/main.py monitor
```

### 场景 5: 复盘 AI 准不准

```bash
# 1. 记录今天的 AI 建议
python skills/02-data-collection/trade-journal/main.py record --code 601991 --signal "MACD金叉" --target_price 3.50

# 2. 30 天后比对
python skills/02-data-collection/trade-journal/main.py review
```

## ⚠️ 3 件必读

1. **数据源问题**: 住宅 IP 跑东财会被封, astock-data-source v2.0 已自动 fallback
2. **缓存很重要**: 第一次跑慢, 第二次快 100 倍 (用 astock-cache)
3. **AI 不可信, 除非复盘**: 用 trade-journal 记录, 30 天后看胜率

## 🛡️ 免责声明

本项目所有数据来源于**公开市场数据**, 仅供学习研究使用,
**不构成任何投资建议**。投资有风险, 入市需谨慎。
