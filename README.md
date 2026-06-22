# 📈 A-Stock-Skills

> 🇨🇳 A 股分析 Claude Agent Skills | **10 个核心 Skill** | 实战派,不做花架子

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-10-orange.svg)](#-技能目录)
[![GitHub stars](https://img.shields.io/github/stars/ZICXR/A-Stock-Skills.svg)](https://github.com/ZICXR/A-Stock-Skills)

---

## 🎯 项目简介

**A-Stock-Skills** 是面向 **A 股散户**的 **Claude Agent Skills 集合**。
**只保留实战用得上的 10 个 Skill**, 其他 29 个已归档到 [`archive-v1`](https://github.com/ZICXR/A-Stock-Skills/tree/archive-v1) 分支。

> 🤖 专为 Claude Code 设计 - Claude 自动识别和使用这些 Skill

---

## ✨ 核心特色

| 特色 | 描述 |
|------|------|
| 🎯 **少即是多** | 10 个核心 Skill,5 个真实场景覆盖 90% 需求 |
| 🔌 **多源 fallback** | ifzq → sina → 东财 → akshare, 住宅 IP 友好 |
| 💾 **K线 parquet 缓存** | 第一次 30 分钟,之后 5 秒,差 360 倍 |
| 🔁 **断点续传** | screener 崩了? 下次自动继续 |
| 📝 **AI 复盘机制** | trade-journal 记录 AI vs 实盘,跑 3 个月看胜率 |
| 🛡️ **不接券商账号** | 安全第一,交易还是您自己来 |

---

## 📦 10 个核心 Skill

| # | Skill | 解决什么 | Layer |
|---|-------|---------|-------|
| 0 | **start-here** | 30 秒上手指南 | 入门 |
| 1 | **astock-data-source** | 多源数据 (v2.0 fallback) | 基建 |
| 2 | **astock-cache** | K线 parquet 缓存 | 基建 |
| 3 | **astock-utils** | 代码转换/工具函数 | 基建 |
| 4 | **watchlist-monitor** | 自选股监控 + 告警 | 数据 |
| 5 | **screener** | 全市场筛选 (v3 接入数据源+缓存) | 量化 |
| 6 | **stock-technical-analysis** | MA/MACD/KDJ/RSI/BOLL | 分析 |
| 7 | **report** | 每日复盘 + 个股研报 | 报告 |
| 8 | **alerter** | 钉钉/微信/飞书 推送 | 工具 |
| 9 | **trade-journal** | 🆕 AI vs 实盘 复盘 | 工具 |

> 📦 29 个原 Skill (ML/量化训练/多策略组合等) 已归档 → [`archive-v1`](https://github.com/ZICXR/A-Stock-Skills/tree/archive-v1) 分支

---

## 🚀 快速开始 (3 分钟)

### 1. 安装

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
pip install -r requirements.txt
```

### 2. 在 Claude Code 中使用

```bash
cd A-Stock-Skills
claude  # Claude 自动发现 skills/
```

### 3. 实战 5 场景

**场景 1: 拿一只股票行情**
```bash
python skills/01-infra/astock-data-source/main.py get-realtime --code 601991
```

**场景 2: 全市场 PE<20 筛选**
```bash
python skills/05-quant/screener/main.py screen --where "pe<20 and roe>15" --top 30
```

**场景 3: 监控自选股**
```bash
# 1) 生成配置模板
python skills/02-data-collection/watchlist-monitor/main.py init
# 2) 编辑 watchlist.yaml
# 3) 启动
python skills/02-data-collection/watchlist-monitor/main.py monitor
```

**场景 4: K 线缓存 (加速 360 倍)**
```bash
# 一次性更新全市场
python daily_update.py
# 之后 5 秒出结果
```

**场景 5: 复盘 AI 准不准**
```bash
# 记录今天的 AI 建议
python skills/02-data-collection/trade-journal/main.py record \
  --code 601991 --signal "MACD金叉" --target_price 3.50
# 30 天后比对
python skills/02-data-collection/trade-journal/main.py review
```

---

## 🏗️ 项目结构

```
A-Stock-Skills/
├── README.md
├── daily_update.py              # K线缓存更新 (15-30 分钟首次,5 秒增量)
├── requirements.txt
├── skills/
│   ├── 00-start-here/           # 上手指南
│   ├── 01-infra/                # 基建 (3)
│   │   ├── astock-data-source/  # 多源数据 v2.0
│   │   ├── astock-cache/        # K线 parquet 缓存
│   │   └── astock-utils/        # 工具
│   ├── 02-data-collection/      # 数据采集 (2)
│   │   ├── watchlist-monitor/   # 自选股
│   │   └── trade-journal/       # AI vs 实盘 复盘 🆕
│   ├── 04-stock-analysis/       # 个股分析 (1)
│   │   └── stock-technical-analysis/
│   ├── 05-quant/                # 量化 (1)
│   │   └── screener/            # v3 接入数据源+缓存
│   ├── 05-reports/              # 报告 (1)
│   │   └── report/
│   └── 06-tools/                # 工具 (1)
│       └── alerter/             # 钉钉/微信/飞书
└── webui/                       # Web UI (Streamlit)
```

每个 Skill 的标准结构:
```
skill-name/
├── SKILL.md            # 30-200 行核心 (When to Activate + 5 API)
├── main.py             # 可执行入口
├── requirements.txt
└── references/         # 详细文档 (按需加载,不挤上下文)
    ├── API.md
    ├── EXAMPLES.md
    └── TROUBLESHOOTING.md
```

---

## 🎯 设计哲学

1. **少即是多** - 10 个 Skill 覆盖 90% 实战需求
2. **数据源隔离** - 所有 Skill 走 astock-data-source,不再各自抓 eastmoney
3. **缓存优先** - K线 parquet 缓存让"每天跑一次"成为可能
4. **AI 可问责** - trade-journal 让 AI 对自己的建议负责
5. **拒绝合并** - 不做"3合1/2合1",用户要的是清晰

---

## 🤖 Claude Agent Skills 规范

每个 Skill 的 `SKILL.md`:
```yaml
---
name: skill-name
description: 触发条件描述
---
```

Claude 自动:
1. 扫描 `SKILL.md`
2. 解析 frontmatter
3. 用户请求匹配时自动激活
4. 调用对应 `main.py`

---

## 🛠️ 技术栈

- **Python 3.8+**
- **数据源**: ifzq gtimg (腾讯) → sina → 东财 → akshare
- **缓存**: pandas + pyarrow parquet
- **风格**: 函数式 + CLI 双接口

---

## 📊 路线图

- [x] **精简到 10 个核心 Skill** ✅
- [x] **多源 fallback (v2.0)** ✅
- [x] **K线 parquet 缓存** ✅
- [x] **断点续传 screener** ✅
- [x] **trade-journal** 🆕 ✅
- [ ] 跑 3 个月,看 AI 胜率
- [ ] Web UI 完善
- [ ] 飞书/钉钉 推送模板

---

## 🛡️ 免责声明

本项目数据来源于**公开市场数据**, 仅供学习研究使用,
**不构成任何投资建议**。投资有风险, 入市需谨慎。
**AI 不可信, 除非它愿意被复盘** — 用 `trade-journal` 验证。

---

## 📜 许可证

[MIT License](./LICENSE)

---

<div align="center">

**⭐ 如果觉得有用, 请点 Star ⭐**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

</div>
