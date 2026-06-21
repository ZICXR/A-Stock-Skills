---
name: watchlist-monitor
description: A 股自选股实时监控。当用户需要监控自选股 (Watchlist) 的实时行情、涨跌幅、异动信号、持仓盈亏,或需要盘中盯盘告警时,Claude 应使用此 Skill。支持 3 种自选股来源: ① 配置文件 (推荐) ② 命令行参数 ③ 同花顺/东财在线 API (需 cookie)。支持自定义告警阈值 (涨跌幅/价格突破/量能/涨跌停)。
---

# A 股自选股实时监控 Skill

## 何时使用

- 用户有自选股列表需要监控
- 用户需要盘中盯盘
- 用户需要异动告警
- 用户需要在配置文件中维护自选股

## 3 种自选股来源

### 方式 1: 配置文件 (推荐)

创建 `watchlist.yaml` 或 `watchlist.json`:

```yaml
# watchlist.yaml
stocks:
  - code: "000001"
    name: "平安银行"
    cost: 12.50        # 持仓成本 (可选)
    shares: 1000       # 持仓数量 (可选)
  - code: "600519"
    name: "贵州茅台"
  - code: "300750"
    name: "宁德时代"

alerts:
  pct_change_up: 5.0      # 涨幅超过 5% 告警
  pct_change_down: -3.0   # 跌幅超过 3% 告警
  price_above: 100        # 价格突破 100 告警
  price_below: 50         # 价格跌破 50 告警
```

### 方式 2: 命令行传入

```bash
python main.py monitor --codes 000001,600519,300750
```

### 方式 3: 同花顺/东财 API (高级)

需要用户提供 cookie, 详见下方"高级功能"。

## 提供能力

- `load_watchlist(path)` - 加载自选股
- `get_realtime_quotes(codes)` - 批量获取实时行情
- `check_alerts(quotes, alerts)` - 检查告警
- `monitor_once(path)` - 单次扫描
- `monitor_loop(path, interval)` - 持续监控

## 使用方式

```bash
# 使用默认配置 (./watchlist.yaml)
python main.py monitor

# 指定配置
python main.py monitor --config ~/my_watchlist.yaml

# 命令行传入
python main.py monitor --codes 000001,600519,300750

# 持续监控 (每 30 秒)
python main.py loop --interval 30

# 初始化配置模板
python main.py init

# 检查告警
python main.py alerts --config watchlist.yaml
```

## Python API

```python
from skills.02-data-collection.watchlist-monitor.main import (
    load_watchlist, get_realtime_quotes, check_alerts
)

# 加载自选股
watchlist = load_watchlist("./watchlist.yaml")
# {'stocks': [...], 'alerts': {...}}

# 批量获取行情
codes = ["000001", "600519", "300750"]
quotes = get_realtime_quotes(codes)
# [{'code', 'name', 'price', 'pct_change', ...}, ...]

# 检查告警
alerts = check_alerts(quotes, watchlist["alerts"])
# [{'code': '000001', 'type': 'pct_change_up', 'message': '...'}]
```

## 告警类型

| 类型 | 触发条件 |
|------|----------|
| `pct_change_up` | 涨幅超过阈值 |
| `pct_change_down` | 跌幅超过阈值 |
| `price_above` | 价格突破上限 |
| `price_below` | 价格跌破下限 |
| `volume_spike` | 量比异常 (>3) |
| `limit_up` | 涨停 |
| `limit_down` | 跌停 |

## 高级: 同花顺/东财在线自选股 (需 cookie)

如果你有同花顺/东财账号, 可以从他们的服务器同步自选股:

```yaml
# watchlist.yaml
source:
  type: "ths"            # 同花顺
  cookie: "your_cookie"  # 需要登录后的 cookie
  # 或
  type: "eastmoney"
  cookie: "your_cookie"
```

## 输出示例

```
📊 自选股监控 (2024-12-30 14:30:00)
========================================
✅ 000001 平安银行     12.45  +1.25%   量比1.2
🔺 600519 贵州茅台   1680.50  +5.20%   [告警: 涨幅>5%]
🟢 300750 宁德时代   245.80  +2.80%   量比1.5
----------------------------------------
🚨 触发告警 1 条:
  [pct_change_up] 600519 贵州茅台 +5.20%
```

## 依赖

```
akshare>=1.12.0
pyyaml>=5.4.0
pandas>=1.5.0
```
