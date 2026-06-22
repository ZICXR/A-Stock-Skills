# A-Stock-Skills

## 一句话: 让 Claude 帮你看 A 股。

**不装插件, 不学新软件, 装好之后 Claude 自己会用。**

## 上手 (3 行命令)

```bash
git clone https://github.com/ZICXR/A-Stock-Skills.git
cd A-Stock-Skills
pip install -r requirements.txt
```

打开 Claude Code, 直接说:
> "601991 现在多少钱?"

Claude 自动拉数据:

```
601991 大唐发电  3.20  +5.26%  (数据源: 腾讯 ifzq)
```

> "全市场 PE < 20, 涨 5% 以上的股票"

```
找到 23 只
  600519  贵州茅台  1680  PE 18.5
  300750  宁德时代   220  PE 19.2
  ...
```

> "监控我的自选股, 涨 5% 推钉钉"

```yaml
# watchlist.yaml
- 601991  大唐发电
- 300750  宁德时代
```

收到推送, 30 天后看 `trade-journal` 统计 AI 推荐胜率: **58%**。

## 跑过一次, 5 秒

```bash
python daily_update.py   # 首次 30 分钟
python skills/05-quant/screener/main.py screen --where "pe<20"  # 5 秒
```

## 10 个工具

| 名字 | 干啥 |
|------|------|
| `astock-data-source` | 拿行情 (4 源 fallback) |
| `astock-cache` | 缓存 K 线 (parquet) |
| `screener` | 全市场筛选 |
| `watchlist-monitor` | 自选股监控 |
| `stock-technical-analysis` | MA/MACD/KDJ/RSI |
| `trade-journal` | AI 推荐 vs 实盘复盘 |
| `report` | 生成研报 |
| `alerter` | 钉钉/微信/飞书 |
| `astock-utils` | 工具函数 |
| `start-here` | 上手 |

## 注意

- 不接券商账号, **交易还是你来**
- **不构成投资建议**, 投资有风险

## License

MIT
