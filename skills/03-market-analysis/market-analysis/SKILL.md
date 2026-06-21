---
name: market-analysis
description: A 股大盘分析。当用户需要分析大盘指数趋势、判断多空形态、计算支撑压力位 (R1/R2/S1/S2)、分析量价配合 (放量/缩量)、生成操作建议 (买入/卖出/观望) 时,Claude 应使用此 Skill。支持均线系统 (MA5/10/20/60)、MACD、量价分析、关键点位识别。
---

# A 股大盘分析 Skill

## 何时使用

- 用户询问大盘走势判断
- 用户需要指数支撑位/压力位
- 用户需要量价分析
- 用户询问操作建议 (买入/卖出/观望)
- 用户需要多空研判

## 提供能力

### 趋势分析
- `analyze_index_trend(symbol, days)` - 指数趋势分析
- `analyze_volume_price(df)` - 量价分析
- `calc_support_resistance(df, window)` - 支撑压力位

### 综合研判
- `full_market_analysis(symbol, days)` - 一键综合分析
- 返回操作建议 (强势/偏多/震荡/偏空/弱势)

## 使用方式

```bash
python main.py trend 000001 --days 60       # 趋势分析
python main.py full 000001 --days 60         # 综合分析
python main.py volume 000001                 # 量价分析
```

## Python API

```python
from skills.03-market-analysis.market-analysis.main import full_market_analysis

result = full_market_analysis("000001", days=60)
# {
#   'trend': {'overall': '看多', 'score': 4, 'signals': [...]},
#   'support_resistance': {'R1': 3050, 'S1': 2950, ...},
#   'volume_price': {'signal': '放量上涨'},
#   'advice': '偏多格局, 精选个股'
# }
```

## 趋势信号体系

| 信号 | 含义 |
|------|------|
| 多头排列 | MA5 > MA10 > MA20 > MA60 |
| 空头排列 | MA5 < MA10 < MA20 < MA60 |
| MACD金叉 | DIF 上穿 DEA |
| MACD死叉 | DIF 下穿 DEA |
| 站上MA20 | 收盘价在 20 日均线之上 |

## 量价信号

| 信号 | 描述 |
|------|------|
| 放量上涨 | 量比 > 1.5 且价格上涨 |
| 放量下跌 | 量比 > 1.5 且价格下跌 |
| 缩量上涨 | 量比 < 0.7 且价格上涨, 需警惕 |
| 缩量下跌 | 量比 < 0.7 且价格下跌, 抛压衰竭 |

## 操作建议

| 评分 | 建议 |
|------|------|
| >= 3 | 强势格局, 积极配置, 关注主线板块 |
| 1 ~ 3 | 偏多格局, 精选个股, 控制仓位 |
| -1 ~ 1 | 震荡格局, 高抛低吸, 控制节奏 |
| -3 ~ -1 | 偏空格局, 谨慎参与, 快进快出 |
| <= -3 | 弱势格局, 防守为主, 降低仓位 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
