# 📈 A-Stock-Skills

> 🇨🇳 专业级 A 股分析 Claude Agent Skills 库 | 15 个即插即用 Skills 覆盖数据采集 / 大盘分析 / 资金流向 / 涨停追踪 / 个股研究 / 智能报告

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-15-orange.svg)](#-技能目录)
[![GitHub stars](https://img.shields.io/github/stars/ZICXR/A-Stock-Skills.svg)](https://github.com/ZICXR/A-Stock-Skills)

---

## 🎯 项目简介

**A-Stock-Skills** 是面向 **A 股市场**的 **Claude Agent Skills 集合**。每个 Skill 符合 [Claude Agent Skills 规范](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview),包含 `SKILL.md` (YAML frontmatter + 完整说明) + 可执行 `main.py` 脚本。

集成 **akshare / tushare / 东方财富** 多源数据,提供从**数据采集 → 市场分析 → 个股研究 → 智能报告**的全链路分析能力。

> 🤖 **专为 Claude Code 设计** - 在 Claude Code 中,这些 Skill 会被自动加载,Claude 会知道何时使用它们。

---

## ✨ 核心特色

| 特色 | 描述 |
|------|------|
| 🤖 **Claude Agent 原生** | 符合 Agent Skills 规范,Claude 自动识别和使用 |
| 🔌 **多源融合** | akshare + tushare + 东方财富,自动降级重试 |
| 🏗️ **6层架构** | 基础设施→数据采集→市场分析→个股分析→量化策略→智能报告 |
| 🧩 **即插即用** | 每个 Skill 独立,函数式风格,CLI + Python API |
| 📊 **专业指标** | MA/MACD/KDJ/RSI/BOLL 完整技术分析体系 |
| 💰 **资金三维** | 北向资金 + 主力资金 + 游资动向 全景追踪 |
| 🚀 **涨停生态** | 涨停板/连板梯队/炸板率/游资动向一站式 |
| 📝 **Markdown 报告** | 自动生成每日复盘报告 |

---

## 📦 15 个 Skills 一览

### 🏗️ Layer 1: 基础设施层

| Skill | 说明 |
|-------|------|
| [astock-data-source](./skills/01-infra/astock-data-source/) | 多源数据源统一管理 (akshare/tushare/东财) + 重试/限流/降级 |
| [astock-utils](./skills/01-infra/astock-utils/) | 通用工具: 代码转换/交易日历/技术指标/格式化 |

### 📡 Layer 2: 数据采集层

| Skill | 说明 |
|-------|------|
| [stock-news-collector](./skills/02-data-collection/stock-news-collector/) | 财经新闻 + 内置 50+ 关键词情绪分析 |
| [announcement-collector](./skills/02-data-collection/announcement-collector/) | 公司公告 + 7 大分类 + 关键公告识别 |
| [market-data-collector](./skills/02-data-collection/market-data-collector/) | 主要指数 + 市场广度 + 情绪强度 |
| [sector-data-collector](./skills/02-data-collection/sector-data-collector/) | 行业/概念板块 + 成分股 + 资金流 |
| [stock-basic-info](./skills/02-data-collection/stock-basic-info/) | 个股基本信息 + 实时行情 + 股东 |

### 🌊 Layer 3: 市场分析层

| Skill | 说明 |
|-------|------|
| [market-analysis](./skills/03-market-analysis/market-analysis/) | 大盘趋势 + 支撑压力 + 量价分析 + 操作建议 |
| [sector-analysis](./skills/03-market-analysis/sector-analysis/) | 板块轮动 + 主线识别 + 强度评分 |
| [capital-flow-analysis](./skills/03-market-analysis/capital-flow-analysis/) | 大盘资金流 + 北向资金 + 个股资金 |
| [dragon-tiger-analysis](./skills/03-market-analysis/dragon-tiger-analysis/) | 龙虎榜 + 40+ 知名游资追踪 |

### 🎯 Layer 4: 个股分析层

| Skill | 说明 |
|-------|------|
| [limit-up-tracker](./skills/04-stock-analysis/limit-up-tracker/) | 涨停板 + 连板梯队 + 炸板率 + 6 维强度评估 |
| [stock-technical-analysis](./skills/04-stock-analysis/stock-technical-analysis/) | K线形态 + 趋势 + 超买超卖 + 买卖信号 |
| [stock-fundamental-analysis](./skills/04-stock-analysis/stock-fundamental-analysis/) | ROE/ROA + 成长性 + 估值 + 4 维综合评分 |

### 📝 Layer 5: 报告层

| Skill | 说明 |
|-------|------|
| [daily-market-report](./skills/05-reports/daily-market-report/) | 一键生成每日 A 股复盘报告 (Markdown) |

---

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
pip install akshare tushare pandas numpy requests
```

### 2. 在 Claude Code 中使用 (推荐)

将本仓库放到 Claude 的 skills 目录:

```bash
# 方法 1: 复制到全局 skills 目录
cp -r skills/* ~/.claude/skills/

# 方法 2: 在项目中使用
cd A-Stock-Skills
claude  # Claude 会自动发现 skills/
```

之后在对话中:

> @Claude 用 daily-market-report 生成今日复盘
>
> @Claude 用 stock-technical-analysis 分析 000001
>
> @Claude 用 sector-analysis 找当前主线板块

Claude 会自动:
1. 找到对应的 Skill
2. 读取 SKILL.md 了解用法
3. 调用 main.py 获取数据
4. 解读结果并给出建议

### 3. 命令行使用

每个 Skill 都有 CLI 入口:

```bash
# 涨停板追踪
python skills/04-stock-analysis/limit-up-tracker/main.py pool
python skills/04-stock-analysis/limit-up-tracker/main.py break

# 个股技术分析
python skills/04-stock-analysis/stock-technical-analysis/main.py full 000001

# 一键生成每日报告
python skills/05-reports/daily-market-report/main.py
```

### 4. Python API

```python
import sys
sys.path.insert(0, ".")

from skills.04-stock-analysis.limit-up-tracker.main import get_zt_pool, evaluate_zt_strength
from skills.04-stock-analysis.stock-technical-analysis.main import full_technical_analysis

# 涨停板
zt = get_zt_pool()

# 个股技术分析
result = full_technical_analysis("000001")
print(result["trading_signal"])
```

---

## 📚 详细文档

- 📖 [完整使用教程](./tutorials/01-quickstart.md) - 30分钟上手
- 📖 [Skill 详细使用手册](./tutorials/02-skill-usage.md) - 15个 Skills 完整 API
- 📖 [实战案例集](./tutorials/03-workflow-examples.md) - 8个真实场景
- 📖 [Claude Agent Skills 规范](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)

---

## 🎯 实战场景

### 场景 1: 每日复盘
```python
from skills.05-reports.daily-market-report.main import generate_daily_report
report = generate_daily_report()  # 自动保存为 daily_report_YYYY-MM-DD.md
```

### 场景 2: 涨停打板
```python
from skills.04-stock-analysis.limit-up-tracker.main import get_zt_pool, evaluate_zt_strength
zt = get_zt_pool()
for _, row in zt.iterrows():
    s = evaluate_zt_strength(row)
    if s["score"] >= 4:
        print(f"{row['name']}: {s['level']} ({s['score']}分)")
```

### 场景 3: 板块轮动
```python
from skills.03-market-analysis.sector-analysis.main import identify_main_themes
themes = identify_main_themes(top_n=5)
for t in themes["main_themes"][:5]:
    print(f"[{t['type']}] {t['name']}: 涨幅{t['pct_change']:.2f}%")
```

### 场景 4: 个股深度研究
```python
from skills.04-stock-analysis.stock-technical-analysis.main import full_technical_analysis
from skills.04-stock-analysis.stock-fundamental-analysis.main import full_fundamental_analysis

code = "000001"
tech = full_technical_analysis(code)
fund = full_fundamental_analysis(code)
print(f"技术: {tech['trading_signal']['signal']}, 基本面: {fund['rating']}")
```

---

## 🏗️ 项目架构

```
A-Stock-Skills/
├── README.md
├── requirements.txt
├── LICENSE
├── skills/                           # Skills 目录 (符合 Claude Agent 规范)
│   ├── 01-infra/                     # Layer 1: 基础设施
│   │   ├── astock-data-source/
│   │   │   ├── SKILL.md              # ⭐ Agent 加载此文件
│   │   │   ├── main.py               # 可执行脚本
│   │   │   └── requirements.txt
│   │   └── astock-utils/
│   ├── 02-data-collection/           # Layer 2: 数据采集
│   ├── 03-market-analysis/           # Layer 3: 市场分析
│   ├── 04-stock-analysis/            # Layer 4: 个股分析
│   └── 05-reports/                   # Layer 5: 报告层
├── tutorials/                        # 教程
└── examples/                         # 实战示例
```

每个 Skill 目录的标准结构:
```
skill-name/
├── SKILL.md           # YAML frontmatter + 详细说明 (Agent 读取)
├── main.py            # 主入口脚本
└── requirements.txt   # 依赖
```

---

## 🤖 Claude Agent Skills 规范

每个 Skill 的 `SKILL.md` 包含:

```yaml
---
name: skill-name                      # 必填, 唯一标识
description: 详细描述...               # 必填, Claude 据此判断何时使用
---
```

Claude 会:
1. 自动扫描 `SKILL.md` 文件
2. 解析 frontmatter 中的 `name` 和 `description`
3. 当用户请求匹配时,自动激活该 Skill
4. 根据 SKILL.md 中的说明,调用对应的 main.py

---

## 🛠️ 技术栈

- **Python 3.8+**
- **数据源**: akshare (主) + tushare (辅) + 东方财富 (备选)
- **数据处理**: pandas, numpy
- **风格**: 函数式编程, 纯 Python

---

## 🤝 贡献

欢迎贡献新 Skill! 参见 [贡献指南](./CONTRIBUTING.md)。

1. Fork 本仓库
2. 在 `skills/` 对应层级创建新目录
3. 创建 `SKILL.md` (YAML frontmatter + 文档)
4. 实现 `main.py` (主入口脚本)
5. 添加 `requirements.txt`
6. 提交 Pull Request

---

## 📊 路线图

- [x] 15 个核心 MVP Skills
- [ ] Layer 6: 量化策略层 (多因子/回测/筛选器/风控)
- [ ] LLM 智能解读
- [ ] Web UI (Streamlit)
- [ ] 实时监控预警

---

## ⚠️ 免责声明

本项目所有数据来源于**公开市场数据**, 仅供学习研究使用, **不构成任何投资建议**。投资有风险, 入市需谨慎。

---

## 📜 许可证

[MIT License](./LICENSE)

---

## 📮 联系方式

- **GitHub**: [https://github.com/ZICXR/A-Stock-Skills](https://github.com/ZICXR/A-Stock-Skills)
- **Issues**: [提交问题](https://github.com/ZICXR/A-Stock-Skills/issues)

---

<div align="center">

**⭐ 如果觉得有用, 请点 Star 支持! ⭐**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

</div>
