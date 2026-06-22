# astock-data-source 详细 API

> 📖 完整 API 文档,SKILL.md 之外的详细参考

## 内部架构

### 数据源优先级 (实测排序)

| 优先级 | 数据源 | 域名 | 适用 | 实测可用率 |
|--------|--------|------|------|----------|
| 1️⃣ | ifzq gtimg (腾讯) | ifzq.gtimg.cn | 行情/K线 | 90%+ |
| 2️⃣ | sina hq | hq.sinajs.cn | 行情/全市场列表 | 80%+ |
| 3️⃣ | eastmoney push2his | push2his.eastmoney.com | K线 | 30% |
| 3️⃣ | eastmoney push2 | push2.eastmoney.com | 行情 | 30% |
| 4️⃣ | akshare | 内部聚合 | 各种数据 | 85% |

### Fallback 机制

- 每个数据源连续失败 **3 次** 自动跳过
- 跳过后会**永久禁用** (重启进程恢复)
- 失败计数器是**进程级**的,不是全局

## API 详细

### get_realtime(code)

获取单只股票实时行情。

```python
from skills.01-infra.astock-data-source.main import get_realtime

q = get_realtime("601991")
# 返回:
# {
#   "code": "601991",
#   "name": "大唐发电",
#   "price": 3.20,
#   "pct_change": 5.26,
#   "open": 3.10, "high": 3.25, "low": 3.08,
#   "pre_close": 3.04,
#   "volume": 12345678,        # 成交量 (股)
#   "amount": 39456789.0,      # 成交额 (元)
#   "amount_yi": 3.95,         # 成交额 (亿)
#   "turnover": 1.23,
#   "pe": 18.5, "pb": 0.92,
#   "total_mv": 68900000000,   # 元
#   "total_mv_yi": 68.9,       # 亿
#   "circ_mv": 65000000000,
#   "source": "ifzq_gtimg",    # 数据源标识
# }
```

### get_realtime_all()

获取全 A 股实时行情 (~5000+ 只)。

⚠️ 走 sina Market Center, 不是 push2。

```python
all_stocks = get_realtime_all()
# 返回 DataFrame, ~5028 行
```

### get_kline(code, days=60, adjust="qfq")

获取 K 线数据。

```python
from skills.01-infra.astock-data-source.main import get_kline

df = get_kline("601991", days=60)
# 返回 DataFrame, columns:
# date, open, close, high, low, volume, amount
```

### get_index_realtime()

主要指数实时行情。

### get_stock_info(code)

股票基本信息 (名称/行业/上市日期等)。

### get_news(code)

个股新闻 (走 akshare, 限速较严)。

## 失败处理

### 健康检查

```bash
python main.py healthcheck
```

输出每个数据源是否可用。

### 手动重置失败计数

```python
from skills.01-infra.astock-data-source.main import SOURCE_FAIL_COUNT
SOURCE_FAIL_COUNT.clear()
```

### 强制使用某数据源

```python
import skills.01-infra.astock-data-source.main as ds
# 临时禁用某源
ds.SOURCE_RELIABILITY["eastmoney_push2"] = 0
```

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `ProxyError: 7890` | 代理挡外网 | 关闭代理或换源 |
| `Max retries exceeded` | 东财被风控 | 等待自动切换 |
| `所有数据源失败` | 全封 | 跑 healthcheck 检查 |
| `UnicodeEncodeError` | Windows GBK | 已自动修复 |
| `RemoteDisconnected` | 服务端断连 | 重试 3 次后切源 |
