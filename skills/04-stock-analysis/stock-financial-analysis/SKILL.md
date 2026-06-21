---
name: stock-financial-analysis
description: A 股个股财务报表深度分析。当用户需要分析某只股票的利润表/资产负债表/现金流量表 (三表分析)、进行杜邦分析 (ROE 分解: 净利率×周转率×杠杆)、评估财务质量 (利润含金量/资产质量/负债结构) 时,Claude 应使用此 Skill。
---

# A 股个股财务报表分析 Skill

## 何时使用

- 用户需要三表分析
- 用户需要杜邦分析
- 用户需要财务质量评估
- 用户需要现金流分析

## 提供能力

- `get_income_statement(code)` - 利润表
- `get_balance_sheet(code)` - 资产负债表
- `get_cash_flow(code)` - 现金流量表
- `dupont_analysis(code)` - 杜邦分析
- `assess_finance_quality(code)` - 财务质量评估

## 使用方式

```bash
python main.py income 000001
python main.py balance 000001
python main.py cashflow 000001
python main.py dupont 000001
python main.py quality 000001
```

## Python API

```python
from skills.04-stock-analysis.stock-financial-analysis.main import (
    get_income_statement, dupont_analysis, assess_finance_quality
)

# 利润表
inc = get_income_statement("000001")

# 杜邦分析
dupont = dupont_analysis("000001")
# {ROE, 净利率, 总资产周转率, 权益乘数}

# 财务质量
quality = assess_finance_quality("000001")
# {'level': '优', 'score': 80, 'issues': []}
```

## 杜邦公式

```
ROE = 净利率 × 总资产周转率 × 权益乘数
     = 销售盈利能力 × 运营效率 × 财务杠杆
```

## 财务质量评估维度

- 利润含金量 (经营现金流/净利润)
- 资产质量 (应收账款占比)
- 负债结构 (短期/长期负债比)
- 现金流健康度

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
