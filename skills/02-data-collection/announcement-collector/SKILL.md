---
name: announcement-collector
description: A 股公司公告采集与分析。当用户需要获取某只公司的公告列表、按公告类型 (业绩/分红/重组/股东/风险/经营/治理) 分类筛选、识别关键公告 (重大事项、停牌重组、处罚等) 时,Claude 应使用此 Skill。
---

# A 股公司公告采集 Skill

## 何时使用

- 用户要求获取某只公司的近期公告
- 用户询问某公司的分红/重组/股东变动情况
- 用户需要按公告类型筛选
- 用户需要识别关键公告

## 提供能力

### 数据获取
- `get_announcements(code, max_count)` - 个股公告列表

### 分析能力
- `classify(title)` - 公告分类 (业绩/分红/重组/股东/风险/经营/治理)
- `is_key(title)` - 是否关键公告
- `filter_by_category(df, category)` - 按分类筛选
- `filter_key(df)` - 筛选关键公告
- `summarize(df)` - 汇总统计

## 公告分类

| 分类 | 关键词示例 |
|------|-----------|
| 业绩 | 业绩、盈利、净利润、扭亏、预增、预减 |
| 分红 | 分红、派息、送股、转增、回购 |
| 重组 | 重组、并购、收购、合并、资产置换 |
| 股东 | 股东、减持、增持、质押、解押 |
| 风险 | 风险、停牌、复牌、退市、ST、处罚 |
| 经营 | 中标、签约、订单、战略合作、扩产 |
| 治理 | 高管、董事、股东大会、换届、辞职 |

## 使用方式

```bash
python main.py announcements 000001 --max 30
python main.py key 000001 --max 100
python main.py category 000001 --type 业绩
python main.py summary 000001
```

## Python API

```python
from skills.02-data-collection.announcement-collector.main import (
    get_announcements, filter_key, filter_by_category, summarize
)

ann = get_announcements("000001")
key = filter_key(ann)  # 关键公告
perf = filter_by_category(ann, "业绩")  # 业绩类公告
stats = summarize(ann)  # 汇总
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
