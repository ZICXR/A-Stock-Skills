---
name: stock-screener-custom
description: A 股自定义条件筛选器。当用户需要按任意条件组合筛选股票 (例如 "市值 50-200 亿 + PE < 20 + ROE > 15% + 站上 20 日均线") 时,Claude 应使用此 Skill。支持 11 种字段、9 种操作符 (>/</> = /<=/between/in 等)、保存策略为 YAML 复用、5 个内置策略模板 (value/growth/small_cap/momentum/low_pe_high_roe)。
---

# A 股自定义条件筛选器 Skill

## 何时使用

- 用户需要自定义条件组合
- 用户需要保存常用筛选策略
- 用户需要定时扫描
- 用户需要复杂的选股条件

## 内置条件字段

- `pe` - 市盈率 (TTM)
- `pb` - 市净率
- `ps` - 市销率
- `total_mv` - 总市值 (亿)
- `circ_mv` - 流通市值 (亿)
- `roe` - 净资产收益率 (%)
- `pct_change` - 涨跌幅 (%)
- `turnover` - 换手率 (%)
- `volume_ratio` - 量比
- `price` - 当前价格
- `change_5d` - 5日涨跌幅
- `change_20d` - 20日涨跌幅
- `above_ma5/20/60` - 是否站上均线

## 操作符

- `>` `<` `>=` `<=` `==` `!=`
- `between(a, b)` - 区间
- `in` `not in`
- `crosses_above(MA20)` - 上穿
- `crosses_below(MA20)` - 下穿

## 使用方式

```bash
# 单条件
python main.py screen --where "pe<20"

# 多条件 AND
python main.py screen --where "pe<20" --where "pb<2" --where "total_mv>50"

# 区间
python main.py screen --where "total_mv between 50,200"

# 加载策略文件
python main.py screen --strategy my_strategy.yaml

# 保存策略
python main.py save --name value_strategy
```

## Python API

```python
from skills.05-quant.stock-screener-custom.main import screen_custom, load_strategy

# 自定义条件
result = screen_custom(
    conditions=[
        {"field": "pe", "op": "<", "value": 20},
        {"field": "total_mv", "op": "between", "value": (50, 200)},
        {"field": "roe", "op": ">", "value": 15},
    ],
    top_n=50,
)
```

## 策略文件格式

创建 `strategy.yaml`:

```yaml
name: 价值低估
description: 低 PE + 高 ROE + 合理市值
conditions:
  - field: pe
    op: "<"
    value: 20
  - field: roe
    op: ">"
    value: 15
  - field: total_mv
    op: "between"
    value: [50, 500]
sort_by: pe
top_n: 30
```

## 内置策略模板

- `value` - 价值策略 (低 PE/PB + 高 ROE)
- `growth` - 成长策略 (高 ROE + 营收增长)
- `dividend` - 高分红 (高股息率 + 低 PE)
- `small_cap` - 小市值策略 (市值 < 100亿)
- `momentum` - 动量策略 (5/20 日涨幅 > 0)

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
pyyaml>=5.4.0
```
