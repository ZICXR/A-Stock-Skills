---
name: stock-classifier
description: A 股 ML 涨跌分类预测。当用户需要用机器学习预测股票未来涨跌 (3 分类: 涨/跌/震荡) 时,Claude 应使用此 Skill。基于 XGBoost/LightGBM/随机森林,综合技术指标 + 资金流 + 量价特征,输出胜率。
---

# A 股 ML 涨跌分类预测 Skill

## 何时使用

- 用户需要预测股票涨跌方向
- 用户需要 ML 选股
- 用户需要胜率评估
- 用户需要特征工程

## 模型

| 模型 | 特点 | 速度 |
|------|------|------|
| `xgboost` | 主流, 准确率高 | 中 |
| `lightgbm` | 速度快, 大数据 | 快 |
| `random_forest` | 稳定, 不易过拟合 | 中 |
| `logistic` | 简单可解释 | 快 |

## 特征 (默认 20+ 个)

- 价格类: MA5/10/20/60, 收盘价, 涨跌幅
- 动量类: 5/20/60 日收益率
- 波动类: 20 日波动率, ATR
- 成交量类: 量比, 换手率
- 技术指标: RSI, KDJ, MACD
- 资金流: 主力净流入占比

## 标签定义

- **1 (涨)**: 未来 N 日收益率 > +3%
- **0 (震荡)**: -3% ~ +3%
- **-1 (跌)**: 收益率 < -3%

## 使用方式

```bash
# 训练
python main.py train --code 000001 --horizon 5

# 预测
python main.py predict --code 000001

# 特征重要性
python main.py importance --code 000001

# 批量预测
python main.py batch --codes 000001,600519,300750
```

## Python API

```python
from skills.05-ml.stock-classifier.main import train, predict

# 训练
model = train("000001", horizon=5, model="xgboost")

# 预测
result = predict("000001", horizon=5)
# {signal: 'buy', probability: 0.72, confidence: 'high'}
```

## 输出示例

```
📊 预测结果
代码: 000001
信号: 买入
概率: 72.3%
置信度: 高
预计收益: +3.5%
```

## 模型评估

- 准确率 (Accuracy)
- 精确率 (Precision)
- 召回率 (Recall)
- F1 Score
- AUC

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
scikit-learn>=1.3.0
xgboost>=2.0.0
lightgbm>=4.0.0
```
