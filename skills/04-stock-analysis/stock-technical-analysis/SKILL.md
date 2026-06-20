---
name: stock-technical-analysis
description: A 股个股技术面分析。当用户需要对某只股票做技术面分析时,Claude 应使用此 Skill。支持 K 线形态识别 (十字星/锤子线/吞没/早晨之星)、趋势研判 (均线/MACD)、超买超卖 (KDJ/RSI)、支撑压力位计算、综合买卖信号生成。
---

# A 股个股技术面分析 Skill

## 何时使用

- 用户要求分析某只股票的技术面
- 用户需要 K 线形态识别
- 用户需要买卖信号
- 用户需要支撑压力位
- 用户需要超买超卖判断

## 提供能力

### K线数据
- `get_kline(code, days, adjust)` - 历史 K 线

### K线形态
- `detect_patterns(df)` - 形态识别 (十字星/锤子线/吞没/早晨之星/黄昏之星)

### 趋势研判
- `analyze_trend(df)` - 综合趋势 (均线+MACD)
- `generate_trading_signal(df)` - 买卖信号 (买入/卖出/观望)

### 超买超卖
- `detect_obs(df)` - KDJ + RSI 超买超卖

### 支撑压力
- `calc_support_pressure(df, window)` - 支撑压力位 (R1/R2/S1/S2)

### 综合
- `full_technical_analysis(code, days)` - 一键综合分析

## 使用方式

```bash
python main.py kline 000001 --days 120 --adjust qfq   # K线
python main.py trend 000001 --days 60                   # 趋势
python main.py signal 000001 --days 60                  # 买卖信号
python main.py patterns 000001 --days 5                 # K线形态
python main.py full 000001 --days 120                   # 综合分析
```

## Python API

```python
from skills.04-stock-analysis.stock-technical-analysis.main import full_technical_analysis

result = full_technical_analysis("000001", days=120)
# {
#   'patterns': [{'date': ..., 'pattern': '锤子线', 'signal': '看涨'}],
#   'trend': {'trend': '上涨', 'score': 4, 'signals': [...]},
#   'overbought_oversold': {'level': '超买', 'K': 88, 'D': 85, 'J': 95},
#   'support_pressure': {'R1': 13.5, 'S1': 12.0, ...},
#   'trading_signal': {'signal': '买入', 'strength': '强', 'buy_signals': [...], 'sell_signals': [...]}
# }
```

## 买卖信号生成规则

**买入信号** (满足>=2个且多于卖出):
- 均线多头排列
- MACD 金叉
- KDJ 低位 (<50) 金叉
- 放量上涨 (量比 > 1.5)

**卖出信号** (满足>=2个且多于买入):
- 均线空头排列
- MACD 死叉
- KDJ 高位 (>50) 死叉
- 放量下跌

## K线形态

| 形态 | 信号 | 描述 |
|------|------|------|
| 十字星 | 反转 | 多空胶着, 关注变盘 |
| 锤子线 | 看涨 | 下影线长, 多方力量 |
| 看涨吞没 | 看涨 | 阳包阴, 强势反转 |
| 看跌吞没 | 看跌 | 阴包阳, 弱势反转 |

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
