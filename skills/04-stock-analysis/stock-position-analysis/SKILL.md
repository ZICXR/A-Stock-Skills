---
name: stock-position-analysis
description: A 股个股股东分析。当用户需要分析某只股票的股东结构、前十大股东、机构持仓、股东户数变化 (筹码集中/分散)、大股东减持/增持、识别筹码集中信号时,Claude 应使用此 Skill。
---

# A 股个股股东分析 Skill

## 何时使用

- 用户需要查看十大股东
- 用户需要分析股东结构
- 用户需要股东户数变化
- 用户需要识别增减持信号

## 提供能力

- `get_top_holders(code, top_n)` - 前十大股东
- `get_holder_count_change(code)` - 股东户数变化
- `analyze_holder_changes(code)` - 增减持变化
- `institutional_holders(code)` - 机构持仓

## 使用方式

```bash
python main.py top 000001 --top 10
python main.py count 000001
python main.py changes 000001
python main.py institutional 000001
```

## Python API

```python
from skills.04-stock-analysis.stock-position-analysis.main import (
    get_top_holders, get_holder_count_change, analyze_holder_changes
)

# 十大股东
holders = get_top_holders("000001", top_n=10)

# 股东户数变化
count = get_holder_count_change("000001")
# {latest_count, prev_count, change_pct}

# 增减持分析
changes = analyze_holder_changes("000001")
# {'增持': [...], '减持': [...]}
```

## 股东分析维度

- 股东户数变化 (减少 = 筹码集中, 增加 = 筹码分散)
- 大股东持股比例
- 机构持仓变化
- 高管增减持

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
