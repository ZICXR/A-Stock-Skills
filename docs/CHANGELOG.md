# 更新日志

> 记录 A-Stock-Skills 的重要变更

## [1.0.0] - 2024-12-30

### 🎉 首次发布

**核心 Skills (15个)**:

#### Layer 1: 基础设施层
- ✨ `astock-data-source`: 多源数据源管理 (akshare/tushare/东财)
- ✨ `astock-utils`: 通用工具 (代码/日期/技术指标)

#### Layer 2: 数据采集层
- ✨ `stock-news-collector`: 财经新闻 + 情绪分析
- ✨ `announcement-collector`: 公司公告 + 分类筛选
- ✨ `market-data-collector`: 大盘数据 + 市场广度
- ✨ `sector-data-collector`: 板块数据 + 资金流
- ✨ `stock-basic-info`: 个股基本信息

#### Layer 3: 市场分析层
- ✨ `market-analysis`: 大盘综合分析
- ✨ `sector-analysis`: 板块轮动 + 主线识别
- ✨ `capital-flow-analysis`: 资金流向分析
- ✨ `dragon-tiger-analysis`: 龙虎榜 + 游资追踪

#### Layer 4: 个股分析层
- ✨ `limit-up-tracker`: 涨停板追踪
- ✨ `stock-technical-analysis`: 技术面分析
- ✨ `stock-fundamental-analysis`: 基本面分析

#### Layer 5: 报告层
- ✨ `daily-market-report`: 每日复盘报告

**文档**:
- 📖 完整的 README.md
- 📖 4 篇教程 (快速上手/Skill手册/实战案例/最佳实践)
- 📖 架构设计文档
- 📖 Skills 全目录

**示例**:
- 🚀 5 个实战示例 (复盘/涨停/个股研究/板块/资金)

### 技术特性
- 多源数据自动降级
- 装饰器重试 + 限流
- 5分钟内存缓存
- 完整的类型注解
- 异常隔离, 单个 Skill 失败不影响整体

---

## 路线图

### [1.1.0] - 计划中

- 🔄 Layer 6: 量化策略层
  - 因子分析
  - 策略回测
  - 信号筛选器
  - 风险管理
- 🔄 LLM 智能解读
- 🔄 Web UI (Streamlit)

### [1.2.0] - 远期

- 🔄 实时盘中监控
- 🔄 多账户管理
- 🔄 因子库
- 🔄 微信/钉钉推送
