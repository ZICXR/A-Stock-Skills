---
name: industry-comparison
description: A 股同行业多只股票对比分析。当用户需要对比同行业多只股票 (财务/估值/技术/资金) 时,Claude 应使用此 Skill。支持 7 维对比 (估值/盈利/成长/技术/资金/市值/分析师),自动排名。
---

# A 股同业对比 Skill

## 何时使用

- 用户需要对比同行多只股票
- 用户需要找行业龙头
- 用户需要行业强弱排名
- 用户需要选股决策

## 对比维度 (7 大维度)

1. **估值** - PE/PB/PS
2. **盈利能力** - ROE/毛利率/净利率
3. **成长性** - 营收增长/利润增长
4. **技术面** - 趋势/动量/强弱
5. **资金面** - 主力净流入/换手率
6. **市值** - 总市值/流通市值
7. **机构持仓** - 持仓变化

## 使用方式

```bash
# 对比指定股票
python main.py compare --codes 000001,600036,601398 --name "银行"

# 按行业查找
python main.py by-industry --industry 银行 --top 10

# 找行业龙头
python main.py leader --industry 白酒 --top 5

# 多维排名
python main.py rank --codes 000001,600036,601398,002142 --metric roe
```

## Python API

```python
from skills.04-stock-analysis.industry-comparison.main import (
    compare_stocks, rank_by_metric, find_leader
)

# 对比多只股票
result = compare_stocks(["000001", "600036", "601398"], name="银行")
# [{'code', 'name', 'pe', 'pb', 'roe', 'momentum', 'score', 'rank'}, ...]

# 行业排名
leaders = find_leader("银行", top_n=5)
```

## 输出示例

```
=== 银行行业对比 ===
代码    名称        PE    PB    ROE   涨幅  主力流入  综合得分  排名
000001  平安银行    5.2   0.6  12.3%  +1.2%  +0.5亿  78.5     🥇
600036  招商银行    6.1   1.0  16.5%  +0.5%  -0.3亿  76.2     🥈
601398  工商银行    5.0   0.6  11.2%  +0.8%  +0.1亿  72.0     🥉
```

## 排名规则

- 综合得分 = 估值分 × 0.2 + 盈利分 × 0.25 + 成长分 × 0.2 + 技术分 × 0.2 + 资金分 × 0.15
- 各分项按行业内百分位计算 (0-100)

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
