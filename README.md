<div align="center">

# 📈 A-Stock-Skills

**让 Claude 成为你的 A 股分析师**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Skills: 10](https://img.shields.io/badge/Skills-10-orange.svg)](#-10-个技能)
[![GitHub stars](https://img.shields.io/github/stars/ZICXR/A-Stock-Skills?style=social)](https://github.com/ZICXR/A-Stock-Skills)

[快速开始](#-3-分钟上手) · [5 个真实场景](#-5-个真实场景) · [为什么只有 10 个](#-为什么只有-10-个) · [English](README_EN.md)

</div>

---

## 😩 你也这样吗?

- 跑全市场筛选, **30 分钟还没完**
- 数据源今天能用, 明天就封
- Claude 给了 4 只推荐, **不知道准不准**
- 自选股涨了 5%, 收盘才发现
- 40 个工具, 90% 用不上

**这工具就是来解决这些的。**

---

## ✨ 它能做什么

| 痛点 | 解决方式 | 速度 |
|------|---------|------|
| 数据源今天能跑明天就废 | 4 源自动 fallback | ✅ |
| 跑一次筛选要 30 分钟 | K线 parquet 缓存 | **360 倍** ↑ |
| 跑了 100 只崩了 | 断点续传 | ✅ |
| 不知道 AI 准不准 | trade-journal 复盘 | ✅ |
| 40 个工具用不上 | 只留 10 个核心 | 砍掉 75% |
| 自选股涨了才看见 | 实时监控 + 钉钉推送 | ✅ |

---

## 🚀 3 分钟上手

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
pip install -r requirements.txt
claude
```

搞定。Claude 会自动识别这些 Skill。

---

## 🎬 5 个真实场景

### 1️⃣ 拿一只股票行情

```bash
python skills/01-infra/astock-data-source/main.py get-realtime --code 601991
```

```json
{"code":"601991","name":"大唐发电","price":3.20,"pct_change":+5.26,"source":"ifzq_gtimg"}
```

---

### 2️⃣ 全市场 PE<20 + ROE>15 (Python 表达式)

```bash
python skills/05-quant/screener/main.py screen --where "pe<20 and roe>15" --top 30
```

```
✅ 筛选结果 (30 只)
================================================================================
  code    name    price   pe    roe   total_mv   change_5d
  600519  贵州茅台 1680.0  18.5  32.1  21500.0    +3.2
  ...
================================================================================
```

---

### 3️⃣ 监控自选股, 涨 5% 自动推钉钉

```bash
# 1) 生成配置
python skills/02-data-collection/watchlist-monitor/main.py init
# 2) 编辑 watchlist.yaml
# 3) 启动
python skills/02-data-collection/watchlist-monitor/main.py loop --interval 30
```

> 下午 2:30, 持仓股 300308 涨 5.2% → 钉钉收到推送 📲

---

### 4️⃣ K 线缓存: 第二次 5 秒出结果

```bash
# 盘后跑一次, 之后都 5 秒
python daily_update.py
# 📦 缓存统计: {"count": 5028, "size_mb": 18.4}
```

> 第一次 30 分钟, 之后 5 秒. **差 360 倍**.

---

### 5️⃣ 记录 AI 推荐, 30 天后看胜率

```bash
# 记录 AI 建议
python skills/02-data-collection/trade-journal/main.py record \
  --code 601991 --signal "MACD金叉" --target_price 3.50

# 30 天后比对
python skills/02-data-collection/trade-journal/main.py review
```

> 🎯 AI 胜率 (近 90 天): 58.3%, 平均 +4.2%, 跑赢沪深 300 +2.4%

---

## 🎯 为什么只有 10 个?

> **少即是多。** 我之前有 40 个, 90% 是"长尾场景"。现在只剩实战用得上的。

| Layer | 数量 | Skill |
|-------|------|-------|
| 🟢 入门 | 1 | start-here |
| 🔵 基建 | 3 | astock-data-source, astock-cache, astock-utils |
| 🟡 数据 | 2 | watchlist-monitor, trade-journal |
| 🟠 分析 | 1 | stock-technical-analysis |
| 🔴 量化 | 1 | screener |
| 🟣 报告 | 1 | report |
| ⚫ 工具 | 1 | alerter |

📦 另外 29 个 (ML/多策略组合/财务三表等) 已归档到 [`archive-v1`](https://github.com/ZICXR/A-Stock-Skills/tree/archive-v1) 分支, 用到再开。

---

## 🛠️ 给开发者

每个 Skill 的结构:

```
skill-name/
├── SKILL.md            # 30-200 行 (When to Activate + 5 API)
├── main.py             # 可执行入口
├── requirements.txt
└── references/         # 详细文档, 不挤上下文
    ├── API.md
    ├── EXAMPLES.md
    └── TROUBLESHOOTING.md
```

**调用方式**:

```python
# CLI
python skills/01-infra/astock-data-source/main.py get-realtime --code 601991

# Python API
from skills.01-infra.astock-data-source.main import get_realtime
q = get_realtime("601991")
```

**数据源优先级** (v2.0):

```
ifzq gtimg (腾讯) → sina → 东财 → akshare
```

任何源连续失败 3 次, 自动跳过。住宅 IP 也能用。

---

## 📊 路线图

- [x] 精简到 10 个核心 Skill
- [x] 多源 fallback (v2.0)
- [x] K线 parquet 缓存 (5 秒 vs 30 分)
- [x] 断点续传 screener
- [x] trade-journal 复盘机制
- [ ] 跑 3 个月, 看 AI 真实胜率
- [ ] 推送模板库
- [ ] Web UI

---

## 🛡️ 免责声明

数据来自**公开市场**, **仅供学习研究**。
**不构成任何投资建议**。

> **AI 不可信, 除非它愿意被复盘** —— 用 `trade-journal` 验证。

投资有风险, 入市需谨慎。

---

## 🤝 一起做

觉得好用? **点个 ⭐ Star** 是最大的支持。

想贡献? 提 Issue / PR 都欢迎。

---

<div align="center">

**⭐ Star** · [📖 文档](tutorials/) · [🐛 提 Issue](https://github.com/ZICXR/A-Stock-Skills/issues) · [🍴 Fork](https://github.com/ZICXR/A-Stock-Skills/fork)

[MIT License](LICENSE) · Made with ❤️ for A 股散户

</div>
