# 📚 Skills 全目录

> 15个核心 Skills 完整索引

## 🏗️ Layer 1: 基础设施层 (2)

| # | Skill | 路径 | 主要功能 |
|---|-------|------|----------|
| 1 | **astock-data-source** | `skills/01-infra/astock-data-source/` | 多源数据源统一管理 (akshare/tushare/东财) + 自动重试/限流/降级 |
| 2 | **astock-utils** | `skills/01-infra/astock-utils/` | 通用工具: 代码转换/日期/技术指标/格式化 |

## 📡 Layer 2: 数据采集层 (5)

| # | Skill | 路径 | 主要功能 |
|---|-------|------|----------|
| 3 | **stock-news-collector** | `skills/02-data-collection/stock-news-collector/` | 财经新闻 + 情绪分析 + 关键词筛选 |
| 4 | **announcement-collector** | `skills/02-data-collection/announcement-collector/` | 公司公告 + 7大分类 + 关键公告识别 |
| 5 | **market-data-collector** | `skills/02-data-collection/market-data-collector/` | 主要指数 + 市场广度 + 情绪指标 |
| 6 | **sector-data-collector** | `skills/02-data-collection/sector-data-collector/` | 行业/概念板块 + 成分股 + 资金流 |
| 7 | **stock-basic-info** | `skills/02-data-collection/stock-basic-info/` | 个股基本信息 + 实时行情 + 股东 |

## 🌊 Layer 3: 市场分析层 (4)

| # | Skill | 路径 | 主要功能 |
|---|-------|------|----------|
| 8 | **market-analysis** | `skills/03-market-analysis/market-analysis/` | 大盘趋势研判 + 支撑压力 + 量价分析 + 操作建议 |
| 9 | **sector-analysis** | `skills/03-market-analysis/sector-analysis/` | 板块轮动 + 主线识别 + 强度评分 + 轮动信号 |
| 10 | **capital-flow-analysis** | `skills/03-market-analysis/capital-flow-analysis/` | 大盘资金流 + 北向资金 + 个股资金 |
| 11 | **dragon-tiger-analysis** | `skills/03-market-analysis/dragon-tiger-analysis/` | 龙虎榜 + 游资追踪 (40+ 知名席位) + 机构席位 |

## 🎯 Layer 4: 个股分析层 (3)

| # | Skill | 路径 | 主要功能 |
|---|-------|------|----------|
| 12 | **limit-up-tracker** | `skills/04-stock-analysis/limit-up-tracker/` | 涨停板 + 连板梯队 + 炸板率 + 强度评估 + 题材归类 |
| 13 | **stock-technical-analysis** | `skills/04-stock-analysis/stock-technical-analysis/` | K线形态 + 趋势 + 买卖信号 + 支撑压力 + 超买超卖 |
| 14 | **stock-fundamental-analysis** | `skills/04-stock-analysis/stock-fundamental-analysis/` | ROE/ROA + 成长性 + 估值 + 财务健康 + 综合评分 |

## 📝 Layer 5: 报告层 (1)

| # | Skill | 路径 | 主要功能 |
|---|-------|------|----------|
| 15 | **daily-market-report** | `skills/05-reports/daily-market-report/` | 整合所有分析模块, 一键生成 Markdown 复盘报告 |

---

## 📊 数据流图

```
┌──────────────────────────────────────────────────────────────┐
│                       数据源层                                │
│  akshare (主)  +  tushare (辅)  +  东财直连 (备)             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              Layer 1: 基础设施层                              │
│  astock-data-source  |  astock-utils                          │
└────────────────────────┬─────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Layer 2    │  │   Layer 2    │  │   Layer 2    │
│   数据采集   │  │   数据采集   │  │   数据采集   │
│  - 新闻      │  │  - 大盘      │  │  - 个股信息  │
│  - 公告      │  │  - 板块      │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Layer 3    │  │   Layer 3    │  │   Layer 3    │
│   市场分析   │  │   市场分析   │  │   市场分析   │
│  - 大盘      │  │  - 板块      │  │  - 资金      │
│              │  │  - 龙虎榜    │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Layer 4    │  │   Layer 4    │  │   Layer 4    │
│   个股分析   │  │   个股分析   │  │   个股分析   │
│  - 涨停      │  │  - 技术面    │  │  - 基本面    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
              ┌──────────────────────┐
              │       Layer 5         │
              │       报告层          │
              │  daily-market-report  │
              │  (生成完整复盘报告)    │
              └──────────────────────┘
```

---

## 🔗 Skill 依赖关系

```
astock-utils (基础工具)
    ↑
    ├── astock-data-source (依赖 utils)
    ├── stock-news-collector
    ├── announcement-collector
    ├── market-data-collector
    ├── sector-data-collector
    ├── stock-basic-info
    ├── market-analysis (依赖 utils)
    ├── sector-analysis (依赖 sector-data-collector)
    ├── capital-flow-analysis
    ├── dragon-tiger-analysis
    ├── limit-up-tracker (依赖 utils)
    ├── stock-technical-analysis (依赖 utils)
    ├── stock-fundamental-analysis (依赖 utils)
    └── daily-market-report (依赖所有 Layer 1-4)
```

---

## 📞 快速跳转

- [项目主页](../README.md)
- [快速上手](../tutorials/01-quickstart.md)
- [Skill 使用手册](../tutorials/02-skill-usage.md)
- [实战案例](../tutorials/03-workflow-examples.md)
- [最佳实践](../tutorials/04-best-practices.md)
