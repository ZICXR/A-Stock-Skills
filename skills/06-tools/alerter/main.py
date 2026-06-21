#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""alerter: 告警推送 (钉钉/微信/Slack/Telegram)"""

import os
import sys
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import argparse
from typing import Optional, Dict


def send_dingtalk(webhook: str, title: str, content: str, secret: str = None) -> bool:
    """钉钉机器人"""
    try:
        import requests
        url = webhook
        # 加签
        if secret:
            timestamp = str(round(time.time() * 1000))
            secret_enc = secret.encode("utf-8")
            string_to_sign = f"{timestamp}\n{secret}"
            string_to_sign_enc = string_to_sign.encode("utf-8")
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            url = f"{webhook}&timestamp={timestamp}&sign={sign}"

        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"## {title}\n\n{content}",
            },
        }
        r = requests.post(url, json=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"钉钉推送失败: {e}", file=sys.stderr)
        return False


def send_wechat(webhook: str, content: str, mentioned: list = None) -> bool:
    """企业微信机器人"""
    try:
        import requests
        data = {
            "msgtype": "markdown",
            "markdown": {"content": content},
        }
        if mentioned:
            data["mentioned_list"] = mentioned
        r = requests.post(webhook, json=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"企业微信推送失败: {e}", file=sys.stderr)
        return False


def send_feishu(webhook: str, content: str) -> bool:
    """飞书机器人"""
    try:
        import requests
        data = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "A股告警"}}},
                "elements": [{"tag": "markdown", "content": content}],
            },
        }
        r = requests.post(webhook, json=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"飞书推送失败: {e}", file=sys.stderr)
        return False


def send_slack(webhook: str, content: str) -> bool:
    """Slack webhook"""
    try:
        import requests
        data = {"text": content, "mrkdwn": True}
        r = requests.post(webhook, json=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Slack 推送失败: {e}", file=sys.stderr)
        return False


def send_telegram(token: str, chat_id: str, content: str) -> bool:
    """Telegram Bot"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": content,
            "parse_mode": "Markdown",
        }
        r = requests.post(url, json=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram 推送失败: {e}", file=sys.stderr)
        return False


def send_serverchan(key: str, title: str, content: str) -> bool:
    """Server 酱 (推送到微信)"""
    try:
        import requests
        url = f"https://sctapi.ftqq.com/{key}.send"
        data = {"title": title, "desp": content}
        r = requests.post(url, data=data, timeout=10)
        return r.status_code == 200 and r.json().get("code") == 0
    except Exception as e:
        print(f"Server 酱推送失败: {e}", file=sys.stderr)
        return False


def send(channel: str, content: str, title: str = "A股告警", **kwargs) -> bool:
    """统一推送入口"""
    if channel == "dingtalk":
        return send_dingtalk(kwargs.get("webhook"), title, content, kwargs.get("secret"))
    elif channel == "wechat":
        return send_wechat(kwargs.get("webhook"), content)
    elif channel == "feishu":
        return send_feishu(kwargs.get("webhook"), content)
    elif channel == "slack":
        return send_slack(kwargs.get("webhook"), content)
    elif channel == "telegram":
        return send_telegram(kwargs.get("token"), kwargs.get("chat_id"), content)
    elif channel == "serverchan":
        return send_serverchan(kwargs.get("key"), title, content)
    else:
        print(f"未知渠道: {channel}", file=sys.stderr)
        return False


def load_config(path: str = None) -> Dict:
    """加载告警配置"""
    if not path:
        path = os.path.expanduser("~/.astock_skills/alert_config.yaml")
    if not os.path.exists(path):
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def main():
    parser = argparse.ArgumentParser(description="alerter")
    sub = parser.add_subparsers(dest="cmd")

    # 钉钉
    p = sub.add_parser("dingtalk", help="钉钉")
    p.add_argument("--webhook", required=True)
    p.add_argument("--secret")
    p.add_argument("--title", default="A股告警")
    p.add_argument("--content", required=True)

    # 企业微信
    p = sub.add_parser("wechat", help="企业微信")
    p.add_argument("--webhook", required=True)
    p.add_argument("--content", required=True)

    # 飞书
    p = sub.add_parser("feishu", help="飞书")
    p.add_argument("--webhook", required=True)
    p.add_argument("--content", required=True)

    # Slack
    p = sub.add_parser("slack", help="Slack")
    p.add_argument("--webhook", required=True)
    p.add_argument("--content", required=True)

    # Telegram
    p = sub.add_parser("telegram", help="Telegram")
    p.add_argument("--token", required=True)
    p.add_argument("--chat_id", required=True)
    p.add_argument("--content", required=True)

    # Server 酱
    p = sub.add_parser("serverchan", help="Server 酱")
    p.add_argument("--key", required=True)
    p.add_argument("--title", default="A股告警")
    p.add_argument("--content", required=True)

    # 通用 send
    p = sub.add_parser("send", help="通用")
    p.add_argument("--channel", required=True,
                   choices=["dingtalk", "wechat", "feishu", "slack", "telegram", "serverchan"])
    p.add_argument("--config", help="配置文件")
    p.add_argument("--content", required=True)
    p.add_argument("--title", default="A股告警")

    # 从 stdin 转发 (用于管道)
    sub.add_parser("forward", help="从 stdin 转发")

    args = parser.parse_args()

    if args.cmd == "dingtalk":
        ok = send_dingtalk(args.webhook, args.title, args.content, args.secret)
    elif args.cmd == "wechat":
        ok = send_wechat(args.webhook, args.content)
    elif args.cmd == "feishu":
        ok = send_feishu(args.webhook, args.content)
    elif args.cmd == "slack":
        ok = send_slack(args.webhook, args.content)
    elif args.cmd == "telegram":
        ok = send_telegram(args.token, args.chat_id, args.content)
    elif args.cmd == "serverchan":
        ok = send_serverchan(args.key, args.title, args.content)
    elif args.cmd == "send":
        cfg = load_config(args.config)
        channel_cfg = cfg.get("channels", {}).get(args.channel, {})
        content = args.content
        if not channel_cfg:
            print(f"配置中未找到 {args.channel}")
            return
        ok = send(args.channel, content, args.title, **channel_cfg)
    elif args.cmd == "forward":
        # 从 stdin 读取
        content = sys.stdin.read()
        if not content.strip():
            print("(空内容, 跳过)")
            return
        # 默认推送到钉钉 (可配)
        cfg = load_config()
        if "dingtalk" in cfg.get("channels", {}):
            d = cfg["channels"]["dingtalk"]
            ok = send_dingtalk(d["webhook"], "A股告警", content, d.get("secret"))
        else:
            print("未配置钉钉 webhook, 无法转发")
            return
    else:
        parser.print_help()
        return

    print("✅ 发送成功" if ok else "❌ 发送失败")


if __name__ == "__main__":
    main()
