# astock-data-source

> A股多源数据源统一管理

## 功能

- 统一封装 **akshare / tushare / 东方财富** 三大数据源
- 自动重试、限流、降级
- 内存缓存
- 统一调用接口

## 快速开始

```python
from skills.01-infra.astock-data-source.astock_data_source import get_manager

m = get_manager()

# 获取全A股实时行情
df = m.akshare.stock_zh_a_spot()

# 获取个股历史K线
df = m.akshare.stock_zh_a_hist("000001", adjust="qfq")

# 健康检查
from skills.01-infra.astock-data-source.astock_data_source import health_check
print(health_check())
```

## 配置

- `TUSHARE_TOKEN` 环境变量: tushare pro token
- 安装: `pip install akshare tushare requests`
