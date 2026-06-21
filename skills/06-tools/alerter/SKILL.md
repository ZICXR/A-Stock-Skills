---
name: alerter
description: A 股告警推送工具。当用户需要将告警/报告/监控结果推送到微信/钉钉/Slack/Telegram/企业微信/Server 酱等渠道时,Claude 应使用此 Skill。支持 Markdown 消息、自定义 webhook、批量推送。可与 watchlist-monitor 联动实现盘中实时告警。
---

# A 股告警推送 Skill

## 何时使用

- 用户需要微信/钉钉/Slack 通知
- 用户需要将告警实时推送
- 用户需要集成企业微信/Server酱
- 用户需要批量推送报告

## 支持的渠道

| 渠道 | 难度 | 适用 |
|------|------|------|
| 钉钉 | 易 | 团队 |
| 飞书 | 易 | 团队 |
| 企业微信 | 易 | 企业 |
| Slack | 易 | 海外团队 |
| Telegram | 中 | 个人 |
| Server 酱 (微信) | 易 | 个人微信 |
| 自定义 Webhook | 易 | 通用 |
| 邮件 (SMTP) | 中 | 传统 |

## 使用方式

### 1. 钉钉推送

```bash
python main.py dingtalk \
    --webhook "https://oapi.dingtalk.com/robot/send?access_token=xxx" \
    --title "涨停板告警" \
    --content "## 今日涨停 56 只\n- 000001 平安银行"
```

### 2. 企业微信推送

```bash
python main.py wechat \
    --webhook "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" \
    --content "今日复盘..."
```

### 3. Server 酱 (推送到微信)

```bash
python main.py serverchan \
    --key "SCT123xxx" \
    --title "涨停告警" \
    --content "..."
```

### 4. 飞书推送

```bash
python main.py feishu \
    --webhook "https://open.feishu.cn/open-apis/bot/v2/hook/xxx" \
    --content "..."
```

### 5. 配置文件 (推荐)

编辑 `~/.astock_skills/alert_config.yaml`:

```yaml
channels:
  dingtalk:
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    secret: "SEC..."
  wechat:
    webhook: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
  serverchan:
    key: "SCTxxx"
  feishu:
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

然后:

```bash
python main.py send --channel dingtalk --content "..."
```

## Python API

```python
from skills.06-tools.alerter.main import send

# 钉钉
send("dingtalk", title="告警", content="## 内容", webhook="...")

# 企业微信
send("wechat", content="...", webhook="...")

# 从配置文件
send("dingtalk", content="...", config="~/.astock_skills/alert_config.yaml")
```

## 与 watchlist-monitor 集成

```bash
# 监控 + 推送
python skills/02-data-collection/watchlist-monitor/main.py monitor \
    --config watchlist.yaml \
    | python skills/06-tools/alerter/main.py forward --channel dingtalk
```

## 依赖

```
requests>=2.28.0
pyyaml>=5.4.0
```
