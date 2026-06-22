# A-Stock-Skills

让 Claude 帮你看 A 股。

10 个工具, 一次安装, 3 分钟跑通。

## 安装

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
pip install -r requirements.txt
```

## 用法

打开 Claude Code, 直接说:

> 帮我用 screener 找 PE 小于 20 的股票
>
> 601991 现在多少钱?
>
> 监控我的自选股, 涨 5% 提醒我
>
> 记录一下这个推荐, 30 天后看准不准

Claude 会自己选工具、跑命令。

## 工具列表

- `astock-data-source` - 拿股票数据
- `astock-cache` - 缓存, 跑一次, 之后 5 秒
- `screener` - 全市场筛选
- `watchlist-monitor` - 监控自选股
- `stock-technical-analysis` - 算技术指标
- `report` - 生成研报
- `alerter` - 推送到钉钉/微信
- `trade-journal` - 记录推荐, 30 天后看准不准
- `astock-utils` - 工具函数
- `start-here` - 入门指南

## 命令行也能用

```bash
# 拿行情
python skills/01-infra/astock-data-source/main.py get-realtime --code 601991

# 筛选
python skills/05-quant/screener/main.py screen --where "pe<20"

# 跑一次缓存, 之后 5 秒
python daily_update.py
```

## 注意事项

- 不接券商账号, 交易还是你自己来
- 数据来自公开接口, **不构成投资建议**
- 投资有风险, 入市需谨慎

## License

MIT
