# 📈 A-Stock-Skills

> 🇨🇳 专业级 A 股分析 Claude Agent Skills 库 | 10 个核心 Skills 覆盖数据采集 / 技术分析 / 量化筛选 / 报告生成 / 工具集成

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-10-orange.svg)](#-技能目录)
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
| 🎯 **少即是多** | 10 个核心 Skill 覆盖 90% 实战需求,其余 29 个归档到 `archive-v1` |
| 🔌 **多源 fallback** | ifzq gtimg → sina → 东财 → akshare,住宅 IP 也能用 |
| 💾 **K线 parquet 缓存** | 第一次 30 分钟,之后 5 秒,加速 360 倍 |
| 🔁 **断点续传** | screener 跑到一半崩了? 下次自动继续 |
| 📝 **AI 复盘机制** | trade-journal 记录 AI 推荐 vs 实盘,跑 3 个月看胜率 |
| 🛡️ **不接券商账号** | 安全第一,交易还是您自己来 |

---

## 📦 10 个核心 Skills 一览

> 📦 29 个原 Skill (ML/量化训练/多策略组合等) 已归档到 [`archive-v1`](https://github.com/ZICXR/A-Stock-Skills/tree/archive-v1) 分支

### 🏗️ Layer 1: 基础设施层 (3)

| Skill | 适用场景 | 怎么用 |
|-------|---------|--------|
| [astock-data-source](./skills/01-infra/astock-data-source/) | 想拿某只股票/某只 ETF 的实时价格或 K 线 | Claude 里直接说"601991 现在多少钱",它自动调用 |
| [astock-utils](./skills/01-infra/astock-utils/) | 需要转换股票代码格式 (601991 ↔ sh601991)、算交易日、格式化输出 | 其他 Skill 内部调用,你一般不用直接用 |
| [astock-cache](./skills/01-infra/astock-cache/) | 跑全市场筛选每次都要等半小时,想让第二次只等 5 秒 | 跑一次 `python daily_update.py`,之后跑筛选就快了 |

### 📡 Layer 2: 数据采集层 (2)

| Skill | 适用场景 | 怎么用 |
|-------|---------|--------|
| [watchlist-monitor](./skills/02-data-collection/watchlist-monitor/) | 持仓股想实时监控,涨 5% 自动提醒,免得收盘才发现 | 生成 `watchlist.yaml` 配股票池,`loop --interval 30` 启动 |
| **🆕 [trade-journal](./skills/02-data-collection/trade-journal/)** | 想记录 AI 给的推荐,30 天后看 AI 准不准 | 每次 AI 推荐用 `record` 记录,30 天后用 `review` 看胜率 |

### 🎯 Layer 4: 个股分析层 (1)

| Skill | 适用场景 | 怎么用 |
|-------|---------|--------|
| [stock-technical-analysis](./skills/04-stock-analysis/stock-technical-analysis/) | 想看 MACD 金叉、KDJ 死叉、是否站上 20 日均线 | Claude 里说"601991 现在 MACD 是不是金叉" |

### 📊 Layer 5: 量化策略层 (1)

| Skill | 适用场景 | 怎么用 |
|-------|---------|--------|
| [screener](./skills/05-quant/screener/) | 想从全市场 5000 只里筛出"PE<20、ROE>15、站上 20 日均线"的股票 | `screen --where "pe<20 and roe>15"` |

### 📝 Layer 6: 报告层 (1)

| Skill | 适用场景 | 怎么用 |
|-------|---------|--------|
| [report](./skills/05-reports/report/) | 想让 AI 帮你写一份今日复盘或单股深度研报 | `report daily` 或 `report stock 601991` |

### 🛠️ Layer 8: 工具层 (1)

| Skill | 适用场景 | 怎么用 |
|-------|---------|--------|
| [alerter](./skills/06-tools/alerter/) | 监控告警要推到钉钉/微信/飞书,不打开电脑也能收到 | 配置 webhook,其他 Skill 触发时自动推送 |

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

> @Claude 用 report daily 生成今日复盘
>
> @Claude 帮我用 watchlist-monitor 监控我的自选股
>
> @Claude 用 report stock 深度研究 000001
>
> @Claude 用 screener 找出 MACD 金叉 + 站上 20 日均线 + 涨幅大于 5% 的股票
>
> @Claude 记录一下 601991 的推荐,30 天后看准不准

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

- [x] **精简到 10 个核心 Skill** (其余 29 个归档到 archive-v1)
- [x] **多源 fallback v2.0** (ifzq→sina→东财→akshare)
- [x] **K线 parquet 缓存** (5 秒 vs 30 分)
- [x] **断点续传 screener** v3
- [x] **trade-journal** AI 复盘机制 🆕
- [ ] 跑 3 个月,看 AI 真实胜率
- [ ] 推送模板库
- [ ] Web UI 完善

---

## ⚠️ 免责声明

本项目所有数据来源于**公开市场数据**, 仅供学习研究使用, **不构成任何投资建议**。投资有风险, 入市需谨慎。
**AI 不可信, 除非它愿意被复盘** — 用 `trade-journal` 验证。

---

## 📜 许可证

[MIT License](./LICENSE)

---

<div align="center">

**⭐ 如果觉得有用, 请点 Star 支持! ⭐**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

</div>
