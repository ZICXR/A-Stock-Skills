---
name: dragon-tiger-analysis
description: A 股龙虎榜分析。当用户需要查看龙虎榜个股明细、追踪知名游资动向 (方新侠/作手新一/赵老哥/章盟主/炒股养家/佛山系等 40+ 知名席位)、分析机构席位买卖、生成龙虎榜日报时,Claude 应使用此 Skill。
---

# A 股龙虎榜分析 Skill

## 何时使用

- 用户询问龙虎榜数据
- 用户需要追踪游资动向
- 用户要求查看机构席位
- 用户询问某只股票是否上龙虎榜

## 提供能力

### 数据获取
- `get_lhb_detail(date)` - 龙虎榜明细
- `get_institution_summary(date)` - 机构买卖汇总
- `get_zt_hot_money(date)` - 涨停板中游资参与的股票

### 游资追踪
- `track_hot_money(date)` - 知名游资操作
- `is_hot_money(branch)` - 判断是否知名游资
- `KNOWN_HOT_MONEY` - 40+ 知名游资席位列表

### 综合
- `lhb_daily_report(date)` - 每日龙虎榜综合报告

## 使用方式

```bash
python main.py detail 2024-12-30      # 龙虎榜明细
python main.py hot 2024-12-30          # 游资动向
python main.py inst 2024-12-30         # 机构席位
python main.py report                  # 每日报告
```

## Python API

```python
from skills.03-market-analysis.dragon-tiger-analysis.main import (
    get_lhb_detail, track_hot_money, lhb_daily_report
)

# 游资动向
hot = track_hot_money("2024-12-30")

# 龙虎榜报告
report = lhb_daily_report()
# {'summary': {...}, 'detail': df, 'hot_money': df, 'institution': df}
```

## 知名游资席位 (内置 40+)

方新侠 · 作手新一 · 赵老哥 · 孙哥 · 章盟主 · 炒股养家 · 欢乐海 · 佛山系 · 成都系 · 上海溧阳路 · 深圳益田路 · 荣超商务中心 · 杭州延安路 · 南京中山东路 · 宁波桑田路 · 财通杭州 · 华鑫上海分公司 · 东方上海源深路

## 龙虎榜上榜条件

- 日涨跌幅 ±7% 以上 (创业板/科创板 ±15%)
- 日换手率达 20% 以上
- 日成交额 5000 万以上 (创业板 1000 万)
- 连续三个交易日涨跌幅 ±20% 以上 (ST 股 ±15%)

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
