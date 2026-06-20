# 架构设计文档

> A-Stock-Skills 的设计哲学与技术选型

## 设计目标

1. **模块化**: 每个 Skill 独立可用, 可自由组合
2. **即插即用**: 最小化配置, 一行代码上手
3. **多源融合**: 自动选择最佳数据源, 失败降级
4. **可扩展**: 容易添加新 Skill 或新数据源
5. **生产级**: 限流、重试、缓存、容错

## 6层架构

### Layer 1: 基础设施层 (Foundation)
**职责**: 提供基础能力, 屏蔽底层细节
- `astock-data-source`: 数据源抽象与统一管理
- `astock-utils`: 通用工具(代码、日期、指标)

**设计原则**:
- 单一职责, 每个工具函数只做一件事
- 函数式风格, 无副作用
- 纯 Python 实现, 无框架依赖

### Layer 2: 数据采集层 (Data Collection)
**职责**: 从各种数据源抓取原始数据
- 新闻、公告、行情、板块、个股信息

**设计原则**:
- 每个数据源对应一个 Skill
- 统一返回 DataFrame
- 统一字段命名规范

### Layer 3: 市场分析层 (Market Analysis)
**职责**: 基于采集层数据进行市场级分析
- 大盘趋势、板块轮动、资金流向、龙虎榜

**设计原则**:
- 输入: Layer 2 的 DataFrame
- 输出: 结构化分析结果 (Dict)
- 评分体系透明可调

### Layer 4: 个股分析层 (Stock Analysis)
**职责**: 针对单只股票的深度分析
- 涨停板、技术面、基本面

**设计原则**:
- 复用 Layer 1 的工具函数
- 综合评分, 直观可读
- 支持单维度调用, 也支持综合分析

### Layer 5: 报告层 (Reports)
**职责**: 整合所有分析, 生成可读报告
- 每日复盘报告 (Markdown 格式)

**设计原则**:
- 模板化, 易于自定义
- 模块化组装, 可单独输出某部分
- 输出格式: Markdown / Text

## 核心设计模式

### 1. 装饰器模式 (Decorator)

用于添加横切关注点 (重试、限流、缓存):

```python
def with_retry(max_retries: int = 3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_retries - 1:
                        raise
                    time.sleep(1)
        return wrapper
    return decorator
```

### 2. 统一接口 (Facade)

`DataSourceManager` 屏蔽多源差异:

```python
class DataSourceManager:
    def call(self, source, method, *args, **kwargs):
        # 1. 尝试主数据源
        # 2. 失败则降级
        # 3. 全部失败则抛异常
```

### 3. 工厂模式 (Factory)

技术指标计算统一接口:

```python
def add_all_indicators(df):
    df = calc_ma(df)
    df = calc_macd(df)
    df = calc_kdj(df)
    # ...
    return df
```

### 4. 管道模式 (Pipeline)

数据流: 采集 → 清洗 → 分析 → 报告

## 数据流

```
原始数据 (API)
   ↓ [astock-data-source]
清洗后数据 (DataFrame)
   ↓ [astock-utils 标准化]
结构化数据
   ↓ [Layer 3-4 分析]
分析结果 (Dict)
   ↓ [daily-market-report]
Markdown 报告
```

## 错误处理策略

| 错误类型 | 处理策略 |
|----------|----------|
| 网络超时 | 重试 3 次, 指数退避 |
| 接口变更 | 降级到备用数据源 |
| 数据为空 | 返回空 DataFrame, 提示非交易日 |
| 代码错误 | 抛 ValueError, 给出明确错误信息 |
| 限流 | 自动 sleep, 重试 |

## 性能优化

1. **内存缓存**: 5 分钟 TTL, 避免重复请求
2. **限流控制**: 装饰器自动 sleep
3. **批量优先**: 一次请求获取多只股票
4. **异步支持**: 可选, 高级用户

## 安全设计

1. **代码校验**: `normalize_stock_code` 严格校验
2. **类型检查**: 函数签名 + 类型注解
3. **异常隔离**: 每个 Skill 独立, 互不影响
4. **资源释放**: 使用 with 语句管理资源

## 扩展指南

### 添加新 Skill

1. 在对应层级创建目录
2. 实现主文件 `xxx.py`
3. 创建 `SKILL.md` 文档
4. 更新 `README.md` 和 `SKILLS_CATALOG.md`

### 添加新数据源

1. 继承 `AkShareClient` 类似的模式
2. 在 `DataSourceManager` 中注册
3. 实现降级逻辑

## 未来规划

- [ ] Layer 6: 量化策略层
- [ ] LLM 集成 (智能解读)
- [ ] 实时监控预警
- [ ] Web UI (Streamlit / Gradio)
- [ ] 策略回测引擎
- [ ] 因子库
- [ ] 多账户支持
