# 🚀 快速上手指南

> 30分钟掌握 A-Stock-Skills

## 📋 目录

- [环境准备](#环境准备)
- [第一个程序](#第一个程序)
- [5大常用场景](#5大常用场景)
- [进阶组合用法](#进阶组合用法)

---

## 环境准备

### 1. 安装 Python

需要 Python 3.8 或更高版本。

```bash
python --version
```

### 2. 克隆项目

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install akshare tushare pandas numpy requests
```

### 4. (可选) 配置 Tushare Token

Tushare 提供更高质量的数据, 但 akshare 已能覆盖 90%+ 需求。

```bash
# Linux/Mac
export TUSHARE_TOKEN="your_token_here"

# Windows PowerShell
$env:TUSHARE_TOKEN = "your_token_here"

# Windows CMD
set TUSHARE_TOKEN=your_token_here
```

---

## 第一个程序

创建一个 `test.py`：

```python
import sys
sys.path.insert(0, ".")

# 获取平安银行(000001)实时行情
from skills.02-data-collection.stock-basic-info.stock_basic_info import get_stock_realtime

info = get_stock_realtime("000001")
print(f"股票名称: {info['name']}")
print(f"最新价: {info['price']}")
print(f"涨跌幅: {info['pct_change']}%")
```

运行：

```bash
python test.py
```

预期输出：

```
股票名称: 平安银行
最新价: 12.34
涨跌幅: 1.25%
```

✅ **恭喜! 你已成功运行 A-Stock-Skills**

---

## 5大常用场景

### 场景 1: 查看大盘走势

```python
from skills.03-market-analysis.market-analysis.market_analysis import full_market_analysis

# 分析上证指数
result = full_market_analysis("000001", days=60)

print(f"趋势: {result['trend']['overall']}")
print(f"建议: {result['advice']}")
print(f"信号:")
for s in result['trend']['signals']:
    print(f"  - {s['name']}: {s['desc']}")
```

### 场景 2: 找涨停板强势股

```python
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import (
    get_zt_pool, evaluate_zt_strength
)

# 获取当日涨停板
zt_df = get_zt_pool()
print(f"今日涨停数: {len(zt_df)}")

# 评估每只涨停股强度
for _, row in zt_df.iterrows():
    strength = evaluate_zt_strength(row)
    if strength['score'] >= 4:  # 强涨停
        print(f"{row['name']} 强度: {strength['level']} ({strength['score']}分)")
        print(f"  因素: {', '.join(strength['factors'])}")
```

### 场景 3: 追踪主力资金

```python
from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis import (
    get_market_fund_flow, get_north_bound_today
)

# 大盘资金流
mf = get_market_fund_flow()
print("大盘资金流:")
for market, data in mf.items():
    print(f"  {market} 主力净流入: {data.get('main_net', 0)}")

# 北向资金
nb = get_north_bound_today()
print(f"\n北向资金: {nb}")
```

### 场景 4: 板块轮动分析

```python
from skills.03-market-analysis.sector-analysis.sector_analysis import (
    identify_main_themes, top_fund_inflow
)

# 主线板块
themes = identify_main_themes(top_n=5)
print("=== 当前主线板块 ===")
for t in themes.get("main_themes", [])[:5]:
    print(f"[{t['type']}] {t['name']}: {t.get('pct_change', 0):.2f}%")

# 资金流入 Top 5
print("\n=== 3日资金流入 Top 5 ===")
inflow = top_fund_inflow(period="3日", top_n=5)
print(inflow[["name", "pct_change", "main_net"]])
```

### 场景 5: 一键生成每日复盘报告

```python
from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report

# 生成今日复盘报告
report = generate_daily_report()
# 自动保存为 daily_report_YYYY-MM-DD.md
print("报告生成完毕! 请查看 daily_report_*.md")
```

---

## 进阶组合用法

### 组合 1: 个股深度研究

```python
from skills.02-data-collection.stock-basic-info.stock_basic_info import get_stock_card
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
from skills.04-stock-analysis.stock-fundamental-analysis.stock_fundamental_analysis import full_fundamental_analysis
from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis import get_stock_fund_flow

code = "000001"
print(f"=== {code} 深度研究 ===\n")

# 基础信息
card = get_stock_card(code)
print(f"公司: {card['basic'].get('股票简称', card['realtime'].get('name'))}")
print(f"行业: {card['basic'].get('行业', 'N/A')}")
print(f"现价: {card['realtime'].get('price')}")

# 技术面
tech = full_technical_analysis(code)
print(f"\n技术面: {tech['trading_signal']['signal']} ({tech['trading_signal']['strength']})")

# 基本面
fund = full_fundamental_analysis(code)
print(f"基本面: {fund['rating']} (评分: {fund['score']})")

# 资金面
flow = get_stock_fund_flow(code, days=5)
print(f"资金面: 5日资金流数据 {len(flow)} 条")
```

### 组合 2: 涨停+龙虎榜联动

```python
from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import get_zt_pool
from skills.03-market-analysis.dragon-tiger-analysis.dragon_tiger_analysis import get_lhb_detail

# 涨停股
zt = get_zt_pool()
zt_codes = set(zt["code"].tolist()) if "code" in zt.columns else set()

# 龙虎榜
lhb = get_lhb_detail()
if not lhb.empty and "代码" in lhb.columns:
    lhb_codes = set(lhb["代码"].astype(str).tolist())

    # 涨停 + 龙虎榜交集
    both = zt_codes & lhb_codes
    print(f"涨停且上榜: {len(both)} 只")
    for code in both:
        name = zt[zt["code"] == code]["name"].iloc[0] if "name" in zt.columns else ""
        print(f"  {code} {name}")
```

### 组合 3: 自定义选股策略

```python
from skills.01-infra.astock-utils.astock_utils import add_all_indicators
from skills.02-data-collection.stock-basic-info.stock_basic_info import get_stock_realtime
import akshare as ak

# 策略: MACD金叉 + 放量 + 站上20日均线
candidates = []

# 获取全A股
df = ak.stock_zh_a_spot_em()
for _, row in df.head(50).iterrows():  # 演示只取前50
    code = row["代码"]
    try:
        hist = ak.stock_zh_a_hist(symbol=code, period="daily",
                                  start_date="20240101",
                                  end_date="20241231",
                                  adjust="qfq")
        hist = add_all_indicators(hist)
        if len(hist) < 30:
            continue
        last = hist.iloc[-1]
        prev = hist.iloc[-2]

        # 条件: MACD金叉 + 放量 + close>MA20
        if (last["DIF"] > last["DEA"] and prev["DIF"] <= prev["DEA"] and
            last["volume"] > hist["volume"].tail(5).mean() * 1.5 and
            last["close"] > last["MA20"]):
            candidates.append({
                "code": code,
                "name": row["名称"],
                "price": last["close"],
                "pct_change": row["涨跌幅"]
            })
    except:
        continue

print(f"找到 {len(candidates)} 只符合条件的股票")
for c in candidates[:10]:
    print(c)
```

---

## ⚠️ 常见问题

### Q1: 报错 "ModuleNotFoundError: No module named 'akshare'"

```bash
pip install akshare
```

### Q2: 接口调用失败/超时

- 检查网络
- akshare 接口偶有调整, 可升级: `pip install -U akshare`
- 项目已内置重试和降级机制

### Q3: Tushare 接口报 token 错误

Tushare 需要注册并获取 token, 但 **akshare 已能满足大部分需求**。

### Q4: 数据返回空 DataFrame

- 可能是非交易日
- 检查代码是否正确 (6位, 不带前缀)

---

## 📚 下一步

- 📖 [Skill 详细使用手册](./02-skill-usage.md)
- 📖 [实战案例集](./03-workflow-examples.md)
- 📖 [最佳实践](./04-best-practices.md)

---

💡 **提示**: 建议配合 [Claude Code](https://claude.com/claude-code) 或其他 AI 工具使用, 可以让 AI 直接调用这些 Skills 完成分析任务!
