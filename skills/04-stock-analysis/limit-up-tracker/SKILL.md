---
name: limit-up-tracker
description: A 股涨停板追踪。当用户需要查看当日涨停板、分析连板梯队 (1板/2板/3板...5+板)、计算炸板率、评估涨停强度 (6 维模型: 封单金额/封板时间/炸板次数/连板数/流通市值/题材热度)、识别涨停原因题材 (AI/新能源/汽车/医药/重组等 11 大类) 时,Claude 应使用此 Skill。
---

# A 股涨停板追踪 Skill

## 何时使用

- 用户询问当日涨停板
- 用户需要连板梯队分析
- 用户要求炸板率统计
- 用户需要评估涨停强度
- 用户询问涨停原因/题材归类

## 提供能力

### 数据获取
- `get_zt_pool(date)` - 当日涨停板池
- `get_consecutive_zt(days)` - 连板梯队

### 分析
- `evaluate_zt_strength(row)` - 涨停强度评估 (0-10分)
- `categorize_zt_reason(reason)` - 涨停原因归类
- `summarize_zt_reasons(df)` - 涨停原因汇总
- `calc_break_rate(date)` - 炸板率

### 综合
- `zt_daily_report(date)` - 涨停板综合日报

## 使用方式

```bash
python main.py pool                  # 当日涨停板
python main.py pool --date 20241230  # 指定日期
python main.py consecutive --days 5  # 连板梯队
python main.py break                 # 炸板率
python main.py reasons               # 涨停原因分布
python main.py report                # 综合日报
```

## Python API

```python
from skills.04-stock-analysis.limit-up-tracker.main import (
    get_zt_pool, evaluate_zt_strength, calc_break_rate, zt_daily_report
)

# 当日涨停
zt = get_zt_pool()

# 涨停强度
for _, row in zt.iterrows():
    s = evaluate_zt_strength(row)
    # {'score': 5, 'level': '强', 'factors': [...]}

# 炸板率
br = calc_break_rate()
# {'zt_count': 56, 'zb_count': 78, 'break_rate': 28.2}
```

## 涨停强度评估 (6 维, 满分 10)

| 维度 | 分值 | 规则 |
|------|------|------|
| 封单金额 | 2 | >1亿=2, >5000万=1 |
| 封板时间 | 2 | 早盘(<10点)=2, 午盘前=1 |
| 炸板次数 | 1 | 0次=1, >=2次=-1 |
| 连板数 | 2 | >=5连板=2, >=3连板=1 |
| 流通市值 | 1 | <5亿=1 (小盘) |
| 题材热度 | 2 | 主流题材=2 |

## 涨停原因分类

- AI/科技 · 新能源 · 汽车 · 医药 · 军工 · 消费 · 金融 · 房地产 · 重组 · 高送转 · 政策 · 其他

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
```
