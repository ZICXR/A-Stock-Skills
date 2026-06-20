# 🎯 实战案例集

> 8个真实场景的完整工作流

## 目录

1. [每日盘后自动复盘](#1-每日盘后自动复盘)
2. [涨停打板策略研究](#2-涨停打板策略研究)
3. [强势板块追踪系统](#3-强势板块追踪系统)
4. [北向资金异动监控](#4-北向资金异动监控)
5. [个股深度研究报告](#5-个股深度研究报告)
6. [量化选股器](#6-量化选股器)
7. [游资动向追踪](#7-游资动向追踪)
8. [AI 智能投顾组合](#8-ai-智能投顾组合)

---

## 1. 每日盘后自动复盘

**场景**: 每个交易日 15:30 自动生成复盘报告, 推送给自己

```python
import schedule
import time
from datetime import datetime
from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report

def daily_review_job():
    """盘后复盘任务"""
    print(f"[{datetime.now()}] 开始生成每日复盘报告...")
    report = generate_daily_report()
    # 推送到微信/邮箱/钉钉
    send_to_me(report)

def send_to_me(content):
    """推送到自己"""
    # 实际场景: 通过微信/邮件 webhook
    import requests
    webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
    requests.post(webhook, json={"markdown": {"content": content[:4096]}})

# 每个交易日 15:30 执行
schedule.every().monday.at("15:30").do(daily_review_job)
schedule.every().tuesday.at("15:30").do(daily_review_job)
schedule.every().wednesday.at("15:30").do(daily_review_job)
schedule.every().thursday.at("15:30").do(daily_review_job)
schedule.every().friday.at("15:30").do(daily_review_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 2. 涨停打板策略研究

**场景**: 研究"什么样的涨停板次日溢价最高"

```python
import pandas as pd
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import (
    get_zt_pool, evaluate_zt_strength, get_consecutive_zt
)
from skills.03-market-analysis.dragon-tiger-analysis.dragon_tiger_analysis import track_hot_money
from datetime import datetime, timedelta

# 收集近30天涨停数据, 统计次日收益
results = []
for i in range(30):
    date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
    zt = get_zt_pool(date)
    if zt.empty:
        continue

    for _, row in zt.iterrows():
        # 评估强度
        strength = evaluate_zt_strength(row)

        # 是否有游资参与
        hot_money = track_hot_money(date)
        has_hot_money = (
            not hot_money.empty and
            "代码" in hot_money.columns and
            row["code"] in hot_money["代码"].astype(str).values
        )

        results.append({
            "date": date,
            "code": row["code"],
            "name": row["name"],
            "consecutive": row.get("consecutive", 1),
            "strength_score": strength["score"],
            "strength_level": strength["level"],
            "has_hot_money": has_hot_money,
            "limit_funds": row.get("limit_funds", 0),
        })

df = pd.DataFrame(results)
print("=== 涨停板特征分析 ===")
print(f"样本数: {len(df)}")
print(f"\n强度分布:")
print(df["strength_level"].value_counts())
print(f"\n游资参与比例: {df['has_hot_money'].mean()*100:.1f}%")
print(f"\n连板数分布:")
print(df["consecutive"].value_counts().sort_index())
```

---

## 3. 强势板块追踪系统

**场景**: 找出当前市场最热的3个板块及龙头股

```python
from skills.03-market-analysis.sector-analysis.sector_analysis import (
    identify_main_themes, top_fund_inflow
)
from skills.02-data-collection.sector-data-collector.sector_data_collector import get_sector_stocks

# 1. 识别主线
themes = identify_main_themes(top_n=3)
print("=== 当前 3 大主线板块 ===\n")
for i, t in enumerate(themes.get("main_themes", [])[:3], 1):
    print(f"{i}. {t['name']} ({t['type']})")
    print(f"   涨幅: {t.get('pct_change', 0):.2f}%")
    print(f"   资金流入: {t.get('main_net', 0)/1e8:.2f}亿")

# 2. 找龙头
for t in themes.get("main_themes", [])[:3]:
    print(f"\n=== {t['name']} 龙头股 ===")
    # 通过成分股API找 (需要板块代码)
    # 简化: 直接用 leader 字段
    print(f"领涨股: {t.get('leader', 'N/A')} ({t.get('pct_change', 0):.2f}%)")

# 3. 持续资金流入
print("\n=== 3日资金流入 TOP 5 ===")
flow_3d = top_fund_inflow("3日", "industry", top_n=5)
print(flow_3d[["name", "pct_change", "main_net"]])
```

---

## 4. 北向资金异动监控

**场景**: 北向资金单日净流入/流出超 50亿时报警

```python
import time
from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis import (
    get_north_bound_today, get_north_bound_flow
)

def check_north_bound_signal():
    """检查北向资金异动"""
    nb = get_north_bound_today()
    if not nb:
        return

    # 提取北向资金净流入
    net = nb.get("资金净流入", nb.get("net_inflow", 0))
    try:
        net = float(net)
    except:
        return

    # 异动阈值
    THRESHOLD = 50e8  # 50亿

    if net > THRESHOLD:
        send_alert(f"🚨 北向资金大幅流入: {net/1e8:.2f}亿")
    elif net < -THRESHOLD:
        send_alert(f"🚨 北向资金大幅流出: {net/1e8:.2f}亿")

    # 历史趋势
    hist = get_north_bound_flow(days=10)
    if not hist.empty and "net_inflow" in hist.columns:
        avg_10d = hist["net_inflow"].mean()
        if net > avg_10d * 3:
            send_alert(f"📈 北向资金: 今日{net/1e8:.2f}亿, 远超10日均{avg_10d/1e8:.2f}亿")

def send_alert(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    # 实际: 发送微信/邮件通知

# 盘中定时检查 (每30分钟)
import schedule
schedule.every(30).minutes.do(check_north_bound_signal)
```

---

## 5. 个股深度研究报告

**场景**: 对一只股票生成完整的研究报告(技术+基本面+资金+情绪)

```python
from skills.02-data-collection.stock-basic-info.stock_basic_info import (
    get_stock_realtime, get_stock_info, get_top_holders
)
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
from skills.04-stock-analysis.stock-fundamental-analysis.stock_fundamental_analysis import full_fundamental_analysis
from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis import get_stock_fund_flow
from skills.02-data-collection.stock-news-collector.stock_news_collector import get_stock_news, summarize_sentiment
from skills.02-data-collection.announcement-collector.announcement_collector import get_stock_announcements, filter_key_announcements

def deep_research(code: str) -> str:
    """个股深度研究"""
    report = f"# 个股深度研究报告: {code}\n\n"

    # 1. 基础信息
    rt = get_stock_realtime(code)
    info = get_stock_info(code)
    report += f"## 📌 基础信息\n"
    report += f"- 名称: {rt.get('name', info.get('股票简称', ''))}\n"
    report += f"- 行业: {info.get('所属行业', info.get('行业', 'N/A'))}\n"
    report += f"- 上市日期: {info.get('上市日期', 'N/A')}\n"
    report += f"- 总股本: {info.get('总股本', 'N/A')}\n"
    report += f"- 现价: {rt.get('price', 'N/A')}\n"
    report += f"- 涨跌幅: {rt.get('pct_change', 'N/A')}%\n"
    report += f"- PE(TTM): {rt.get('pe', 'N/A')}\n"
    report += f"- PB: {rt.get('pb', 'N/A')}\n\n"

    # 2. 技术面
    tech = full_technical_analysis(code)
    report += f"## 📈 技术面\n"
    report += f"- 趋势: **{tech['trend']['trend']}** (评分: {tech['trend']['score']})\n"
    report += f"- 交易信号: **{tech['trading_signal']['signal']}** ({tech['trading_signal']['strength']})\n"
    if tech['overbought_oversold']['level'] != '中性':
        report += f"- 超买超卖: {tech['overbought_oversold']['level']}\n"
    report += f"\n关键信号:\n"
    for s in tech['trend']['signals'][:5]:
        report += f"  - {s['name']}: {s['desc']}\n"
    report += "\n"

    # 3. 基本面
    fund = full_fundamental_analysis(code)
    report += f"## 💼 基本面\n"
    report += f"- 综合评分: **{fund['score']}** ({fund['rating']})\n"
    report += f"- 财务健康: {fund['health'].get('level', 'N/A')}\n"
    if fund['health'].get('issues'):
        report += f"- ⚠️ 关注点: {', '.join(fund['health']['issues'])}\n"
    report += "\n"

    # 4. 资金面
    flow = get_stock_fund_flow(code, days=5)
    report += f"## 💰 资金面 (近5日)\n"
    if not flow.empty:
        cols = [c for c in ["日期", "主力净流入-净额"] if c in flow.columns]
        report += flow[cols].to_markdown() if hasattr(flow, 'to_markdown') else flow[cols].to_string()
    report += "\n\n"

    # 5. 新闻情绪
    news = get_stock_news(code, max_count=20)
    sent = summarize_sentiment(news)
    report += f"## 📰 舆情\n"
    report += f"- 情绪: **{sent.get('label', 'N/A')}** (分数: {sent.get('score', 0)})\n"
    report += f"- 利好新闻: {sent.get('positive', 0)} 条\n"
    report += f"- 利空新闻: {sent.get('negative', 0)} 条\n\n"

    # 6. 关键公告
    ann = get_stock_announcements(code, max_count=20)
    key_ann = filter_key_announcements(ann)
    report += f"## 📋 关键公告 (近20条)\n"
    if not key_ann.empty:
        cols = [c for c in ["date", "title"] if c in key_ann.columns]
        for _, row in key_ann[cols].head(5).iterrows():
            report += f"- {row.get('date', '')}: {row.get('title', '')}\n"
    report += "\n"

    # 7. 投资建议
    tech_signal = tech['trading_signal']['signal']
    fund_rating = fund['rating']
    sent_label = sent.get('label', 'neutral')

    report += f"## 🎯 投资建议\n\n"
    if tech_signal == "买入" and fund_rating in ("优", "良") and sent_label in ("positive", "very_positive"):
        advice = "✅ **积极配置**: 技术面、基本面、舆情均向好, 建议关注"
    elif tech_signal == "买入" and fund_rating in ("优", "良"):
        advice = "👍 **逢低关注**: 基本面良好, 技术面有买点"
    elif tech_signal == "卖出":
        advice = "❌ **回避**: 技术面发出卖出信号"
    else:
        advice = "⚠️ **观望**: 多空因素交织, 建议等待明确信号"
    report += f"{advice}\n\n"

    report += "---\n"
    report += "⚠️ 本报告由程序自动生成, 不构成投资建议, 投资有风险, 入市需谨慎。\n"

    return report


# 使用
report = deep_research("000001")
print(report)

# 保存
with open(f"research_000001.md", "w", encoding="utf-8") as f:
    f.write(report)
```

---

## 6. 量化选股器

**场景**: 综合多因子选股 (动量 + 资金 + 涨停 + 突破)

```python
import akshare as ak
from skills.01-infra.astock-utils.astock_utils import add_all_indicators
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import get_zt_pool
from skills.01-infra.astock-data-source.astock_data_source import get_manager

def multi_factor_screener():
    """多因子选股器"""
    # 1. 获取全A股
    m = get_manager()
    all_stocks = m.akshare.stock_zh_a_spot()
    candidates = []

    # 2. 多因子筛选
    for _, row in all_stocks.iterrows():
        code = str(row["代码"])
        try:
            # 排除ST/停牌
            name = str(row.get("名称", ""))
            if name.startswith(("ST", "*ST", "N", "C")) or row.get("最新价", 0) == 0:
                continue

            # 排除小市值(<20亿)和大盘股(>2000亿)
            total_mv = float(row.get("总市值", 0))
            if total_mv < 20e8 or total_mv > 2000e8:
                continue

            # 排除成交额过小
            amount = float(row.get("成交额", 0))
            if amount < 5e7:  # <5000万
                continue

            # 获取K线
            df = m.akshare.stock_zh_a_hist(symbol=code, period="daily",
                                            start_date="20240101",
                                            end_date="20241230",
                                            adjust="qfq")
            if df.empty or len(df) < 60:
                continue

            df = add_all_indicators(df)
            last = df.iloc[-1]

            score = 0
            factors = []

            # 因子1: 趋势(20日均线) - 20%
            if last["close"] > last["MA20"] > last["MA60"]:
                score += 2
                factors.append("站上20/60日均线")

            # 因子2: 动量(20日涨幅) - 20%
            pct_20d = (last["close"] - df.iloc[-21]["close"]) / df.iloc[-21]["close"] * 100
            if 5 < pct_20d < 50:
                score += 2
                factors.append(f"20日涨幅{pct_20d:.1f}%")
            elif pct_20d > 50:
                score += 1  # 涨幅过大降分
                factors.append(f"20日涨幅{pct_20d:.1f}%偏高")

            # 因子3: MACD - 15%
            if last["DIF"] > last["DEA"] and last["MACD"] > 0:
                score += 1.5
                factors.append("MACD红柱")

            # 因子4: 量能 - 15%
            vol_5 = df["volume"].tail(5).mean()
            vol_20 = df["volume"].tail(20).mean()
            if vol_5 > vol_20 * 1.2:
                score += 1.5
                factors.append("近5日放量")

            # 因子5: RSI 适中 - 10%
            rsi = last.get("RSI6", 50)
            if 50 < rsi < 75:
                score += 1
                factors.append(f"RSI={rsi:.0f}适中")

            if score >= 5:
                candidates.append({
                    "code": code,
                    "name": row["名称"],
                    "price": row["最新价"],
                    "pct_change": row["涨跌幅"],
                    "score": score,
                    "factors": factors,
                })
        except Exception as e:
            continue

    # 排序
    candidates.sort(key=lambda x: x["score"], reverse=True)

    print(f"=== 量化选股结果 (Top 20) ===")
    for i, c in enumerate(candidates[:20], 1):
        print(f"\n{i}. {c['code']} {c['name']} ({c['score']:.1f}分)")
        print(f"   现价: {c['price']:.2f} ({c['pct_change']:+.2f}%)")
        print(f"   因子: {', '.join(c['factors'])}")

# 运行
multi_factor_screener()
```

---

## 7. 游资动向追踪

**场景**: 监控知名游资最近5天的操作风格

```python
from datetime import datetime, timedelta
from skills.03-market-analysis.dragon-tiger-analysis.dragon_tiger_analysis import (
    track_hot_money, get_lhb_detail
)
from collections import defaultdict
import pandas as pd

def track_hot_money_behavior():
    """追踪游资行为"""
    all_records = []

    # 收集5天龙虎榜
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        hot = track_hot_money(date)
        if not hot.empty:
            hot["date"] = date
            all_records.append(hot)

    if not all_records:
        print("最近5天无游资上榜")
        return

    df = pd.concat(all_records, ignore_index=True)

    # 统计游资活跃度
    # 这里需要根据实际列名调整
    print(f"=== 5日游资动向 ===")
    print(f"总记录: {len(df)}")

    # 找出热门个股
    if "代码" in df.columns:
        hot_stocks = df["代码"].value_counts().head(10)
        print(f"\n游资重点关注个股:")
        for code, count in hot_stocks.items():
            name = df[df["代码"] == code]["名称"].iloc[0] if "名称" in df.columns else ""
            print(f"  {code} {name}: 出现{count}次")

# track_hot_money_behavior()
```

---

## 8. AI 智能投顾组合

**场景**: 用 Claude AI + Skills 打造智能投顾

```python
"""
在 Claude Code 中, 你可以这样使用:

"@Claude 请帮我做以下分析:
1. 用 sector-analysis 找出当前3大主线板块
2. 每个板块用 stock-technical-analysis 找出技术面最强的1只龙头
3. 对这3只股票做基本面评分
4. 用 daily-market-report 风格输出建议"
"""

# Claude 会自动组合这些 Skills:

from skills.03-market-analysis.sector-analysis.sector_analysis import identify_main_themes
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
from skills.04-stock-analysis.stock-fundamental-analysis.stock_fundamental_analysis import full_fundamental_analysis
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import get_zt_pool

# Step 1: 主线板块
themes = identify_main_themes(top_n=3)
main_sectors = [t for t in themes.get("main_themes", [])[:3]]

# Step 2: 每个板块的龙头 + 涨停
portfolio = []
zt = get_zt_pool()
zt_codes = set(zt["code"].tolist()) if "code" in zt.columns else set()

for sector in main_sectors:
    # Step 3: 找该板块涨停 + 技术面强的股票
    if not zt.empty:
        # 简化: 取该板块涨停的股票
        for _, row in zt.iterrows():
            code = row.get("code")
            if not code:
                continue
            # 技术面
            tech = full_technical_analysis(code)
            # 基本面
            fund = full_fundamental_analysis(code)

            portfolio.append({
                "sector": sector["name"],
                "code": code,
                "name": row.get("name"),
                "tech_score": tech["trend"]["score"],
                "fund_score": fund["score"],
                "composite": (tech["trend"]["score"] + fund["score"]) / 2,
            })

# Step 4: 综合排序
portfolio.sort(key=lambda x: x["composite"], reverse=True)
print("=== AI 智能推荐组合 (Top 5) ===")
for i, p in enumerate(portfolio[:5], 1):
    print(f"{i}. {p['name']}({p['code']}) - {p['sector']}")
    print(f"   技术:{p['tech_score']} 基本:{p['fund_score']} 综合:{p['composite']:.1f}")
```

---

## 💡 进阶玩法

### 玩法 1: 接入 Web 框架 (FastAPI)

```python
from fastapi import FastAPI
from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report

app = FastAPI()

@app.get("/api/daily_report")
def daily_report():
    return {"content": generate_daily_report()}

@app.get("/api/stock/{code}")
def stock_info(code: str):
    # 调用多个 Skills
    pass
```

### 玩法 2: 接入 Notion / 飞书

```python
import requests
from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report

# 推送到 Notion
def push_to_notion(content):
    # Notion API
    pass

# 推送到飞书
def push_to_feishu(content):
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    requests.post(webhook, json={"msg_type": "interactive", "card": {...}})
```

### 玩法 3: 配合 LLM 决策

```python
# 把 Skill 结果喂给 LLM
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis

result = full_technical_analysis("000001")

# 构造 prompt
prompt = f"""
基于以下技术分析数据, 给出投资建议:
{result}

要求:
1. 综合考虑趋势、信号、估值
2. 给出明确的买卖建议
3. 列出关键风险点
"""

# 调用 Claude/GPT
# response = call_llm(prompt)
```

---

## 📚 相关教程

- [快速上手](./01-quickstart.md)
- [Skill 详细使用](./02-skill-usage.md)
- [最佳实践](./04-best-practices.md)
