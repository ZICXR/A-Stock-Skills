---
name: policy-collector
description: A 股政策资讯采集。当用户需要获取国家政策、监管动态 (证监会/银保监)、央行动作 (降准/降息/MLF)、部委通知 (工信部/发改委)、识别政策对相关板块/个股的影响、提取受益方向时,Claude 应使用此 Skill。
---

# A 股政策资讯采集 Skill

## 何时使用

- 用户需要查看最新政策
- 用户询问证监会/央行/发改委动态
- 用户需要政策对市场影响分析
- 用户需要识别政策受益板块

## 提供能力

- `get_latest_policies(days)` - 最新政策
- `get_industry_policies(industry)` - 行业政策
- `analyze_impact(policy_text)` - 政策影响分析
- `extract_beneficiaries(policy_text)` - 提取受益方向

## 使用方式

```bash
python main.py latest --days 7
python main.py industry 半导体
python main.py analyze "央行降准0.5个百分点"
```

## Python API

```python
from skills.02-data-collection.policy-collector.main import (
    get_latest_policies, analyze_impact, extract_beneficiaries
)

# 最新政策
policies = get_latest_policies(days=7)

# 分析影响
impact = analyze_impact("央行降准0.5个百分点")
# {'direction': '利好', 'targets': ['银行', '地产', '基建']}
```

## 政策分类

- 货币政策 (央行/降准/降息)
- 财政政策 (减税/补贴)
- 产业政策 (半导体/新能源/AI)
- 监管政策 (证监会/银保监)
- 国际政策 (中美贸易/汇率)

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
