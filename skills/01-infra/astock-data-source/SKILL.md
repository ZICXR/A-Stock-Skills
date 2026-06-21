---
name: astock-data-source
description: A 股多源数据源统一管理 (v2.0 - 多源 fallback)。当用户需要获取股票行情/K线/财务数据/新闻/公告/资金流等任何 A 股数据,或需要稳定的 API 封装 (含自动重试/限流/降级/缓存) 时,Claude 应优先使用此 Skill。这是其他所有 Skill 的基础数据源。**v2.0 已修复住宅 IP 数据源问题**。
---

# A 股多源数据源管理 Skill (v2.0)

## 何时使用

- 用户需要获取股票数据
- 用户需要稳定的 API 封装
- 用户在住宅网络环境下使用
- 任何需要 A 股数据的 Skill

## ⚠️ 重要更新 (v2.0)

**修复了住宅 IP 数据源被封问题**:

| 优先级 | 数据源 | 实测可用 | 备注 |
|--------|--------|----------|------|
| 1️⃣ | **ifzq gtimg** (腾讯) | ✅ 90%+ | **住宅 IP 首选** |
| 2️⃣ | 新浪 hq.sinajs.cn | ✅ 80%+ | 全市场列表也用这个 |
| 3️⃣ | 东财 push2.eastmoney | ❌ 30% | 经常被封, 仅作备用 |
| 4️⃣ | akshare | ✅ 85% | 聚合源, fallback |

**自动 fallback 机制**:
- 每个数据源连续失败 3 次自动跳过
- 支持多源切换, 不再硬抛"所有数据源失败"
- 修复了 Windows GBK 编码问题
- 修复了 akshare 内部代理问题

## 🏃 快速验证 (网络环境测试)

```bash
# 测试你的网络环境
python main.py healthcheck

# 输出示例:
# === 数据源健康检查 ===
#   ✅ ifzq_gtimg
#   ✅ sina_hq
#   ❌ eastmoney_push2 (被风控, 已自动跳过)
#   ✅ sina 全市场: 5028 只
```

## 提供能力

### 行情
- `get-realtime --code X` - 单股实时 (多源)
- `get-realtime-all` - 全 A 股实时 (用新浪)
- `get-kline --code X --days N` - K 线 (用 ifzq)

### 指数
- `get-index-realtime` - 主要指数
- `get-index-kline --symbol X` - 指数 K 线

### 其他
- `get-stock-info --code X` - 股票信息
- `get-news --code X` - 个股新闻
- `healthcheck` - 数据源健康检查

## 使用方式

### 命令行 (新规范)

```bash
# ✅ 正确: 用 --code 命名参数
python main.py get-realtime --code 601991
python main.py get-kline --code 601991 --days 60

# ✅ 正确: --list 列出方法
python main.py --list

# ❌ 旧版 (已废弃): 位置参数
python main.py get-realtime 601991
```

### Python API

```python
from skills.01-infra.astock-data-source.main import (
    get_realtime, get_realtime_all, get_kline
)

# 单股 (自动多源 fallback)
quote = get_realtime("601991")

# 全 A 股
all_stocks = get_realtime_all()

# K 线
df = get_kline("601991", days=60)
```

## 故障速查

| 现象 | 原因 | 解决 |
|------|------|------|
| `ProxyError: 7890` | 代理挡住外网 | 切到 ifzq/sina |
| `RemoteDisconnected` | 东财被封 | 等待 3 次后自动切 |
| `UnicodeEncodeError` (Win) | GBK 编码 | 已自动修复 |
| `所有数据源失败` | 网络隔离 | 运行 healthcheck 检查 |

## 依赖

```
requests>=2.28.0
akshare>=1.12.0
pandas>=1.5.0
```

## 实测状态

- **2026-06-21**: 住宅 IP 验证通过, ifzq + sina 稳定可用
- **2026-05-03**: 旧版在住宅 IP 100% 失败 (已修复)
