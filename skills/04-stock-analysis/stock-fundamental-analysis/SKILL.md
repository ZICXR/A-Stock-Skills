---
name: stock-fundamental-analysis
description: A 股个股基本面分析。当用户需要对某只股票做基本面分析时,Claude 应使用此 Skill。支持盈利能力 (ROE/ROA/毛利率/净利率)、成长性 (营收/利润增长率)、估值 (PE/PB)、财务健康度评估,综合评分采用 4 维模型 (盈利 30% + 成长 30% + 估值 20% + 健康 20%)。
---

# A 股个股基本面分析 Skill

## 何时使用

- 用户要求分析某只股票的基本面
- 用户需要 ROE/ROA 等盈利指标
- 用户需要成长性分析
- 用户需要估值分析
- 用户需要综合评分

## 提供能力

### 财务数据
- `get_financial_indicator(code)` - 财务指标
- `get_performance_express(code)` - 业绩快报

### 评分维度
- `analyze_profitability(fin_df)` - 盈利能力 (ROE/ROA/毛利率)
- `analyze_growth(fin_df)` - 成长性 (营收/利润增长)
- `analyze_valuation(code)` - 估值 (PE/PB)
- `analyze_financial_health(fin_df)` - 财务健康度

### 综合
- `full_fundamental_analysis(code)` - 一键综合分析 (评分 0-100)

## 使用方式

```bash
python main.py fin 000001              # 财务指标
python main.py express 000001          # 业绩快报
python main.py valuation 000001        # 估值
python main.py full 000001             # 综合分析
```

## Python API

```python
from skills.04-stock-analysis.stock-fundamental-analysis.main import full_fundamental_analysis

result = full_fundamental_analysis("000001")
# {
#   'profitability': {'roe': {...}, 'gross_margin': {...}},
#   'growth': {'revenue_growth': {...}, 'profit_growth': {...}},
#   'valuation': {'pe_ttm': 8.5, 'pb': 0.7},
#   'health': {'level': '健康', 'issues': []},
#   'score': 75.5,
#   'rating': '良'  # 优/良/中/差
# }
```

## 综合评分模型

| 维度 | 权重 | 评分项 |
|------|------|--------|
| 盈利能力 | 30% | ROE>15%=优, >10%=良 |
| 成长性 | 30% | 营收增长>30%=优, 利润增长>30%=优 |
| 估值 | 20% | PE<20=优, <40=良, PB<2=优 |
| 财务健康 | 20% | 资产负债率<30%=优, >70%扣分 |

## 评分等级

| 分数 | 等级 |
|------|------|
| >= 70 | 优 |
| >= 50 | 良 |
| >= 30 | 中 |
| < 30 | 差 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
