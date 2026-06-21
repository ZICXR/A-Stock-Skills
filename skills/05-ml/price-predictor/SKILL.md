---
name: price-predictor
description: A 股 ML 价格预测。当用户需要用机器学习预测股票未来价格 (回归问题, 预测下日/5日/20日收盘价) 时,Claude 应使用此 Skill。基于 XGBoost/LightGBM 回归模型,综合技术指标特征,输出价格点估计和置信区间。
---

# A 股 ML 价格预测 Skill

## 何时使用

- 用户需要预测未来价格
- 用户需要价格点估计
- 用户需要置信区间
- 用户需要回归模型评估

## 模型

| 模型 | 特点 |
|------|------|
| `xgboost` | XGBoost 回归 |
| `lightgbm` | LightGBM 回归 |
| `random_forest` | 随机森林回归 |
| `ridge` | 岭回归 (线性) |
| `linear` | 线性回归 |

## 评估指标

- MAE (平均绝对误差)
- RMSE (均方根误差)
- MAPE (平均绝对百分比误差)
- R² (决定系数)

## 使用方式

```bash
# 训练
python main.py train --code 000001 --horizon 5

# 预测
python main.py predict --code 000001 --horizon 5

# 置信区间
python main.py predict --code 000001 --horizon 5 --interval 0.95

# 评估
python main.py evaluate --code 000001 --horizon 5
```

## Python API

```python
from skills.05-ml.price-predictor.main import train, predict

# 训练
model = train("000001", horizon=5)

# 预测
result = predict("000001", horizon=5)
# {predicted_price, current_price, expected_return, confidence_interval}
```

## 输出示例

```
📊 价格预测
当前价格: 12.50
预测价格: 13.20 (+5.6%)
95% 置信区间: [12.30, 14.10]
模型: XGBoost
R²: 0.72
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
scikit-learn>=1.3.0
xgboost>=2.0.0
lightgbm>=4.0.0
```
