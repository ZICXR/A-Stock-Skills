# astock-data-source 实战示例

## 场景 1: 单股实时监控

```python
import time
from skills.01-infra.astock-data-source.main import get_realtime

codes = ["601991", "600519", "300750"]
while True:
    for code in codes:
        q = get_realtime(code)
        print(f"{q['name']:8s} {q['price']:7.2f} {q['pct_change']:+6.2f}%")
    print("---")
    time.sleep(30)
```

## 场景 2: 全市场 PE < 20

```python
from skills.01-infra.astock-data-source.main import get_realtime_all
import pandas as pd

df = get_realtime_all()
# 标准化列名 (astock-data-source 内部已统一)
df_pe = df[df["pe"] < 20].sort_values("pe").head(50)
print(df_pe[["代码", "名称", "最新价", "pe"]])
```

## 场景 3: K 线 + 技术分析

```python
from skills.01-infra.astock-data-source.main import get_kline
from skills.04-stock-analysis.stock-technical-analysis.main import calc_macd, calc_ma

df = get_kline("601991", days=120)
df["ma5"] = calc_ma(df, 5)
df["ma20"] = calc_ma(df, 20)
df["macd"], df["signal"], df["hist"] = calc_macd(df)
print(df.tail(20))
```

## 场景 4: 行业资金流

```python
from skills.01-infra.astock-data-source.main import get_realtime_all
from skills.03-market-analysis.capital-flow-analysis.main import get_sector_flow

all_stocks = get_realtime_all()
# 合并资金流 ...
```

## 场景 5: 断网检测 + 降级

```python
from skills.01-infra.astock-data-source.main import get_realtime, SOURCE_FAIL_COUNT

try:
    q = get_realtime("601991")
except RuntimeError as e:
    print(f"❌ 所有数据源失败: {e}")
    print(f"失败统计: {SOURCE_FAIL_COUNT}")
    # 提示用户
    print("💡 检查: 1) 代理 2) 网络 3) 跑 healthcheck")
```

## 场景 6: 大批量数据 (用缓存)

```python
import pandas as pd
from skills.01-infra.astock-cache.main import kline_get_or_fetch
from skills.01-infra.astock-data-source.main import get_kline

def smart_kline(code, days=60):
    return kline_get_or_fetch(code, get_kline, days=days)

# 第一次慢, 之后 5 秒
codes = ["601991", "600519", "000001", ...]
for code in codes:
    df = smart_kline(code)
    # ... 分析
```
