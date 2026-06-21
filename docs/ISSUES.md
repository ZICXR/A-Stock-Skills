# A-Stock-Skills 实测问题追踪

> 基于 2026-06-21 实际使用反馈, 按"踩坑严重度"分类

## 🔴 严重问题 (3 个)

### 1. 东财 push2 接口在住宅 IP 100% 失败 ✅ 已修复

**问题**:
- `astock-data-source` 默认走东财 push2his/push2
- 住宅 IP + 代理 (7890) 几乎 100% 失败
- SKILL.md 写"间歇风控", 实测是**根本连不上**

**修复 (v2.0)**:
- 重写 `astock-data-source/main.py`
- 数据源优先级: **ifzq gtimg → sina → 东财 → akshare**
- 自动多源 fallback, 连续失败 3 次自动跳过
- 修复 akshare 内部 `requests` 代理问题
- 新增 `healthcheck` 子命令

**状态**: ✅ 已修复

### 2. argparse 设计反人类 (位置参数报错) 🟡 部分修复

**问题**:
- `python main.py --list` 报 "unrecognized arguments"
- `python main.py get-realtime --code 601991` 报 "unrecognized arguments: --code"
- 实际是位置参数: `python main.py get_realtime 601991`

**影响**: AI 调用时反复试错

**修复**:
- `astock-data-source` 已修复: 用 `--code` 命名参数
- 其他 Skill 仍需修复

**待修复 Skill** (30+):
- limit-up-tracker (使用位置参数)
- watchlist-monitor
- market-analysis
- 所有 ML Skill
- 所有量化 Skill
- 等等

**状态**: 🟡 已识别, 部分修复

### 3. screener 全市场拉取必然失败 🟡 部分修复

**问题**:
- `screener` 默认拉 5000+ 只全市场
- 东财被封 → 全市场 pull 失败
- 退到 sina `Market_Center.getHQNodeData` 才能拿 3028 只

**修复**:
- `astock-data-source` 新增 `get-realtime-all` 用 sina Market Center
- `screener` 仍需改造: 解耦 pool builder 和 per-stock

**状态**: 🟡 数据源已修复, 解耦待做

## 🟡 中等问题 (4 个)

### 4. 跨 skill 字段不一致 (code/symbol) ❌ 未修复

**问题**: 
- `astock-data-source` 输出 `code`/`name`
- `astock-utils` 用 `code`/`market`
- 不同 skill 字段名混乱

**建议方案** (在 `astock-utils` 中定义标准 `Stock` dataclass)

**状态**: ❌ 未修复 (工作量大)

### 5. SKILL.md 过长 (28K tokens) 🟡 部分修复

**问题**:
- `astock-data-source/SKILL.md` 2000+ 行
- 挤占 Claude 上下文

**建议**:
- 拆出 `TROUBLESHOOTING.md` / `FAQ.md`
- `SKILL.md` 只保留核心 + When to Activate
- `astock-data-source` 已添加故障速查表

**状态**: 🟡 部分修复

### 6. 数值单位混乱 (元/万/亿) ❌ 未修复

**问题**:
- `screener` 用 `amount_yi` (亿)
- 东财 push2 用元
- 新浪 hq 用元
- 不同 skill 输出不同

**建议**:
- 统一字段名后缀: `amount_yi` (亿) 或 `amount_wan` (万)
- `astock-data-source` v2.0 已统一

**状态**: 🟡 部分修复

### 7. 缺接口健康检查 ✅ 已修复

**问题**:
- 没有"跑前知道哪些端点今天能用"的机制
- 跑完才知道 502

**修复**:
- `astock-data-source` 新增 `healthcheck` 子命令
- 未来可考虑加定时 cron

**状态**: ✅ 已修复

## 🟢 小问题 (4 个)

### 8. Windows GBK 编码问题 ✅ 已修复

**修复**: `astock-data-source` 顶部加自动 patch
**状态**: ✅ 已修复 (仅 source, 其他 Skill 待统一)

### 9. Web UI 启动文档缺失 ❌ 未修复

**状态**: ❌ 待补文档

### 10. 依赖版本分散 ❌ 未修复

**状态**: ❌ 待用 `pip-compile` / `uv` 统一

### 11. 缺端到端示例 ❌ 未修复

**建议**: 新增 `tutorials/05-end-to-end.md`
**状态**: ❌ 待补

---

## 📊 修复进度

| 类别 | 数量 | 已修 | 待修 |
|------|------|------|------|
| 🔴 严重 | 3 | 1 | 2 |
| 🟡 中等 | 4 | 0 | 4 |
| 🟢 小问题 | 4 | 1 | 3 |
| **合计** | **11** | **2** | **9** |

## 🛠️ 落地数据 (基于用户实测)

用户已用本项目完成:
- 601991 单股诊断
- 全市场 300 只筛选 (102 只候选)
- 找到 6/18 收盘 TOP 10 候选 (动量+趋势+资金三重共振)
- 排名 #1: 300308 中际旭创 (5日+21.7%, 20日+37.7%, PE 140)
- 排名 #2: 300502 新易盛 (5日+10.6%, 20日+44.1%, PE 61)

## 🔧 用户的临时解决方案

1. **数据源**: 改用 `ifzq gtimg` + `sina Market_Center`
2. **CLI**: 跳过 `--list`, 直接用位置参数
3. **screener**: 改用 sina `Market_Center.getHQNodeData` 拉代码列表
4. **bool 字段**: 改用 int
5. **代理**: 走非 push2 域名

## 📅 后续计划

### 短期 (1 周内)
- [x] 修复 astock-data-source 多源 fallback ✅
- [x] 修复 argparse (astock-data-source) ✅
- [x] 添加 healthcheck ✅
- [x] 修复 Windows 编码 (astock-data-source) ✅
- [ ] 批量修复其他 Skill 的 argparse (30+ 文件)
- [ ] screener 解耦 pool builder

### 中期 (1 月内)
- [ ] 定义标准 Stock dataclass
- [ ] 统一数值单位 (amount_yi)
- [ ] 添加端到端示例教程
- [ ] Web UI 完善文档

### 长期
- [ ] 抽取共享代码 (astock-common)
- [ ] 单元测试覆盖
- [ ] pip 包发布
- [ ] CI/CD

## 🙏 致谢

感谢用户 **@**[用户] 提供如此详尽的实测反馈!
这份反馈价值远超想象, 直接帮助 A-Stock-Skills 走过了最关键的一关。
