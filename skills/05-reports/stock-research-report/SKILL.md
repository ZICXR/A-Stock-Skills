---
name: stock-research-report
description: A 股个股深度研究报告生成。当用户需要对某只股票生成完整的研究报告 (Markdown 格式, 7 大部分: 公司概况/技术面/基本面/估值/资金面/舆情/投资建议) 时,Claude 应使用此 Skill。整合所有 Layer 1-4 数据,自动保存为 research_<code>_<date>.md。
---

# A 股个股深度研究报告 Skill

## 何时使用

- 用户需要某只股票的完整研报
- 用户需要整合多维度分析
- 用户需要 Markdown 格式的深度报告
- 用户需要保存个股分析

## 报告内容

1. 📌 **公司概况** - 基本信息/主营业务/股东
2. 📈 **技术面** - 趋势/形态/买卖信号
3. 💼 **基本面** - 财务/盈利/成长
4. 💰 **估值** - PE/PB/PEG
5. 💸 **资金面** - 主力/北向/龙虎榜
6. 📰 **舆情** - 新闻情绪
7. 🎯 **投资建议** - 综合评分 + 操作建议

## 提供能力

- `generate_research(code, save)` - 一键生成完整研报
- `build_company_section(code)` - 公司概况
- `build_technical_section(code)` - 技术面
- `build_fundamental_section(code)` - 基本面
- `build_valuation_section(code)` - 估值
- `build_capital_section(code)` - 资金面
- `build_sentiment_section(code)` - 舆情
- `build_advice_section(code)` - 投资建议

## 使用方式

```bash
python main.py 000001
python main.py 000001 --save ./research.md
```

## Python API

```python
from skills.05-reports.stock-research-report.main import generate_research

# 生成研报 (自动保存)
report = generate_research("000001", save=True)
# 自动保存为 research_000001_YYYY-MM-DD.md
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```

## 依赖的其他 Skill (软依赖)

> 本 Skill 独立可用, 内部直接调用 akshare; 也会尝试调用其他 Skill (如可用)。
