---
name: stock-news-collector
description: A 股财经新闻采集与情绪分析。当用户需要获取某只股票的近期新闻、市场财经快讯、热点题材新闻、或分析新闻情绪倾向 (利好/利空) 时,Claude 应使用此 Skill。内置 50+ 利好/利空关键词词典,可自动评估每条新闻的情绪倾向并汇总。
---

# A 股财经新闻采集 Skill

## 何时使用

- 用户要求获取某只股票的近期新闻
- 用户询问市场财经快讯
- 用户需要新闻情绪分析
- 用户询问"为什么某只股票今天涨/跌"

## 提供能力

### 数据获取
- `get_stock_news(code, max_count)` - 个股新闻
- `get_market_news(max_count)` - 全市场快讯
- `get_hot_sector_news(top_n)` - 热点板块新闻

### 分析能力
- `summarize_sentiment(news_df)` - 汇总情绪
- `calc_sentiment(text)` - 单条新闻情绪
- `filter_by_keyword(news_df, keywords)` - 关键词筛选

## 使用方式

```bash
# CLI
python main.py stock-news 000001 --max 20
python main.py market-news --max 50
python main.py sentiment 000001
python main.py hot-sectors --top 10
```

## Python API

```python
from skills.02-data-collection.stock-news-collector.main import (
    get_stock_news, summarize_sentiment, filter_by_keyword
)

# 获取新闻
news = get_stock_news("000001", max_count=20)

# 关键词筛选
key_news = filter_by_keyword(news, ["重组", "中标", "签约"])

# 情绪汇总
summary = summarize_sentiment(news)
# {'total': 20, 'positive': 8, 'negative': 3, 'label': 'positive'}
```

## 情绪词典 (内置 50+ 关键词)

**利好词**: 涨停、大涨、突破、新高、利好、中标、签约、盈利、增长、龙头、连板、妖股、增持、回购、并购、重组、首板、扩产

**利空词**: 跌停、大跌、破位、新低、利空、亏损、风险、减持、套现、违规、处罚、诉讼、调查、退市、ST、暴跌、崩盘

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
