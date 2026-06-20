# 🚀 快速上手指南

> 30 分钟掌握 A-Stock-Skills

## 📋 目录

- [什么是 Claude Agent Skills](#什么是-claude-agent-skills)
- [环境准备](#环境准备)
- [安装 Skills](#安装-skills)
- [在 Claude Code 中使用](#在-claude-code-中使用)
- [命令行使用](#命令行使用)
- [Python API 使用](#python-api-使用)

---

## 什么是 Claude Agent Skills

**Agent Skills** 是 Anthropic 推出的 Claude 扩展机制。每个 Skill 包含:
- `SKILL.md` - YAML frontmatter + 完整说明 (Claude 读取)
- `main.py` - 可执行脚本 (Claude 调用)

Claude 会自动扫描所有 Skills,根据用户请求自动激活匹配的 Skill。

---

## 环境准备

### 1. 安装 Python 3.8+

```bash
python --version
```

### 2. 安装 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

### 3. 安装依赖

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
pip install -r requirements.txt
```

### 4. (可选) 配置 Tushare Token

```bash
export TUSHARE_TOKEN="your_token_here"  # Linux/Mac
$env:TUSHARE_TOKEN = "your_token_here"  # PowerShell
```

---

## 安装 Skills

### 方法 1: 项目级使用 (推荐)

直接在项目目录中使用:

```bash
cd A-Stock-Skills
claude
```

Claude 会自动发现 `skills/` 目录下的所有 Skills。

### 方法 2: 全局安装

复制到 Claude 全局 skills 目录:

```bash
# Linux/Mac
mkdir -p ~/.claude/skills
cp -r skills/* ~/.claude/skills/

# Windows
mkdir %USERPROFILE%\.claude\skills
xcopy /E /I skills %USERPROFILE%\.claude\skills
```

---

## 在 Claude Code 中使用

### 启动 Claude

```bash
claude
```

### 触发 Skill

在对话中,Claude 会根据你的请求自动激活对应 Skill:

| 你的请求 | Claude 激活的 Skill |
|---------|-------------------|
| "分析平安银行的技术面" | `stock-technical-analysis` |
| "今天有什么涨停板" | `limit-up-tracker` |
| "生成今日复盘报告" | `daily-market-report` |
| "今天哪些板块在涨" | `sector-analysis` |
| "北向资金今天怎么样" | `capital-flow-analysis` |

### 示例对话

**示例 1: 涨停板分析**

> 你: 帮我看看今天的涨停板
>
> Claude: [自动激活 limit-up-tracker Skill,调用 get_zt_pool,展示涨停板数据]

**示例 2: 个股深度研究**

> 你: 深度研究一下 000001
>
> Claude: [自动调用 stock-technical-analysis + stock-fundamental-analysis + stock-news-collector + capital-flow-analysis,生成综合报告]

**示例 3: 每日复盘**

> 你: 帮我生成今日复盘
>
> Claude: [自动激活 daily-market-report,生成完整 Markdown 报告并保存]

---

## 命令行使用

每个 Skill 都提供 CLI 入口:

### Skill 1: astock-data-source

```bash
python skills/01-infra/astock-data-source/main.py --list
python skills/01-infra/astock-data-source/main.py get_realtime 000001
python skills/01-infra/astock-data-source/main.py get_kline 000001 --days 60
```

### Skill 12: limit-up-tracker

```bash
# 当日涨停
python skills/04-stock-analysis/limit-up-tracker/main.py pool

# 炸板率
python skills/04-stock-analysis/limit-up-tracker/main.py break

# 涨停原因
python skills/04-stock-analysis/limit-up-tracker/main.py reasons

# 连板梯队
python skills/04-stock-analysis/limit-up-tracker/main.py consecutive
```

### Skill 13: stock-technical-analysis

```bash
# 综合分析
python skills/04-stock-analysis/stock-technical-analysis/main.py full 000001

# 仅趋势
python skills/04-stock-analysis/stock-technical-analysis/main.py trend 000001

# 仅买卖信号
python skills/04-stock-analysis/stock-technical-analysis/main.py signal 000001
```

### Skill 15: daily-market-report

```bash
# 生成今日报告
python skills/05-reports/daily-market-report/main.py

# 指定日期
python skills/05-reports/daily-market-report/main.py --date 2024-12-30

# 指定保存路径
python skills/05-reports/daily-market-report/main.py --save ./my_report.md
```

---

## Python API 使用

```python
import sys
sys.path.insert(0, ".")

# 数据采集层
from skills.02-data-collection.stock-basic-info.stock_basic_info.main import (
    get_realtime, get_stock_info
)
from skills.02-data-collection.stock-news-collector.stock_news_collector.main import (
    get_stock_news, summarize_sentiment
)

# 市场分析层
from skills.03-market-analysis.sector-analysis.sector_analysis.main import identify_main_themes
from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis.main import (
    get_north_bound_today, get_stock_fund_flow
)

# 个股分析层
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis.main import full_technical_analysis
from skills.04-stock-analysis.stock-fundamental-analysis.stock_fundamental_analysis.main import full_fundamental_analysis
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker.main import get_zt_pool, evaluate_zt_strength

# 报告层
from skills.05-reports.daily-market-report.daily_market_report.main import generate_daily_report

# 1. 个股实时行情
rt = get_realtime("000001")
print(f"平安银行: {rt['price']} ({rt['pct_change']:+.2f}%)")

# 2. 技术面
tech = full_technical_analysis("000001")
print(f"技术: {tech['trading_signal']}")

# 3. 基本面
fund = full_fundamental_analysis("000001")
print(f"基本面: {fund['rating']} (评分: {fund['score']})")

# 4. 新闻情绪
news = get_stock_news("000001", max_count=20)
sent = summarize_sentiment(news)
print(f"舆情: {sent['label']}")

# 5. 涨停板
zt = get_zt_pool()
for _, row in zt.head(5).iterrows():
    s = evaluate_zt_strength(row)
    print(f"{row['name']}: {s['level']} ({s['score']}分)")

# 6. 主线板块
themes = identify_main_themes(top_n=3)
for t in themes["main_themes"][:3]:
    print(f"[{t['type']}] {t['name']}: {t['pct_change']:+.2f}%")

# 7. 一键生成报告
report = generate_daily_report()
```

---

## 🎯 实战场景

### 场景 1: 选股策略

> 你: 帮我找出 MACD 金叉 + 站上 20 日均线 + 放量的股票
>
> Claude: [自动激活 astock-data-source 获取全A股 + stock-technical-analysis 的工具函数,编写组合选股脚本]

### 场景 2: 涨停板研究

> 你: 今天的涨停板,哪些是强势涨停?它们的共同特征是什么?
>
> Claude: [调用 limit-up-tracker 的 evaluate_zt_strength 评估,分析强势涨停的特征]

### 场景 3: 板块轮动监控

> 你: 现在的主线板块是什么?资金在流入哪些?
>
> Claude: [调用 sector-analysis 的 identify_main_themes + capital-flow-analysis]

### 场景 4: 个股风险评估

> 你: 帮我看看 600519 的风险点
>
> Claude: [综合 stock-fundamental-analysis + announcement-collector + stock-news-collector,输出风险评估]

---

## ❓ 常见问题

### Q1: Claude 怎么知道使用哪个 Skill?

每个 Skill 的 `SKILL.md` 都有详细的 `description`,Claude 会根据你的请求语义匹配最合适的 Skill。

### Q2: Skills 之间如何协作?

Claude 可以同时激活多个 Skill,组合使用。例如 "分析 000001" 可能同时调用:
- `stock-basic-info` (基本信息)
- `stock-technical-analysis` (技术面)
- `stock-fundamental-analysis` (基本面)
- `stock-news-collector` (舆情)
- `capital-flow-analysis` (资金流)

### Q3: 不使用 Claude Code 可以吗?

完全可以!所有 Skill 都提供:
- ✅ CLI 命令行
- ✅ Python API
- ✅ 独立可执行

### Q4: 数据获取失败?

- 检查网络
- akshare 升级: `pip install -U akshare`
- 项目已内置重试机制

### Q5: Tushare 报 token 错误?

```bash
export TUSHARE_TOKEN="your_token"
```

Tushare 需要注册,但 akshare 已能满足 90% 需求。

---

## 📚 下一步

- 📖 [Skill 详细使用手册](./02-skill-usage.md)
- 📖 [实战案例集](./03-workflow-examples.md)
- 📖 [Claude Agent Skills 规范](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)

---

💡 **提示**: 配合 Claude Code 使用效果最佳,Claude 会自动选择合适的 Skill 并组合使用!
