---
name: factor-analysis
description: A 股多因子分析 (传统 + ML 增强版)。当用户需要进行多因子选股 (动量/价值/质量/成长/波动/流动性 8 大因子) 时,Claude 应使用此 Skill。支持传统加权评分 + ML 集成学习 (LightGBM/XGBoost) + IC 评估 (|IC|>0.05 强有效)。是 factor-analysis + ml-factor 合并的统一版本。
---

# A 股多因子分析 Skill (统一版)

## 何时使用

- 用户需要多因子选股
- 用户需要因子有效性评估
- 用户需要因子 IC 计算
- 用户需要 ML 增强因子 (新)

## 2 大模式

| 模式 | 命令 | 适用 |
|------|------|------|
| 传统加权 | `score` | 快速, 可解释 |
| ML 增强 | `train-ml` + `ml-rank` | 更准确, 自动学习 |

## 提供能力

### 传统
- `calc_factor()` - 单因子
- `calc_all_factors()` - 8 因子
- `multi_factor_score()` - 综合评分

### ML
- `train_ml_model()` - 训练 LightGBM/XGBoost
- `ml_rank()` - 全市场排序

### 通用
- `calc_ic()` - IC 评估

## 使用方式

```bash
# 传统
python main.py calc 000001 momentum_20
python main.py all 000001
python main.py score --codes 000001,600519 --top 20

# ML
python main.py train-ml --top 500 --model lightgbm
python main.py ml-rank --top 30
```

## Python API

```python
from skills.05-quant.factor-analysis.main import (
    calc_factor, multi_factor_score, ml_rank
)

# 传统
factors = calc_all_factors("000001")
score = multi_factor_score(["000001", "600519"])

# ML
top = ml_rank(30)
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
scikit-learn>=1.3.0
lightgbm>=4.0.0  (ML 模式)
xgboost>=2.0.0   (ML 模式)
```

## 合并历史

本 Skill 由原 `factor-analysis` + `ml-factor` 合并而成, 节省 1 个 Skill。
