---
name: strategy-scheduler
description: A 股策略定时调度器。当用户需要定时自动执行某个 Skill (例如每天 15:30 自动生成复盘报告、盘中每 30 分钟监控自选股) 时,Claude 应使用此 Skill。支持 cron 表达式、配置文件管理、告警联动、执行日志。
---

# A 股策略调度器 Skill

## 何时使用

- 用户需要定时任务
- 用户需要自动化工作流
- 用户需要每天自动复盘
- 用户需要盘中自动监控

## 核心功能

- **Cron 表达式**: 标准 cron
- **配置文件**: YAML 管理多个任务
- **执行日志**: 完整记录
- **告警联动**: 触发后自动推送
- **后台运行**: daemon 模式

## 使用方式

### 1. 初始化

```bash
python main.py init
```

生成 `~/.astock_skills/scheduler.yaml`:

```yaml
tasks:
  - name: "daily_report"
    schedule: "30 15 * * 1-5"        # 周一-周五 15:30
    skill: "daily-market-report"
    args: ""
    alert:
      channel: "dingtalk"

  - name: "watchlist_check"
    schedule: "*/30 9-15 * * 1-5"    # 盘中每 30 分钟
    skill: "watchlist-monitor"
    args: "--config watchlist.yaml"
    alert:
      channel: "dingtalk"
```

### 2. 启动调度器

```bash
# 前台运行 (调试)
python main.py start

# 后台运行
python main.py start --daemon
```

### 3. 任务管理

```bash
python main.py list          # 列出所有任务
python main.py run daily_report  # 手动运行
python main.py logs daily_report  # 查看日志
python main.py stop          # 停止
```

## Python API

```python
from skills.06-tools.strategy-scheduler.main import (
    add_task, start_scheduler, run_now
)

# 添加任务
add_task(
    name="daily_report",
    schedule="30 15 * * 1-5",
    skill="daily-market-report",
)

# 立即执行
run_now("daily_report")

# 启动调度器
start_scheduler(daemon=True)
```

## 与 alerter 集成

任务触发后, 自动通过 alerter 推送结果:

```yaml
tasks:
  - name: "high_freq_monitor"
    schedule: "*/15 9-15 * * 1-5"
    skill: "watchlist-monitor"
    args: "--config watchlist.yaml"
    alert:
      channel: "dingtalk"
      on: "always"        # always / error / success
```

## 内置任务模板

```bash
# 列出模板
python main.py templates

# 应用模板
python main.py apply daily_workflow
```

模板:
- `daily_workflow`: 每天 15:30 复盘 + 推送
- `intraday_monitor`: 盘中每 30 分钟监控
- `weekly_summary`: 每周五收盘后周报

## 依赖

```
schedule>=1.2.0
pyyaml>=5.4.0
```
