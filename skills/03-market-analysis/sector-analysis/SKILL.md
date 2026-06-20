---
name: sector-analysis
description: A 股板块轮动分析。当用户需要识别市场主线板块、判断板块轮动信号、计算板块综合强度评分、获取资金流入流出榜时,Claude 应使用此 Skill。结合涨跌幅、资金净流入、上涨家数占比多维度评估。
---

# A 股板块轮动分析 Skill

## 何时使用

- 用户询问当前主线板块
- 用户需要板块轮动信号
- 用户要求板块强度排序
- 用户需要资金流入流出榜

## 提供能力

### 排名
- `rank_sectors(type, top_n)` - 板块涨跌幅排名
- `top_fund_inflow(period, type, top_n)` - 资金流入榜
- `top_fund_outflow(period, type, top_n)` - 资金流出榜

### 评分
- `calc_sector_score(sector_df, flow_df)` - 板块综合强度评分
- `identify_main_themes(top_n)` - 主线板块识别
- `detect_rotation_signal(df)` - 轮动信号检测

## 使用方式

```bash
python main.py rank industry --top 20
python main.py inflow 5日 --type industry --top 10
python main.py outflow 今日 --type industry
python main.py themes --top 5
python main.py rotation
```

## Python API

```python
from skills.03-market-analysis.sector-analysis.main import (
    identify_main_themes, top_fund_inflow, top_fund_outflow, detect_rotation_signal
)

# 主线板块
themes = identify_main_themes(top_n=5)
# [{'type': '行业', 'name': '...', 'pct_change': ..., 'main_net': ..., 'score': ...}]

# 资金流入 Top 10
inflow = top_fund_inflow("5日", "industry", top_n=10)

# 轮动信号
signal = detect_rotation_signal(industry_df)
# {'signal': '普涨', 'up_ratio': 85.2, 'desc': '...'}
```

## 评分维度

| 维度 | 权重 |
|------|------|
| 涨跌幅 | 40% |
| 资金净流入 | 40% |
| 上涨家数占比 | 20% |

## 轮动信号

| 信号 | 条件 | 含义 |
|------|------|------|
| 普涨 | 上涨比例 > 80% | 风险偏好高, 后续或分化 |
| 普跌 | 上涨比例 < 20% | 风险偏好低, 关注护盘 |
| 结构性上涨 | 60-80% | 结构性行情, 抓主线 |
| 结构性下跌 | 20-40% | 多数下跌, 谨慎 |
| 分化 | 40-60% | 精选个股 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
