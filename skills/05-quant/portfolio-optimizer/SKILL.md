---
name: portfolio-optimizer
description: A 股投资组合优化。当用户需要构建最优投资组合 (基于马科维茨均值方差模型)、风险平价、最大化夏普比率、最小化方差时,Claude 应使用此 Skill。支持协方差矩阵计算、有效前沿、行业分散度控制。
---

# A 股投资组合优化 Skill

## 何时使用

- 用户需要构建多只股票组合
- 用户需要风险平价配置
- 用户需要最大夏普组合
- 用户需要分散投资

## 内置策略

| 策略 | 目标 |
|------|------|
| `max_sharpe` | 最大化夏普比率 |
| `min_volatility` | 最小化波动率 |
| `risk_parity` | 风险平价 (等风险贡献) |
| `equal_weight` | 等权重 (1/n) |
| `max_diversification` | 最大化分散度 |

## 提供能力

- `get_returns(codes, days)` - 获取历史收益率
- `calc_cov_matrix(returns)` - 协方差矩阵
- `optimize_portfolio(method, returns)` - 组合优化
- `analyze_portfolio(weights, returns)` - 组合分析
- `efficient_frontier(returns, n_points)` - 有效前沿

## 使用方式

```bash
# 优化组合
python main.py optimize --codes 000001,600519,300750,000858 --method max_sharpe

# 风险平价
python main.py optimize --codes 000001,600519,300750,000858 --method risk_parity

# 等权重
python main.py optimize --codes 000001,600519,300750,000858 --method equal_weight

# 有效前沿
python main.py frontier --codes 000001,600519,300750,000858 --n 20
```

## Python API

```python
from skills.05-quant.portfolio-optimizer.main import (
    get_returns, optimize_portfolio, analyze_portfolio
)

# 获取历史收益
returns = get_returns(["000001", "600519", "300750"], days=252)

# 优化
result = optimize_portfolio("max_sharpe", returns)
# {weights: {code: weight}, expected_return, volatility, sharpe}
```

## 输出示例

```
=== 组合优化结果 (max_sharpe) ===
代码       权重
000001    15.3%
600519    42.1%
300750    28.6%
000858    14.0%

预期年化收益: 18.5%
预期波动率:   22.3%
夏普比率:     0.83
```

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
scipy>=1.10.0
```
