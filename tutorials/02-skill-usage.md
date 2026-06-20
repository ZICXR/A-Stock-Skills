# 📖 Skill 详细使用手册

> 15个 Skills 的详细 API 文档

## 📋 目录

- [Layer 1: 基础设施层](#layer-1-基础设施层)
- [Layer 2: 数据采集层](#layer-2-数据采集层)
- [Layer 3: 市场分析层](#layer-3-市场分析层)
- [Layer 4: 个股分析层](#layer-4-个股分析层)
- [Layer 5: 报告层](#layer-5-报告层)

---

## Layer 1: 基础设施层

### astock-data-source

**功能**: 多源数据源统一管理 (akshare/tushare/东财)

**核心类**:

```python
from skills.01-infra.astock-data-source.astock_data_source import (
    get_manager, health_check, DataSourceManager
)

# 健康检查
status = health_check()
# {'akshare': True, 'tushare': False, 'eastmoney': True}

# 获取管理器
m = get_manager()
m.akshare.stock_zh_a_spot()           # 全A股实时
m.akshare.stock_zh_a_hist("000001")   # 个股K线
m.akshare.stock_zt_pool_em(date="20240601")  # 涨停板
```

**特性**:
- 自动重试 (3次)
- 限流控制 (默认2次/秒)
- 内存缓存 (5分钟TTL)
- 失败自动降级到其他数据源

---

### astock-utils

**功能**: 通用工具函数

**核心 API**:

```python
from skills.01-infra.astock-utils.astock_utils import *

# 代码处理
normalize_stock_code("sh600000")      # -> "600000"
get_market("300750")                  # -> "sz"
is_cyb("300750")                      # -> True (创业板)
is_kcb("688981")                      # -> True (科创板)

# 日期
today_str()                           # -> "2024-12-30"
last_n_trade_days(5)                  # 最近5个交易日

# 技术指标
df = add_all_indicators(df)
# 自动添加: MA5/10/20/60, DIF/DEA/MACD, K/D/J, RSI6/12/24, MID/UPPER/LOWER

# 格式化
fmt_volume(123456789)                 # -> "1.23亿"
fmt_money(9876543)                    # -> "987.65万"
fmt_pct(1.234)                        # -> "1.23%"
```

---

## Layer 2: 数据采集层

### stock-news-collector

**功能**: 财经新闻采集 + 情绪分析

```python
from skills.02-data-collection.stock-news-collector.stock_news_collector import (
    get_stock_news, get_market_news,
    summarize_sentiment, calc_sentiment
)

# 个股新闻
news = get_stock_news("000001", max_count=20)

# 全市场快讯
mkt = get_market_news(max_count=50)

# 情绪汇总
summary = summarize_sentiment(news)
# {
#   'total': 20, 'positive': 8, 'negative': 3, 'neutral': 9,
#   'score': 25.0, 'label': 'positive'
# }
```

**情绪词典**: 内置 50+ 利好/利空关键词

---

### announcement-collector

**功能**: 公司公告采集 + 分类

```python
from skills.02-data-collection.announcement-collector.announcement_collector import (
    get_stock_announcements, filter_key_announcements,
    filter_by_category, summarize_announcements
)

# 公告
ann = get_stock_announcements("000001")

# 关键公告
key = filter_key_announcements(ann)

# 分类筛选
performance = filter_by_category(ann, "业绩")
dividend = filter_by_category(ann, "分红")
risk = filter_by_category(ann, "风险")

# 统计
stats = summarize_announcements(ann)
```

**公告分类**:
- 业绩 (盈利/预增/扭亏)
- 分红 (派息/送股/回购)
- 重组 (并购/收购)
- 股东 (减持/增持/质押)
- 风险 (ST/处罚/退市)
- 经营 (中标/签约/扩产)
- 治理 (高管/股东大会)

---

### market-data-collector

**功能**: 大盘数据

```python
from skills.02-data-collection.market-data-collector.market_data_collector import (
    get_major_indices, get_index_hist,
    get_market_breadth, calc_market_strength
)

# 主要指数
indices = get_major_indices()
# 包含: 上证/深成/创业板/科创50/沪深300/中证500

# 指数K线
df = get_index_hist("000001", start_date="2024-01-01")

# 市场广度
breadth = get_market_breadth()
# {'up': 3421, 'down': 1523, 'limit_up': 56, 'limit_down': 8, ...}

# 市场强度
strength = calc_market_strength(breadth)
# {'score': 0.8, 'level': 'neutral', 'desc': '震荡偏强'}
```

---

### sector-data-collector

**功能**: 板块数据

```python
from skills.02-data-collection.sector-data-collector.sector_data_collector import (
    get_industry_sectors, get_concept_sectors,
    get_sector_fund_flow, get_sector_stocks
)

# 行业板块
industries = get_industry_sectors()

# 概念板块
concepts = get_concept_sectors()

# 板块资金流
flow = get_sector_fund_flow("今日")  # 今日/3日/5日/10日

# 板块成分股
stocks = get_sector_stocks("BK0420")  # 行业代码
```

---

### stock-basic-info

**功能**: 个股基本信息

```python
from skills.02-data-collection.stock-basic-info.stock_basic_info import (
    get_stock_info, get_stock_realtime,
    get_top_holders, get_main_business,
    get_stock_card
)

# 实时行情
rt = get_stock_realtime("000001")
# {'code', 'name', 'price', 'pct_change', 'volume', 'pe', 'pb', ...}

# 公司信息
info = get_stock_info("000001")
# {股票简称, 行业, 上市日期, 总股本, 流通股本, ...}

# 前十大股东
holders = get_top_holders("000001", top_n=10)

# 完整信息卡
card = get_stock_card("000001")
# {'basic': {...}, 'realtime': {...}}
```

---

## Layer 3: 市场分析层

### market-analysis

**功能**: 大盘综合分析

```python
from skills.03-market-analysis.market-analysis.market_analysis import (
    full_market_analysis, analyze_index_trend,
    calc_support_resistance, analyze_volume_price
)

# 综合分析
result = full_market_analysis("000001", days=60)
# {
#   'trend': {'overall': '看多', 'score': 4, 'signals': [...]},
#   'support_resistance': {'R1': 3050, 'S1': 2950, ...},
#   'volume_price': {'signal': '放量上涨'},
#   'advice': '偏多格局, 精选个股, 控制仓位'
# }

# 单项分析
trend = analyze_index_trend("000001")
sr = calc_support_resistance(df)
vp = analyze_volume_price(df)
```

**信号体系**:
- 均线多头/空头
- MACD金叉/死叉
- 量价配合 (放量上涨/缩量下跌)

---

### sector-analysis

**功能**: 板块轮动分析

```python
from skills.03-market-analysis.sector-analysis.sector_analysis import (
    rank_sectors, top_fund_inflow, top_fund_outflow,
    calc_sector_score, identify_main_themes,
    detect_rotation_signal
)

# 板块涨幅排名
top = rank_sectors("industry", top_n=20)

# 资金流入榜
inflow = top_fund_inflow("今日", "industry", top_n=10)
inflow_5d = top_fund_inflow("5日")

# 资金流出榜
outflow = top_fund_outflow("今日")

# 主线识别
themes = identify_main_themes(top_n=5)
# 返回 5 个最热板块

# 轮动信号
signal = detect_rotation_signal(industry_df)
# {'signal': '普涨', 'up_ratio': 85.2, ...}
```

---

### capital-flow-analysis

**功能**: 资金流向分析

```python
from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis import (
    get_market_fund_flow, get_north_bound_today,
    get_north_bound_flow, get_stock_fund_flow
)

# 大盘资金流 (主力/超大单/大单/中单/小单)
mf = get_market_fund_flow()
# {'上证': {...}, '深证': {...}}

# 北向资金 (沪股通+深股通)
nb_today = get_north_bound_today()
nb_hist = get_north_bound_flow(days=30)

# 个股资金流
stock_flow = get_stock_fund_flow("000001", days=10)
```

---

### dragon-tiger-analysis

**功能**: 龙虎榜分析

```python
from skills.03-market-analysis.dragon-tiger-analysis.dragon_tiger_analysis import (
    get_lhb_detail, track_hot_money,
    get_institution_summary, lhb_daily_report
)

# 龙虎榜明细
detail = get_lhb_detail("2024-12-30")

# 知名游资追踪 (含40+ 知名席位)
hot = track_hot_money("2024-12-30")

# 机构席位
inst = get_institution_summary("2024-12-30")

# 每日龙虎榜报告
report = lhb_daily_report()
# {'summary': {...}, 'detail': df, 'hot_money': df, ...}
```

**知名游资词典**: 方新侠/作手新一/赵老哥/章盟主/炒股养家/佛山系 等

---

## Layer 4: 个股分析层

### limit-up-tracker

**功能**: 涨停板追踪

```python
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import (
    get_zt_pool, get_consecutive_zt,
    evaluate_zt_strength, calc_break_rate,
    summarize_zt_reasons, zt_daily_report
)

# 涨停板池
zt = get_zt_pool("20241230")
# 字段: code, name, pct_change, consecutive, reason, limit_funds, ...

# 连板梯队
cons = get_consecutive_zt(days=5)
# 1板/2板/3板/4板/5+板 各自多少只

# 个股涨停强度评估
strength = evaluate_zt_strength(row)
# {'score': 5, 'level': '强', 'factors': [...]}

# 炸板率
br = calc_break_rate("20241230")
# {'zt_count': 56, 'zb_count': 78, 'broken': 22, 'break_rate': 28.2}

# 涨停原因归类
reasons = summarize_zt_reasons(zt)
# AI/科技 12, 新能源 8, ...

# 综合日报
report = zt_daily_report()
```

**强度评分维度** (满分10):
- 封单金额 (2分)
- 封板时间 (2分)
- 炸板次数 (1分)
- 连板数 (2分)
- 流通市值 (1分)
- 题材热度 (2分)

---

### stock-technical-analysis

**功能**: 个股技术面分析

```python
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import (
    get_kline, full_technical_analysis,
    detect_candlestick_patterns, analyze_trend,
    detect_overbought_oversold, calc_support_pressure,
    generate_trading_signal
)

# K线数据
df = get_kline("000001", period="daily", days=120, adjust="qfq")

# 综合分析
result = full_technical_analysis("000001")
# {
#   'patterns': [K线形态...],
#   'trend': {趋势, 评分, 信号列表},
#   'overbought_oversold': {KDJ, RSI, 等级},
#   'support_pressure': {R1, R2, S1, S2},
#   'trading_signal': {signal, strength, 买入/卖出信号列表}
# }

# K线形态识别
patterns = detect_candlestick_patterns(df)
# 十字星, 锤子线, 吞没形态, 早晨之星...

# 趋势
trend = analyze_trend(df)
# {'trend': '上涨', 'score': 4, 'signals': [...]}

# 超买超卖
obs = detect_overbought_oversold(df)
# {'level': '超买', 'K': 88, 'D': 85, 'J': 95, 'RSI6': 82}
```

**K线形态**: 十字星/锤子线/吞没形态/早晨之星/黄昏之星
**指标体系**: MA/MACD/KDJ/RSI/BOLL

---

### stock-fundamental-analysis

**功能**: 个股基本面分析

```python
from skills.04-stock-analysis.stock-fundamental-analysis.stock_fundamental_analysis import (
    full_fundamental_analysis, get_financial_indicator,
    analyze_profitability, analyze_growth,
    analyze_valuation, analyze_financial_health
)

# 综合分析
result = full_fundamental_analysis("000001")
# {
#   'profitability': {ROE, ROA, 毛利率, 净利率},
#   'growth': {营收增长, 利润增长, EPS增长},
#   'valuation': {PE, PB, PS},
#   'health': {资产负债率, 流动比率},
#   'score': 75.5,  # 综合分
#   'rating': '良'  # 优/良/中/差
# }

# 单维度
prof = analyze_profitability(fin_df)
growth = analyze_growth(fin_df)
val = analyze_valuation("000001")
health = analyze_financial_health(fin_df)
```

**评分维度**:
- 盈利能力 (30%)
- 成长性 (30%)
- 估值合理性 (20%)
- 财务健康度 (20%)

---

## Layer 5: 报告层

### daily-market-report

**功能**: 一键生成每日复盘报告

```python
from skills.05-reports.daily-market-report.daily_market_report import (
    generate_daily_report, build_market_section,
    build_sector_section, build_zt_section,
    build_capital_section, build_lhb_section
)

# 一键生成
report = generate_daily_report()
# 自动保存为 daily_report_YYYY-MM-DD.md

# 单独构建某部分
market_md = build_market_section()
sector_md = build_sector_section()
zt_md = build_zt_section("20241230")
```

**报告结构**:
1. 📊 大盘表现 (指数/广度/趋势)
2. 🔥 板块热点 (涨幅榜/资金榜/主线)
3. 🚀 涨停板 (统计/连板/原因/Top10)
4. 💰 资金流向 (北向/主力)
5. 🐉 龙虎榜 (游资/机构)

---

## 🔧 进阶使用

### 自定义数据源

```python
from skills.01-infra.astock-data-source.astock_data_source import DataSourceManager

m = DataSourceManager(tushare_token="xxx", primary="akshare")

# 调用指定数据源
df = m.call("akshare", "stock_zh_a_spot")

# 失败自动降级
df = m.call("tushare", "daily", ts_code="000001.SZ")
```

### 扩展新的数据源

```python
from skills.01-infra.astock-data-source.astock_data_source import with_retry, with_rate_limit

class MyDataSource:
    def __init__(self):
        # 初始化
        pass

    @with_retry(max_retries=3)
    @with_rate_limit(2.0)
    def my_method(self):
        # 你的实现
        pass
```

### 与 LLM 集成

在 Claude Code 中, 可以让 AI 直接调用这些 Skills:

```python
# AI 可以这样组合使用
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
from skills.02-data-collection.stock-news-collector.stock_news_collector import get_stock_news, summarize_sentiment

code = "000001"
tech = full_technical_analysis(code)
news = get_stock_news(code)
sentiment = summarize_sentiment(news)

# 然后让 AI 基于这些数据给出投资建议
```

---

## 💡 最佳实践

1. **数据采集层用 akshare 即可**, 除非 akshare 没有数据再考虑 tushare
2. **请求加缓存**: 短期不需要重复请求的数据应缓存
3. **错峰请求**: 大盘分析尽量在收盘后做, 避免交易时段接口压力大
4. **组合使用**: 单一 Skill 价值有限, 组合多个 Skill 才有威力
5. **配合 LLM**: 用 AI 调用这些 Skills 可以发挥最大价值

---

## ❓ 遇到问题?

- 查看 [常见问题](./04-best-practices.md#常见问题)
- 提交 [GitHub Issue](https://github.com/ZICXR/A-Stock-Skills/issues)
