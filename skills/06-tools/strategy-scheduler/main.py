#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""strategy-scheduler: 策略定时调度器"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

CONFIG_DIR = os.path.expanduser("~/.astock_skills")
CONFIG_PATH = os.path.join(CONFIG_DIR, "scheduler.yaml")
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


# ============================================================
# 配置管理
# ============================================================
def load_config() -> Dict:
    if not os.path.exists(CONFIG_PATH):
        return {"tasks": []}
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"tasks": []}
    except Exception:
        return {"tasks": []}


def save_config(cfg: Dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    import yaml
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)


def init_config():
    """生成配置模板"""
    template = {
        "tasks": [
            {
                "name": "daily_report",
                "schedule": "30 15 * * 1-5",
                "skill": "daily-market-report",
                "args": "",
                "enabled": True,
                "alert": {"channel": "dingtalk", "on": "success"},
            },
            {
                "name": "watchlist_check",
                "schedule": "*/30 9-15 * * 1-5",
                "skill": "watchlist-monitor",
                "args": "--config watchlist.yaml",
                "enabled": True,
                "alert": {"channel": "dingtalk", "on": "always"},
            },
        ]
    }
    save_config(template)
    print(f"✅ 配置已生成: {CONFIG_PATH}")


# ============================================================
# 任务管理
# ============================================================
def add_task(name: str, schedule: str, skill: str, args: str = "",
             alert_channel: str = None, alert_on: str = "success"):
    cfg = load_config()
    task = {
        "name": name,
        "schedule": schedule,
        "skill": skill,
        "args": args,
        "enabled": True,
    }
    if alert_channel:
        task["alert"] = {"channel": alert_channel, "on": alert_on}
    cfg["tasks"].append(task)
    save_config(cfg)
    print(f"✅ 已添加任务: {name}")


def list_tasks():
    cfg = load_config()
    if not cfg["tasks"]:
        print("无任务")
        return
    print(f"\n=== 任务列表 ({len(cfg['tasks'])}) ===")
    for t in cfg["tasks"]:
        enabled = "✅" if t.get("enabled", True) else "❌"
        print(f"  {enabled} {t['name']}: {t['schedule']} -> {t['skill']}")


def run_task(name: str) -> Dict:
    """执行任务"""
    cfg = load_config()
    task = next((t for t in cfg["tasks"] if t["name"] == name), None)
    if not task:
        return {"error": f"任务不存在: {name}"}

    if not task.get("enabled", True):
        return {"error": f"任务已禁用: {name}"}

    skill = task["skill"]
    args = task.get("args", "")
    log_file = os.path.join(LOG_DIR, f"{name}.log")

    start_time = datetime.now()
    cmd = f"python skills/{skill_to_path(skill)}/main.py {args}"

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n=== {start_time} 执行 ===\n")
            f.write(f"命令: {cmd}\n")
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=300,
            )
            f.write(f"返回码: {result.returncode}\n")
            f.write(f"输出:\n{result.stdout}\n")
            if result.stderr:
                f.write(f"错误:\n{result.stderr}\n")

        # 告警
        if task.get("alert"):
            send_alert(task, result.returncode == 0, result.stdout)

        return {
            "ok": True,
            "returncode": result.returncode,
            "stdout": result.stdout[:2000],  # 截断
            "duration": (datetime.now() - start_time).total_seconds(),
        }
    except subprocess.TimeoutExpired:
        return {"error": "任务执行超时"}
    except Exception as e:
        return {"error": str(e)}


def skill_to_path(skill: str) -> str:
    """Skill 名转路径"""
    path_map = {
        "daily-market-report": "05-reports/daily-market-report",
        "watchlist-monitor": "02-data-collection/watchlist-monitor",
        "limit-up-tracker": "04-stock-analysis/limit-up-tracker",
        "sector-analysis": "03-market-analysis/sector-analysis",
        "market-analysis": "03-market-analysis/market-analysis",
    }
    return path_map.get(skill, skill)


def send_alert(task: Dict, success: bool, output: str):
    """发送告警"""
    try:
        from skills.06-tools.alerter.main import load_config, send
        cfg = load_config()
        channel = task["alert"].get("channel", "dingtalk")
        on = task["alert"].get("on", "success")

        # 判断是否需要告警
        if on == "success" and not success:
            return
        if on == "error" and success:
            return

        channel_cfg = cfg.get("channels", {}).get(channel, {})
        if not channel_cfg:
            return

        title = f"任务执行{'成功' if success else '失败'}: {task['name']}"
        content = f"## {title}\n\n```\n{output[:1500]}\n```"
        send(channel, content, title=title, **channel_cfg)
    except Exception as e:
        print(f"告警发送失败: {e}", file=sys.stderr)


# ============================================================
# 调度器
# ============================================================
def start_scheduler(daemon: bool = False):
    """启动调度器"""
    try:
        import schedule
    except ImportError:
        print("需要安装 schedule: pip install schedule")
        return

    cfg = load_config()
    if not cfg["tasks"]:
        print("无任务, 请先 init 添加")
        return

    for task in cfg["tasks"]:
        if not task.get("enabled", True):
            continue
        name = task["name"]
        cron = task["schedule"]

        # 解析 cron (简化: 只支持 * */n n-m n,m)
        try:
            schedule_task(schedule, task)
            print(f"✅ 已注册: {name} ({cron})")
        except Exception as e:
            print(f"❌ 注册失败 {name}: {e}", file=sys.stderr)

    if daemon:
        print("后台运行中... (Ctrl+C 停止)")
    else:
        print("前台运行中... (Ctrl+C 停止)")

    while True:
        schedule.run_pending()
        time.sleep(60)


def schedule_task(schedule, task: Dict):
    """注册单个任务到 schedule"""
    cron = task["schedule"]
    parts = cron.split()
    if len(parts) == 5:
        minute, hour, day, month, weekday = parts
        # 简化: 暂只支持常用模式
        if minute == "*/30":
            schedule.every(30).minutes.do(run_task, task["name"])
        elif hour == "*":
            schedule.every().minute.do(run_task, task["name"])
        elif "/" in minute:
            n = int(minute.split("/")[1])
            schedule.every(n).minutes.do(run_task, task["name"])
        else:
            # 每天固定时间
            schedule.every().day.at(f"{hour.zfill(2)}:{minute.zfill(2)}").do(run_task, task["name"])


# ============================================================
# 模板
# ============================================================
TEMPLATES = {
    "daily_workflow": {
        "name": "daily_workflow",
        "schedule": "30 15 * * 1-5",
        "skill": "daily-market-report",
        "args": "",
        "enabled": True,
    },
    "intraday_monitor": {
        "name": "intraday_monitor",
        "schedule": "*/30 9-15 * * 1-5",
        "skill": "watchlist-monitor",
        "args": "--config watchlist.yaml",
        "enabled": True,
    },
}


def apply_template(name: str):
    """应用模板"""
    if name not in TEMPLATES:
        print(f"模板不存在: {name}")
        return
    cfg = load_config()
    cfg["tasks"].append(TEMPLATES[name])
    save_config(cfg)
    print(f"✅ 已应用模板: {name}")


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="strategy-scheduler")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init", help="初始化配置")
    sub.add_parser("list", help="列出任务")
    sub.add_parser("start", help="启动调度器").add_argument("--daemon", action="store_true")
    sub.add_parser("stop", help="停止")
    p = sub.add_parser("add", help="添加任务")
    p.add_argument("--name", required=True)
    p.add_argument("--schedule", required=True)
    p.add_argument("--skill", required=True)
    p.add_argument("--args", default="")
    p.add_argument("--alert-channel")
    p.add_argument("--alert-on", default="success", choices=["always", "success", "error"])
    p = sub.add_parser("run", help="手动执行")
    p.add_argument("name")
    p = sub.add_parser("logs", help="查看日志")
    p.add_argument("name")
    p.add_argument("--lines", type=int, default=50)
    p = sub.add_parser("templates", help="列出模板")
    p = sub.add_parser("apply", help="应用模板")
    p.add_argument("name")

    args = parser.parse_args()

    if args.cmd == "init":
        init_config()
    elif args.cmd == "list":
        list_tasks()
    elif args.cmd == "start":
        start_scheduler(args.daemon)
    elif args.cmd == "stop":
        print("(当前版本为单进程, Ctrl+C 停止前台进程)")
    elif args.cmd == "add":
        add_task(args.name, args.schedule, args.skill, args.args,
                 args.alert_channel, args.alert_on)
    elif args.cmd == "run":
        r = run_task(args.name)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    elif args.cmd == "logs":
        log_file = os.path.join(LOG_DIR, f"{args.name}.log")
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines[-args.lines:]:
                print(line, end="")
        else:
            print("无日志")
    elif args.cmd == "templates":
        print("可用模板:")
        for k, v in TEMPLATES.items():
            print(f"  {k}: {v['skill']} ({v['schedule']})")
    elif args.cmd == "apply":
        apply_template(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
