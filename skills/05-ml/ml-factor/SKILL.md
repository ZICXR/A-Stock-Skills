---
name: ml-factor
description: A 股 ML 多因子排序。当用户需要用机器学习 (LightGBM/XGBoost 集成学习) 综合多因子 (动量/价值/质量/成长/波动/资金) 对全市场股票进行排序打分、预测未来收益排名时,Claude 应使用此 Skill。是传统 factor-analysis 的 ML 增强版。
---

# A 股 ML 多因子排序 Skill

## 何时使用

- 用户需要 ML 增强因子选股
- 用户需要全市场排序
- 用户需要因子合成
- 用户需要集成学习模型

## vs factor-analysis (传统)

| 维度 | factor-analysis | ml-factor |
|------|-----------------|-----------|
| 因子合成 | 简单加权 | ML 自动学习 |
| 非线性关系 | ❌ | ✅ |
| 因子交互 | ❌ | ✅ |
| 训练周期 | 无 | 月度/周度 |
| 模型 | 线性加权 | LightGBM/XGBoost |

## 提供能力

- `train_factor_model()` - 训练 ML 因子模型
- `rank_stocks()` - 全市场排序
- `get_top_stocks()` - 获取 Top N
- `factor_exposure()` - 因子暴露度

## 使用方式

```bash
# 训练 (使用全市场数据)
python main.py train --top 500 --model lightgbm

# 排序
python main.py rank --top 30

# 因子暴露
python main.py exposure --code 000001

# 评估
python main.py evaluate
```

## Python API

```python
from skills.05-ml.ml-factor.main import train, rank, top_stocks

# 训练
train(top_n=500, model="lightgbm")

# 排序
scores = rank(top_n=30)

# Top 股票
top = top_stocks(20)
```

## 输出示例

```
=== ML 多因子排序 Top 20 ===
代码    名称        因子分    预期收益
000001  平安银行    85.2      +5.3%
600519  贵州茅台    82.1      +4.8%
...
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
scikit-learn>=1.3.0
lightgbm>=4.0.0
xgboost>=2.0.0
```
