# 贡献指南

> 欢迎为 A-Stock-Skills 贡献代码!

## 如何贡献

### 报告 Bug

提交 [GitHub Issue](https://github.com/ZICXR/A-Stock-Skills/issues) 并包含:
- 复现步骤
- 期望行为
- 实际行为
- 截图/日志 (如有)
- 环境信息 (Python版本、依赖版本等)

### 功能建议

提交 Issue 描述:
- 功能描述
- 使用场景
- 预期效果

### 提交代码

1. **Fork 仓库**
2. **创建特性分支**: `git checkout -b feature/AmazingSkill`
3. **编写代码**
4. **添加测试**
5. **更新文档**
6. **提交**: `git commit -m 'Add AmazingSkill'`
7. **推送**: `git push origin feature/AmazingSkill`
8. **创建 Pull Request**

## 命名规范

### 目录名
- 全小写, 中划线连接
- 例: `dragon-tiger-analysis`, `limit-up-tracker`

### 文件名
- 全小写, 下划线连接 (Python 文件)
- 例: `dragon_tiger_analysis.py`, `limit_up_tracker.py`

### 函数名
- 动词开头, 蛇形命名
- 例: `get_stock_news`, `analyze_trend`, `generate_report`

### 变量名
- 蛇形命名
- 例: `stock_code`, `pct_change`, `main_net`

### 类名
- 大驼峰
- 例: `DataSourceManager`, `AkShareClient`

## 代码风格

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/):

- 缩进: 4 空格
- 行长: 不超过 120 字符
- 导入顺序: 标准库 → 第三方 → 本地
- 字符串: 优先双引号
- 注释: 中文 OK, 关键逻辑必须有注释

## Skill 开发模板

```python
"""
<skill-name>: <简述>
==================

功能:
    - <功能1>
    - <功能2>

作者: <你的名字>
版本: 1.0.0
"""

import logging
import pandas as pd
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# 1. <主功能>
# ============================================================
def main_function(param1: str, param2: int = 10) -> pd.DataFrame:
    """<功能描述>
    Args:
        param1: 参数1描述
        param2: 参数2描述
    Returns:
        DataFrame: 返回值描述
    """
    try:
        # 实现
        result = ...
        return result
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return pd.DataFrame()


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    # 测试代码
    df = main_function("test")
    print(df)
```

## SKILL.md 模板

```markdown
# <skill-name>

> <一句话描述>

## 功能

- 功能1
- 功能2

## 快速开始

```python
from skills.<path>.<skill-name>.<file> import func

result = func()
```

## API 文档

### `func(param1, param2=10)`

参数:
- `param1` (str): 描述
- `param2` (int, optional): 描述

返回:
- DataFrame: 描述
```

## 测试要求

- 每个 Skill 应有 Demo 入口 (`if __name__ == "__main__"`)
- 关键函数应捕获异常
- 文档字符串完整

## 提交前检查

- [ ] 代码遵循 PEP 8
- [ ] 添加了完整的 docstring
- [ ] 更新了 SKILL.md
- [ ] 更新了 README.md (如需要)
- [ ] 更新了 SKILLS_CATALOG.md
- [ ] Demo 可正常运行

## 联系方式

- GitHub: [@ZICXR](https://github.com/ZICXR)
- Issues: [提交问题](https://github.com/ZICXR/A-Stock-Skills/issues)

---

感谢你的贡献! ❤️
