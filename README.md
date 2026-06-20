# 📈 A-Stock-Skills

> 🇨🇳 A股市场全栈分析技能库 | 数据采集 · 大盘分析 · 资金追踪 · 涨停监控 · 个股研究 · 量化策略 · 智能报告

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-15-orange.svg)](#-技能目录)
[![GitHub stars](https://img.shields.io/github/stars/ZICXR/A-Stock-Skills.svg)](https://github.com/ZICXR/A-Stock-Skills)

---

## 🎯 项目简介

**A-Stock-Skills** 是面向 A 股市场的**模块化、组合式、开箱即用**的 Python 技能库，集成 **akshare / tushare / 东方财富** 多源数据，提供从**数据采集 → 市场分析 → 个股研究 → 智能报告**的全链路分析能力。

无论你是量化交易者、股票研究员、技术分析爱好者，还是想用程序化方法武装自己的个人投资者，都能在这里找到趁手的工具。

---

## ✨ 核心特色

| 特色 | 描述 |
|------|------|
| 🔌 **多源融合** | akshare + tushare + 东方财富，自动降级重试 |
| 🏗️ **6层架构** | 基础设施→数据采集→市场分析→个股分析→量化策略→智能报告 |
| 🧩 **即插即用** | 每个 Skill 独立可用，函数式风格，组合自由 |
| 📊 **专业指标** | MA/MACD/KDJ/RSI/BOLL 完整技术分析体系 |
| 💰 **资金三维** | 北向资金 + 主力资金 + 两融余额全景追踪 |
| 🚀 **涨停生态** | 涨停板/连板梯队/炸板率/游资动向一站式 |
| 🤖 **AI报告** | 自动生成每日复盘报告（Markdown 格式） |
| 🔒 **限流安全** | 自动限流 + 缓存 + 重试,稳定可靠 |

---

## 📦 技能目录（15个核心 Skills）

### 🏗️ Layer 1: 基础设施层

| Skill | 说明 |
|-------|------|
| [astock-data-source](./skills/01-infra/astock-data-source/) | 多源数据源统一管理 (akshare/tushare/东财) |
| [astock-utils](./skills/01-infra/astock-utils/) | 通用工具: 代码转换/日期/技术指标/格式化 |

### 📡 Layer 2: 数据采集层

| Skill | 说明 |
|-------|------|
| [stock-news-collector](./skills/02-data-collection/stock-news-collector/) | 财经新闻 + 情绪分析 |
| [announcement-collector](./skills/02-data-collection/announcement-collector/) | 公司公告 + 分类筛选 + 关键公告识别 |
| [market-data-collector](./skills/02-data-collection/market-data-collector/) | 大盘指数 + 市场广度 + 情绪指标 |
| [sector-data-collector](./skills/02-data-collection/sector-data-collector/) | 行业/概念板块 + 成分股 + 资金流 |
| [stock-basic-info](./skills/02-data-collection/stock-basic-info/) | 个股基本信息 + 实时行情 + 股东 |

### 🌊 Layer 3: 市场分析层

| Skill | 说明 |
|-------|------|
| [market-analysis](./skills/03-market-analysis/market-analysis/) | 大盘趋势研判 + 支撑压力 + 量价分析 |
| [sector-analysis](./skills/03-market-analysis/sector-analysis/) | 板块轮动 + 主线识别 + 强度评分 |
| [capital-flow-analysis](./skills/03-market-analysis/capital-flow-analysis/) | 大盘资金流 + 北向资金 + 个股资金 |
| [dragon-tiger-analysis](./skills/03-market-analysis/dragon-tiger-analysis/) | 龙虎榜 + 游资追踪 + 机构席位 |

### 🎯 Layer 4: 个股分析层

| Skill | 说明 |
|-------|------|
| [limit-up-tracker](./skills/04-stock-analysis/limit-up-tracker/) | 涨停板 + 连板梯队 + 炸板率 + 强度评估 |
| [stock-technical-analysis](./skills/04-stock-analysis/stock-technical-analysis/) | 技术面 + K线形态 + 趋势 + 买卖信号 |
| [stock-fundamental-analysis](./skills/04-stock-analysis/stock-fundamental-analysis/) | 基本面 + 成长性 + 估值 + 财务健康 |

### 📝 Layer 5: 报告层

| Skill | 说明 |
|-------|------|
| [daily-market-report](./skills/05-reports/daily-market-report/) | 每日大盘复盘报告 (Markdown) |

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills

# 安装依赖
pip install akshare tushare pandas numpy requests
```

### 2. 配置 (可选)

```bash
# 配置 tushare token (提高数据质量, 但 akshare 已能覆盖大部分需求)
export TUSHARE_TOKEN="your_tushare_token_here"
```

### 3. 30秒上手

```python
# ===== 基础用法 =====
import sys
sys.path.insert(0, ".")

# 1. 获取实时行情
from skills.01-infra.astock_data_source.astock_data_source import get_manager
m = get_manager()
df = m.akshare.stock_zh_a_spot()
print(df.head())

# 2. 个股技术分析
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
result = full_technical_analysis("000001")  # 平安银行
print(result['trading_signal'])  # 买卖信号

# 3. 大盘分析
from skills.03-market-analysis.market-analysis.market_analysis import full_market_analysis
market = full_market_analysis("000001")
print(market['advice'])  # 操作建议

# 4. 涨停板追踪
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import zt_daily_report
zt_report = zt_daily_report()
print(zt_report['break_info'])  # 炸板率

# 5. 一键生成每日复盘报告
from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report
report = generate_daily_report()  # 自动保存为 daily_report_YYYY-MM-DD.md
```

### 4. 完整教程

📖 [快速上手指南](./tutorials/01-quickstart.md)
📖 [Skill 详细使用手册](./tutorials/02-skill-usage.md)
📖 [实战案例集](./tutorials/03-workflow-examples.md)
📖 [最佳实践](./tutorials/04-best-practices.md)

---

## 🎓 实战场景

### 场景 1: 每日复盘工作流
```python
from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report
report = generate_daily_report()  # 一键生成完整日报
```

### 场景 2: 涨停板选股
```python
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import get_zt_pool, evaluate_zt_strength

zt = get_zt_pool()
# 筛选强度>=3的涨停
strong_zt = [row for _, row in zt.iterrows() if evaluate_zt_strength(row)['score'] >= 3]
```

### 场景 3: 板块轮动监控
```python
from skills.03-market-analysis.sector-analysis.sector_analysis import identify_main_themes, top_fund_inflow
themes = identify_main_themes(top_n=5)  # 识别主线
inflow = top_fund_inflow(period="3日")  # 3日资金流入
```

### 场景 4: 个股深度研究
```python
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
from skills.04-stock-analysis.stock-fundamental-analysis.stock_fundamental_analysis import full_fundamental_analysis
from skills.02-data-collection.stock-basic-info.stock_basic_info import get_stock_card

code = "000001"
tech = full_technical_analysis(code)
fund = full_fundamental_analysis(code)
basic = get_stock_card(code)
```

---

## 🏗️ 项目架构

```
A-Stock-Skills/
├── README.md                    # 项目主页
├── requirements.txt             # 依赖
├── skills/                      # 技能库
│   ├── 01-infra/                # Layer 1: 基础设施
│   │   ├── astock-data-source/  # 多源数据
│   │   └── astock-utils/        # 通用工具
│   ├── 02-data-collection/      # Layer 2: 数据采集
│   │   ├── stock-news-collector/
│   │   ├── announcement-collector/
│   │   ├── market-data-collector/
│   │   ├── sector-data-collector/
│   │   └── stock-basic-info/
│   ├── 03-market-analysis/      # Layer 3: 市场分析
│   │   ├── market-analysis/
│   │   ├── sector-analysis/
│   │   ├── capital-flow-analysis/
│   │   └── dragon-tiger-analysis/
│   ├── 04-stock-analysis/       # Layer 4: 个股分析
│   │   ├── limit-up-tracker/
│   │   ├── stock-technical-analysis/
│   │   └── stock-fundamental-analysis/
│   └── 05-reports/              # Layer 5: 报告层
│       └── daily-market-report/
├── tutorials/                   # 教程
├── examples/                    # 实战案例
└── docs/                        # 文档
```

---

## 🛠️ 技术栈

- **Python 3.8+**
- **数据源**: akshare (主) + tushare (辅) + 东方财富 (直连)
- **数据处理**: pandas, numpy
- **网络请求**: requests
- **风格**: 函数式编程, 纯 Python, 无框架依赖

---

## 🤝 贡献

欢迎贡献新的 Skill 或改进现有功能！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingSkill`)
3. 提交更改 (`git commit -m 'Add some AmazingSkill'`)
4. 推送到分支 (`git push origin feature/AmazingSkill`)
5. 提交 Pull Request

---

## 📊 路线图

- [x] 15 个核心 MVP Skills
- [ ] Layer 6: 量化策略层 (多因子/回测/筛选器/风控)
- [ ] 接入 LLM 生成 AI 研报
- [ ] Web UI 可视化
- [ ] 实时监控预警
- [ ] 策略回测引擎
- [ ] 因子库与因子计算

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

</div>
