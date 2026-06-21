# SKILL.md 编写标准

> 所有 A-Stock-Skills 必须遵循的 SKILL.md 规范

## 📋 必须包含的章节 (按顺序)

### 1. YAML Frontmatter (必填)

```yaml
---
name: skill-name-kebab-case        # 必填, 全小写中划线
description: 一句话描述 + 何时使用    # 必填, Claude 据此判断
---
```

**description 模板** (2-3 句话):
```
[Skill 的核心功能]. 当用户需要[具体场景 1]、[场景 2]、[场景 3] 时, 
Claude 应使用此 Skill。[可选: 关键技术/算法说明].
```

### 2. 标题 (必填)

```markdown
# Skill 中文名 Skill
```

### 3. 何时使用 (必填)

```markdown
## 何时使用

- 用户场景 1
- 用户场景 2
- 用户场景 3
```

### 4. 提供能力 (必填)

列出所有 API, 表格形式:

```markdown
## 提供能力

### 分类 1
- `function_name(args)` - 简短描述
- `function_name2(args)` - 简短描述

### 分类 2
- `function_name3()` - 简短描述
```

### 5. 使用方式 (必填)

CLI 和 Python API 都要:

```markdown
## 使用方式

\`\`\`bash
# 命令1
python main.py <subcommand> [args]

# 命令2
python main.py <subcommand> [args]
\`\`\`

## Python API

\`\`\`python
from skills.<path>.main import function

result = function(args)
\`\`\`
```

### 6. 输出示例 (推荐)

```markdown
## 输出示例

\`\`\`
[实际输出]
\`\`\`
```

### 7. 关键规则/算法 (推荐)

如果是分析/评分类 Skill, 应说明评分规则:

```markdown
## 评分规则

| 条件 | 分数 |
|------|------|
| ... | ... |
```

### 8. 依赖 (必填)

```markdown
## 依赖

\`\`\`
akshare>=1.12.0
pandas>=1.5.0
\`\`\`
```

### 9. 关联 Skill (可选)

```markdown
## 关联 Skill

- `other-skill` - 配合使用说明
```

## ✅ 最佳实践

1. **description 写"何时用"**: Claude 是根据 description 判断何时激活 Skill
2. **示例代码必须可运行**: 不要写伪代码
3. **API 列表完整**: 所有公开函数都要列出
4. **包含错误处理说明**: 常见错误如何处理
5. **避免敏感信息**: 不要在 SKILL.md 中写 token/cookie 示例
6. **保持简洁**: SKILL.md 不超过 300 行
