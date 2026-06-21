# 📈 A-Stock-Skills

> 🇨🇳 专业级 A 股分析 Claude Agent Skills 库 | 43 个即插即用 Skills 覆盖数据采集 / 大盘分析 / 资金流向 / 涨停追踪 / 个股研究 / 量化策略 / ML 量化 / 工具集成 / 智能报告

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-43-orange.svg)](#-技能目录)
[![GitHub stars](https://img.shields.io/github/stars/ZICXR/A-Stock-Skills.svg)](https://github.com/ZICXR/A-Stock-Skills)

---

## 🎯 项目简介

**A-Stock-Skills** 是面向 **A 股市场**的 **Claude Agent Skills 集合**。每个 Skill 符合 [Claude Agent Skills 规范](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview),包含 `SKILL.md` (YAML frontmatter + 完整说明) + 可执行 `main.py` 脚本。

集成 **akshare / tushare / 东方财富** 多源数据,提供从**数据采集 → 市场分析 → 个股研究 → 量化策略 → 智能报告**的全链路分析能力。

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
| 📊 **量化支持** | 多因子/回测/筛选器/风控 完整量化体系 |
| 📝 **Markdown 报告** | 自动生成每日复盘 + 个股深度研报 |
| 🔔 **自选股监控** | 配置文件 / 命令行 / 同花顺东财 cookie 三种方式 |

---

## 📦 29 个 Skills 一览

### 🏗️ Layer 1: 基础设施层 (3)

| Skill | 说明 |
|-------|------|
| [astock-data-source](./skills/01-infra/astock-data-source/) | 多源数据源统一管理 (akshare/tushare/东财) + 重试/限流/降级 |
| [astock-utils](./skills/01-infra/astock-utils/) | 通用工具: 代码转换/交易日历/技术指标/格式化 |
| [astock-cache](./skills/01-infra/astock-cache/) | 磁盘缓存, 减少 API 请求 |

### 📡 Layer 2: 数据采集层 (7)

| Skill | 说明 |
|-------|------|
| [stock-news-collector](./skills/02-data-collection/stock-news-collector/) | 财经新闻 + 50+ 关键词情绪分析 |
| [announcement-collector](./skills/02-data-collection/announcement-collector/) | 公司公告 + 7 大分类 + 关键公告 |
| [market-data-collector](./skills/02-data-collection/market-data-collector/) | 主要指数 + 市场广度 + 情绪强度 |
| [sector-data-collector](./skills/02-data-collection/sector-data-collector/) | 行业/概念板块 + 成分股 + 资金流 |
| [stock-basic-info](./skills/02-data-collection/stock-basic-info/) | 个股基本信息 + 实时行情 |
| [policy-collector](./skills/02-data-collection/policy-collector/) | 政策资讯 + 影响分析 + 受益方向 |
| **🆕 [watchlist-monitor](./skills/02-data-collection/watchlist-monitor/)** | **自选股监控 (配置/CLI/同花顺cookie)** |

### 🌊 Layer 3: 市场分析层 (6)

| Skill | 说明 |
|-------|------|
| [market-analysis](./skills/03-market-analysis/market-analysis/) | 大盘趋势 + 支撑压力 + 操作建议 |
| [sector-analysis](./skills/03-market-analysis/sector-analysis/) | 板块轮动 + 主线识别 |
| [capital-flow-analysis](./skills/03-market-analysis/capital-flow-analysis/) | 大盘/北向/个股资金流 |
| [dragon-tiger-analysis](./skills/03-market-analysis/dragon-tiger-analysis/) | 龙虎榜 + 40+ 知名游资 |
| [north-capital-tracker](./skills/03-market-analysis/north-capital-tracker/) | 北向资金专项追踪 |
| [margin-trading-analysis](./skills/03-market-analysis/margin-trading-analysis/) | 两融余额 + 杠杆资金 |

### 🎯 Layer 4: 个股分析层 (8)

| Skill | 说明 |
|-------|------|
| [limit-up-tracker](./skills/04-stock-analysis/limit-up-tracker/) | 涨停板 + 连板梯队 + 6 维强度 |
| [stock-technical-analysis](./skills/04-stock-analysis/stock-technical-analysis/) | K线形态 + 趋势 + 买卖信号 |
| [stock-fundamental-analysis](./skills/04-stock-analysis/stock-fundamental-analysis/) | ROE/ROA + 成长性 + 估值 |
| [stock-valuation-analysis](./skills/04-stock-analysis/stock-valuation-analysis/) | PE/PB/PEG + 行业相对估值 |
| [stock-financial-analysis](./skills/04-stock-analysis/stock-financial-analysis/) | 三表 + 杜邦 + 财务质量 |
| [stock-money-flow](./skills/04-stock-analysis/stock-money-flow/) | 个股资金流 + 主力动向 |
| [stock-position-analysis](./skills/04-stock-analysis/stock-position-analysis/) | 十大股东 + 增减持 |
| **🆕 [industry-comparison](./skills/04-stock-analysis/industry-comparison/)** | **同业对比 (7 维度) + 行业龙头识别** |

### 📊 Layer 5: 量化策略层 (4)

| Skill | 说明 |
|-------|------|
| [factor-analysis](./skills/05-quant/factor-analysis/) | 多因子分析 + IC 计算 |
| [strategy-backtest](./skills/05-quant/strategy-backtest/) | 策略回测 + 夏普/回撤 |
| [signal-screener](./skills/05-quant/signal-screener/) | 内置条件选股 + 信号扫描 |
| [risk-management](./skills/05-quant/risk-management/) | VaR + 仓位 + 止损 |
| **🆕 [portfolio-optimizer](./skills/05-quant/portfolio-optimizer/)** | **组合优化 (马科维茨/风险平价/最大夏普)** |
| **🆕 [stock-screener-custom](./skills/05-quant/stock-screener-custom/)** | **自定义条件筛选 + 策略保存** |

### 📝 Layer 6: 报告层 (2)

| Skill | 说明 |
|-------|------|
| [daily-market-report](./skills/05-reports/daily-market-report/) | 每日 A 股复盘 (Markdown) |
| [stock-research-report](./skills/05-reports/stock-research-report/) | 个股深度研究报告 |
| **🆕 [portfolio-report](./skills/05-reports/portfolio-report/)** | **持仓报告 + 盈亏/行业/调仓建议** |

### 🤖 Layer 7: ML 量化层 (4)

| Skill | 说明 |
|-------|------|
| [stock-classifier](./skills/05-ml/stock-classifier/) | ML 涨跌 3 分类 (XGBoost/LightGBM) |
| [price-predictor](./skills/05-ml/price-predictor/) | ML 价格预测 (回归) |
| [ml-factor](./skills/05-ml/ml-factor/) | ML 多因子排序 (集成学习) |
| [lstm-forecaster](./skills/05-ml/lstm-forecaster/) | 简易 LSTM 时序预测 (纯 numpy) |

### 🛠️ Layer 8: 工具层 (2) 🆕

| Skill | 说明 |
|-------|------|
| [alerter](./skills/06-tools/alerter/) | 告警推送 (钉钉/微信/飞书/Slack/Telegram/Server酱) |
| [portfolio-simulator](./skills/06-tools/portfolio-simulator/) | 虚拟持仓模拟器 (虚拟交易 + 业绩跟踪) |

### 🌐 Web UI (新增)

[webui/app.py](./webui/) - Streamlit 可视化仪表板, 启动 `streamlit run webui/app.py`

---

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
pip install -r requirements.txt
```

### 2. 在 Claude Code 中使用 (推荐)

将本仓库放到 Claude 的 skills 目录:

```bash
# 方法 1: 项目级使用
cd A-Stock-Skills
claude  # Claude 会自动发现 skills/

# 方法 2: 全局安装
cp -r skills/* ~/.claude/skills/
```

### 3. 对话示例

> @Claude 用 daily-market-report 生成今日复盘
>
> @Claude 帮我用 watchlist-monitor 监控我的自选股
>
> @Claude 用 stock-research-report 深度研究 000001
>
> @Claude 用 signal-screener 找出 MACD 金叉 + 站上 20 日均线的股票
>
> @Claude 用 strategy-backtest 测试一下 5/20 均线策略在 000001 上的表现

---

## 🎯 重点 Skill: watchlist-monitor

支持 **3 种自选股来源**:

### 方式 1: 配置文件 (推荐)

```bash
python skills/02-data-collection/watchlist-monitor/main.py init  # 生成模板
```

编辑 `watchlist.yaml`:

```yaml
stocks:
  - code: "000001"
    name: "平安银行"
    cost: 12.50
    shares: 1000
  - code: "600519"
    name: "贵州茅台"

alerts:
  pct_change_up: 5.0
  pct_change_down: -3.0
  limit_up: true
```

然后运行:

```bash
python skills/02-data-collection/watchlist-monitor/main.py monitor
python skills/02-data-collection/watchlist-monitor/main.py loop --interval 30
```

### 方式 2: 命令行传入

```bash
python skills/02-data-collection/watchlist-monitor/main.py monitor --codes 000001,600519,300750
```

### 方式 3: 同花顺/东财 cookie (高级)

```yaml
source:
  type: "ths"
  cookie: "your_cookie"
```

---

## 📚 详细文档

- 📖 [快速上手](./tutorials/01-quickstart.md) - 30分钟上手
- 📖 [Skill 详细使用手册](./tutorials/02-skill-usage.md) - 全部 API
- 📖 [实战案例集](./tutorials/03-workflow-examples.md) - 8个真实场景
- 📖 [Claude Agent Skills 规范](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)

---

## 🏗️ 项目架构

```
A-Stock-Skills/
├── README.md
├── requirements.txt
├── LICENSE
├── skills/                           # 29 个 Skills
│   ├── 01-infra/                     # Layer 1: 基础设施 (3)
│   ├── 02-data-collection/           # Layer 2: 数据采集 (7) ⭐含 watchlist-monitor
│   ├── 03-market-analysis/           # Layer 3: 市场分析 (6)
│   ├── 04-stock-analysis/            # Layer 4: 个股分析 (7)
│   ├── 05-quant/                     # Layer 5: 量化策略 (4)
│   └── 05-reports/                   # Layer 6: 报告 (2)
├── tutorials/                        # 教程
└── examples/                         # 示例
```

每个 Skill 的标准结构:
```
skill-name/
├── SKILL.md           # YAML frontmatter + 详细说明
├── main.py            # 主入口脚本
└── requirements.txt   # 依赖
```

---

## 🤖 Claude Agent Skills 规范

每个 Skill 的 `SKILL.md` 包含:

```yaml
---
name: skill-name                      # 必填, 唯一标识
description: 详细描述...                # 必填, Claude 据此判断何时使用
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

- [x] **29 个完整 Skills** (含量化层 + 自选股监控)
- [ ] LLM 智能解读
- [ ] Web UI (Streamlit)
- [ ] 实时监控预警集成 (邮件/微信/钉钉)

---

## ⚠️ 免责声明

本项目所有数据来源于**公开市场数据**, 仅供学习研究使用, **不构成任何投资建议**。投资有风险, 入市需谨慎。

---

## 📜 许可证

[MIT License](./LICENSE)

---

<div align="center">

**⭐ 如果觉得有用, 请点 Star 支持! ⭐**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

</div>
