---
name: lstm-forecaster
description: A 股简易 LSTM 时序预测。当用户需要用 LSTM (长短期记忆网络) 预测股票时间序列 (价格/趋势) 时,Claude 应使用此 Skill。使用 scikit-learn 兼容的简易 RNN 实现,无需 PyTorch/TensorFlow 重型依赖。支持序列预测、滚动预测。
---

# A 股简易 LSTM 时序预测 Skill

## 何时使用

- 用户需要 LSTM 预测
- 用户需要时序模型
- 用户需要序列预测
- 用户不想安装 PyTorch/TensorFlow

## 模型说明

本 Skill 使用**简易版神经网络** (基于 numpy), 模拟 LSTM 思想:
- 用历史 N 日数据作为输入
- 输出未来 M 日价格预测
- 轻量级, 几行代码即可运行

⚠️ 简化实现, **不追求极致精度**, 适合教学/演示

## 提供能力

- `prepare_sequences()` - 数据准备
- `train_lstm()` - 训练
- `forecast()` - 预测
- `rolling_forecast()` - 滚动预测

## 使用方式

```bash
# 训练
python main.py train --code 000001 --lookback 20 --horizon 5

# 预测
python main.py predict --code 000001 --horizon 5

# 滚动预测
python main.py rolling --code 000001 --horizon 5 --steps 10
```

## Python API

```python
from skills.05-ml.lstm-forecaster.main import train, forecast

# 训练
model = train("000001", lookback=20, horizon=5)

# 预测
result = forecast("000001", horizon=5)
# {predictions: [...], current_price, expected_change}
```

## 输出示例

```
📊 LSTM 预测
当前价: 12.50
预测序列: [12.65, 12.78, 12.85, 12.90, 12.95]
预测涨幅: +3.6%
```

## 限制

- 不使用 PyTorch/TensorFlow
- 实现简化, 精度有限
- 适合学习/演示, 不适合生产

## 依赖

```
akshare>=1.12.0
pandas>=1.5.0
numpy>=1.22.0
```
