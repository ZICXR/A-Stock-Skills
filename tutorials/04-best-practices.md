# 🏆 最佳实践

> A-Stock-Skills 高效使用指南

## 目录

- [使用原则](#使用原则)
- [性能优化](#性能优化)
- [错误处理](#错误处理)
- [安全合规](#安全合规)
- [常见问题](#常见问题)

---

## 使用原则

### ✅ DO - 推荐做法

1. **组合使用 Skills, 而非依赖单一 Skill**
   ```python
   # ✅ 好的做法: 多维度分析
   tech = full_technical_analysis(code)
   fund = full_fundamental_analysis(code)
   flow = get_stock_fund_flow(code)
   ```

2. **利用缓存避免重复请求**
   ```python
   # ✅ 同一会话内复用结果
   from skills.01-infra.astock_data_source.astock_data_source import get_manager
   m = get_manager()  # 单例, 内置5分钟缓存
   ```

3. **设置合理的请求间隔**
   ```python
   # ✅ 批量分析时加延迟
   for code in codes:
       result = full_technical_analysis(code)
       time.sleep(0.5)  # 避免触发限流
   ```

4. **捕获异常保证流程完整**
   ```python
   # ✅ 容错处理
   try:
       data = get_stock_news(code)
   except Exception as e:
       logger.warning(f"获取新闻失败: {e}")
       data = pd.DataFrame()
   ```

5. **结合 LLM 做决策**
   ```python
   # ✅ 让 AI 基于数据做决策
   tech = full_technical_analysis(code)
   prompt = f"基于以下数据给出投资建议:\n{tech}"
   # advice = call_llm(prompt)
   ```

### ❌ DON'T - 应避免

1. **不要在交易时段高频请求**
   ```python
   # ❌ 错误: 每秒请求一次
   while True:
       data = get_market_breadth()
       time.sleep(1)  # 会触发限流
   ```

2. **不要无脑相信单一指标**
   ```python
   # ❌ 错误: 仅看 MACD 金叉就买入
   if macd_golden_cross:
       buy()  # 至少还要看趋势、量价、基本面
   ```

3. **不要忽视数据时间**
   ```python
   # ❌ 错误: 不看数据日期
   data = get_kline(code)  # 可能是过时的数据
   # 应检查 data.iloc[-1]['date'] 确认是最新
   ```

4. **不要使用本工具作为投资唯一依据**
   ```python
   # ❌ 错误: 严格按工具信号操作
   # 工具仅辅助决策, 需结合自己的判断
   ```

---

## 性能优化

### 1. 批量数据获取

```python
# ✅ 一次性获取多只股票基础信息
from skills.02-data-collection.stock-basic-info.stock_basic_info import get_stock_realtime
from skills.01-infra.astock-data-source.astock_data_source import get_manager

m = get_manager()
all_stocks = m.akshare.stock_zh_a_spot()  # 一次请求, 5000+ 只股票

# 再单独处理
for code in watch_list:
    rt = all_stocks[all_stocks["代码"] == code]
```

### 2. 异步处理 (高级)

```python
import asyncio
import aiohttp

async def fetch_stock(code):
    """异步获取单只股票"""
    async with aiohttp.ClientSession() as session:
        # 实际使用 akshare 还是同步, 但可以在线程池中执行
        pass

# 大量股票时考虑用多线程
from concurrent.futures import ThreadPoolExecutor

def batch_analyze(codes, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(full_technical_analysis, codes))
    return results
```

### 3. 缓存策略

```python
# 项目内置 5 分钟缓存
# 如需更长缓存, 可自定义:

import diskcache
cache = diskcache.Cache("./my_cache")

@cache.memoize(expire=3600)  # 1小时
def get_financial_indicator_cached(code):
    return get_financial_indicator(code)
```

---

## 错误处理

### 常见错误及处理

```python
import logging
logger = logging.getLogger(__name__)

# 1. 网络超时
try:
    df = ak.stock_zh_a_spot()
except requests.exceptions.Timeout:
    logger.error("请求超时, 请重试")
    df = pd.DataFrame()

# 2. 接口变更 (akshare 经常更新)
try:
    df = get_zt_pool()
except AttributeError as e:
    logger.error(f"akshare 接口可能变更: {e}")
    # 降级方案
    df = pd.DataFrame()

# 3. 非交易日
if df.empty:
    print("可能为非交易日, 或接口临时不可用")

# 4. 代码错误
try:
    normalize_stock_code("ABC")
except ValueError as e:
    print(f"代码错误: {e}")
```

### 项目自带容错

所有 Skills 都内置:
- ✅ 自动重试 (3次)
- ✅ 限流控制
- ✅ 异常捕获
- ✅ 降级到其他数据源

---

## 安全合规

### ⚠️ 重要提醒

1. **本项目仅供学习研究使用**, 不构成投资建议
2. **不应用于实盘交易决策** (除非你完全理解风险)
3. **数据来源于公开 API**, 准确性以官方为准
4. **遵守 API 服务条款**, 不要恶意高频请求

### 数据使用建议

```python
# ✅ 合理使用
- 研究目的: ✅
- 学习目的: ✅
- 回测验证: ✅
- 实盘参考: ⚠️ (谨慎)

# ❌ 禁止使用
- 商业转售数据
- 高频恶意请求
- 违法违规用途
```

### 法律责任

```
本项目开发者不对因使用本工具造成的任何投资损失负责。
投资有风险, 决策需谨慎。
```

---

## 配合 LLM 使用

### 推荐: Claude Code

[Claude Code](https://claude.com/claude-code) 是 Anthropic 官方的 AI CLI 工具, 非常适合调用这些 Skills:

```bash
# 安装
npm install -g @anthropic-ai/claude-code

# 在项目目录中启动
cd A-Stock-Skills
claude
```

**示例对话**:

> @Claude 用 daily-market-report 帮我生成今天的复盘
> 
> @Claude 帮我用 stock-technical-analysis 分析一下 000001
> 
> @Claude 综合 market-analysis 和 sector-analysis 给出今天的操作建议

Claude 会自动:
1. 找到对应的 Skill
2. 调用相应的函数
3. 解读结果
4. 给出建议

---

## 数据源选择

### akshare vs tushare vs 东财

| 数据源 | 优势 | 劣势 | 适用场景 |
|--------|------|------|----------|
| **akshare** | 免费、覆盖全、社区活跃 | 偶尔接口变动 | 默认首选 |
| **tushare** | 数据质量高、稳定 | 需要token/积分 | 财务数据、回测 |
| **东财直连** | 实时性好 | 需自己处理 | 盘中监控 |

**建议**:
- 90% 场景用 akshare 即可
- 财务数据用 tushare
- 盘中监控可用东财直连

---

## 代码组织建议

### 个人项目

```
my_a_stock_project/
├── A-Stock-Skills/      # 本项目作为 submodule
├── strategies/          # 你的策略
│   ├── limit_up.py
│   └── rotation.py
├── config.py            # 自定义配置
└── main.py              # 主入口
```

### 团队项目

```
team_a_stock/
├── core/                # 内部核心代码
├── skills/              # 引用 A-Stock-Skills
├── tests/               # 测试
├── docs/                # 文档
└── README.md
```

---

## 测试

### 快速测试所有 Skills

```python
"""test_all_skills.py - 测试所有 Skills 是否可用"""
import sys
sys.path.insert(0, ".")

def test_data_source():
    from skills.01-infra.astock-data-source.astock_data_source import health_check
    status = health_check()
    assert any(status.values()), "至少一个数据源可用"
    print(f"✅ data-source: {status}")

def test_market_breadth():
    from skills.02-data-collection.market-data-collector.market_data_collector import get_market_breadth
    breadth = get_market_breadth()
    print(f"✅ market-breadth: {breadth.get('up', 0)} 只上涨")

def test_zt_pool():
    from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import get_zt_pool
    zt = get_zt_pool()
    print(f"✅ zt-pool: {len(zt)} 只涨停")

# ... 更多测试

if __name__ == "__main__":
    test_data_source()
    test_market_breadth()
    test_zt_pool()
    print("\n所有测试通过!")
```

---

## 常见问题 (FAQ)

### Q1: 报错 "ModuleNotFoundError: No module named 'akshare'"

```bash
pip install akshare
# 或指定版本
pip install akshare>=1.12.0
```

### Q2: akshare 接口报错 "AttributeError"

akshare 接口经常更新, 可:
```bash
pip install -U akshare
```

或参考我们的 [astock-data-source Skill](./02-skill-usage.md#astock-data-source) 提供的统一接口和降级机制。

### Q3: Tushare 提示 "请设置正确的 token"

```bash
# 设置环境变量
export TUSHARE_TOKEN="your_token"

# 或在代码中
import tushare as ts
ts.set_token("your_token")
```

**注意**: Tushare 大部分接口需要**积分**才可使用, 建议先注册并积累积分。

### Q4: 数据返回空

可能原因:
- 非交易日
- 接口临时故障
- 代码格式错误
- 权限不足 (tushare)

### Q5: 如何提高分析速度?

- 减少分析股票数量
- 减少 K 线天数
- 启用缓存
- 错峰运行

### Q6: 报告中数据有误差?

- 数据源本身有时延/差异
- 复权方式不同 (前/后复权)
- 建议以官方数据为准

---

## 进阶玩法

### 1. 接入消息推送

```python
import requests

def send_wechat(content, webhook_url):
    """企业微信推送"""
    requests.post(webhook_url, json={
        "msgtype": "markdown",
        "markdown": {"content": content}
    })

def send_dingtalk(content, webhook_url):
    """钉钉推送"""
    requests.post(webhook_url, json={
        "msgtype": "markdown",
        "markdown": {"title": "A股日报", "text": content}
    })
```

### 2. 定时任务

```python
import schedule
import time

# 每个交易日 15:30 生成报告
schedule.every().monday.at("15:30").do(generate_daily_report)
schedule.every().tuesday.at("15:30").do(generate_daily_report)
# ...

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. Web 界面 (Streamlit)

```python
import streamlit as st
from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report

st.title("📈 A股分析平台")
if st.button("生成今日复盘"):
    report = generate_daily_report()
    st.markdown(report)
```

---

## 贡献指南

### 如何贡献新 Skill

1. 在 `skills/` 对应层级创建新目录
2. 实现 `xxx.py` 主文件
3. 编写 `SKILL.md` 文档
4. 添加 `__init__.py` (可选)
5. 更新本 README 的 Skill 目录
6. 提交 PR

### 命名规范

- 目录名: 小写中划线, 如 `dragon-tiger-analysis`
- 主文件名: 同目录名, 如 `dragon_tiger_analysis.py` (下划线)
- 函数名: 动词开头, 如 `get_lhb_detail`

---

## 反馈与支持

- 🐛 报告 Bug: [GitHub Issues](https://github.com/ZICXR/A-Stock-Skills/issues)
- 💡 功能建议: [GitHub Discussions](https://github.com/ZICXR/A-Stock-Skills/discussions)
- ⭐ 觉得有用: 给个 Star ⭐

---

**🎓 祝你在 A 股市场用好这套工具, 投资顺利!**
