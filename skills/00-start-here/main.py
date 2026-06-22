#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""start-here: 30 秒上手指南"""

import sys

BANNER = """
╔══════════════════════════════════════════════════════╗
║         A-Stock-Skills · 30 秒上手指南                 ║
╚══════════════════════════════════════════════════════╝

📦 10 个核心 Skill:

  1. astock-data-source    拿行情/K线 (多源 fallback)
  2. astock-cache          K线 parquet 缓存
  3. astock-utils          代码转换/交易日历
  4. watchlist-monitor     监控自选股
  5. screener              全市场筛选
  6. stock-technical-analysis  技术指标
  7. report                复盘报告
  8. alerter               推送告警
  9. trade-journal         AI vs 实盘 复盘  🆕
 10. start-here            本指南  🆕

🎯 5 个真实场景 (见 SKILL.md):
   1. 拿行情        python skills/01-infra/astock-data-source/main.py get-realtime --code 601991
   2. 拿 K 线       (用 astock-data-source get-kline)
   3. 全市场筛选    python skills/05-quant/screener/main.py screen --pe-max 20
   4. 监控自选股    python skills/02-data-collection/watchlist-monitor/main.py init
   5. 复盘 AI      python skills/02-data-collection/trade-journal/main.py record --code 601991 ...

📖 详细使用: 阅读 SKILL.md
🛡️ 免责声明: 仅供学习研究,不构成投资建议
"""


def main():
    print(BANNER)
    print("\n💡 推荐: 从 '拿一只股票行情' 开始,5 分钟跑通第一个场景")


if __name__ == "__main__":
    main()
