#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report: 报告生成器 (3合1)

合并: daily-market-report + stock-research-report + portfolio-report
子命令: daily / stock / portfolio
"""

import os
import sys
import json
import argparse
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta


def fmt_money(v):
    if v is None or (hasattr(pd, 'isna') and pd.isna(v)):
        return "-"
    try:
        v = float(v)
        if abs(v) >= 1e8:
            return f"{v/1e8:+.2f}亿"
        if abs(v) >= 1e4:
            return f"{v/1e4:+.2f}万"
        return f"{v:+.0f}"
    except Exception:
        return str(v)


def fmt_pct(v):
    if v is None or (hasattr(pd, 'isna') and pd.isna(v)):
        return "-"
    try:
        return f"{float(v):+.2f}%"
    except Exception:
        return str(v)


# ============================================================
# 每日复盘 (daily)
# ============================================================
def report_daily(date: Optional[str] = None, save: bool = False) -> str:
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    md = f"# 📈 A股每日复盘报告\n\n"
    md += f"**日期**: {date}\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

    try:
        import akshare as ak
        # 主要指数
        df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
        if not df.empty:
            df["代码"] = df["代码"].astype(str)
            major = ["000001", "399001", "399006", "000688", "000300", "000905", "000852", "000016"]
            df = df[df["代码"].isin(major)]
            md += "## 📊 一、主要指数\n\n"
            md += "| 名称 | 代码 | 收盘 | 涨跌幅 |\n|------|------|------|--------|\n"
            for _, row in df.iterrows():
                md += f"| {row.get('名称', '')} | {row.get('代码', '')} | {row.get('最新价', 0):.2f} | {fmt_pct(row.get('涨跌幅', 0))} |\n"
            md += "\n"
    except Exception as e:
        md += f"## 指数数据获取失败: {e}\n\n"

    # 市场广度
    try:
        import akshare as ak
        spot = ak.stock_zh_a_spot_em()
        if not spot.empty and "涨跌幅" in spot.columns:
            up = int((spot["涨跌幅"] > 0).sum())
            down = int((spot["涨跌幅"] < 0).sum())
            zt = int((spot["涨跌幅"] >= 9.9).sum())
            dt = int((spot["涨跌幅"] <= -9.9).sum())
            md += "## 📊 二、市场广度\n\n"
            md += f"- 上涨: **{up}** 家\n- 下跌: **{down}** 家\n- 涨停: **{zt}** 家\n- 跌停: **{dt}** 家\n\n"
    except Exception:
        pass

    # 板块
    try:
        import akshare as ak
        ind = ak.stock_board_industry_name_em()
        if not ind.empty:
            rm = {"板块名称": "name", "涨跌幅": "pct_change", "领涨股": "leader"}
            ind = ind.rename(columns={k: v for k, v in rm.items() if k in ind.columns})
            md += "## 🔥 三、行业板块 Top 5\n\n"
            md += "| 行业 | 涨跌幅 | 领涨股 |\n|------|--------|--------|\n"
            for _, row in ind.nlargest(5, "pct_change").iterrows():
                md += f"| {row.get('name', '')} | {fmt_pct(row.get('pct_change', 0))} | {row.get('leader', '')} |\n"
            md += "\n"
    except Exception:
        pass

    # 涨停
    try:
        import akshare as ak
        zt_df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        if not zt_df.empty:
            rm = {"代码": "code", "名称": "name", "涨跌幅": "pct_change", "连板数": "consecutive", "涨停原因": "reason"}
            zt_df = zt_df.rename(columns={k: v for k, v in rm.items() if k in zt_df.columns})
            md += f"## 🚀 四、涨停板统计\n\n涨停数: **{len(zt_df)}**\n\n"
            if "reason" in zt_df.columns:
                # 题材归类
                categories = {"AI/科技": ["AI", "芯片", "半导体"], "新能源": ["锂电", "光伏"],
                              "汽车": ["汽车", "智驾"], "医药": ["医药", "生物"],
                              "重组": ["重组", "并购"]}
                cat_count = {}
                for r in zt_df["reason"]:
                    if r:
                        matched = False
                        for c, kws in categories.items():
                            if any(k in str(r) for k in kws):
                                cat_count[c] = cat_count.get(c, 0) + 1
                                matched = True
                                break
                        if not matched:
                            cat_count["其他"] = cat_count.get("其他", 0) + 1
                if cat_count:
                    md += "**题材分布**:\n"
                    for c, n in sorted(cat_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                        md += f"- {c}: {n}\n"
                    md += "\n"
    except Exception:
        pass

    md += "---\n\n"
    md += "⚠️ 本报告由 A-Stock-Skills 自动生成, 仅供学习研究, 不构成投资建议。\n"

    if save:
        path = f"daily_report_{date}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        md += f"\n报告已保存: `{path}`\n"
    return md


# ============================================================
# 个股研报 (stock)
# ============================================================
def report_stock(code: str, save: bool = False) -> str:
    md = f"# 🔬 个股深度研究报告: {code}\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

    try:
        import akshare as ak
        # 实时行情
        spot = ak.stock_zh_a_spot_em()
        target = spot[spot["代码"].astype(str) == str(code).zfill(6)]
        if not target.empty:
            row = target.iloc[0]
            md += "## 📌 一、公司概况\n\n"
            md += f"- 名称: {row.get('名称', '')}\n"
            md += f"- 现价: {row.get('最新价', 0):.2f}\n"
            md += f"- 涨跌幅: {fmt_pct(row.get('涨跌幅', 0))}\n"
            md += f"- 总市值: {row.get('总市值', 0)/1e8:.2f}亿\n"
            md += f"- PE(TTM): {row.get('市盈率-动态', 0):.2f}\n"
            md += f"- PB: {row.get('市净率', 0):.2f}\n\n"

        # K线 + 技术指标
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=200)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=str(code).zfill(6), period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if not df.empty:
            df.columns = [c.lower() for c in df.columns]
            df["MA5"] = df["close"].rolling(5).mean()
            df["MA20"] = df["close"].rolling(20).mean()
            md += "## 📈 二、技术面\n\n"
            last = df.iloc[-1]
            md += f"- MA5: {last['MA5']:.2f}\n- MA20: {last['MA20']:.2f}\n"
            if last["close"] > last["MA5"] > last["MA20"]:
                md += "- 趋势: **多头排列** ✅\n\n"
            elif last["close"] < last["MA5"] < last["MA20"]:
                md += "- 趋势: **空头排列** ❌\n\n"
            else:
                md += "- 趋势: 震荡\n\n"
    except Exception as e:
        md += f"## 错误: {e}\n\n"

    # 资金流
    try:
        import akshare as ak
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        flow = ak.stock_individual_fund_flow(stock=str(code).zfill(6), market=market)
        if not flow.empty:
            md += "## 💰 三、资金面\n\n"
            md += "**最近 5 日资金流**:\n\n"
            md += "| 日期 | 主力净流入 |\n|------|------------|\n"
            for _, row in flow.head(5).iterrows():
                date = str(row.get("日期", ""))[:10]
                main_net = float(row.get("主力净流入-净额", 0)) if row.get("主力净流入-净额") else 0
                md += f"| {date} | {fmt_money(main_net)} |\n"
            md += "\n"
    except Exception:
        pass

    # 新闻情绪
    try:
        import akshare as ak
        news = ak.stock_news_em(symbol=code)
        if not news.empty:
            md += f"## 📰 四、舆情\n\n最近 {min(5, len(news))} 条新闻:\n\n"
            for _, row in news.head(5).iterrows():
                title = str(row.get("新闻标题", ""))
                md += f"- {title}\n"
            md += "\n"
    except Exception:
        pass

    md += "---\n\n"
    md += "⚠️ 本报告由程序自动生成, 不构成投资建议, 投资有风险, 入市需谨慎。\n"

    if save:
        path = f"research_{code}_{datetime.now().strftime('%Y%m%d')}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        md += f"\n报告已保存: `{path}`\n"
    return md


# ============================================================
# 持仓报告 (portfolio)
# ============================================================
def report_portfolio(config_path: Optional[str] = None, save: bool = False) -> str:
    """持仓报告"""
    DEFAULT_PATHS = ["./portfolio.yaml", "./portfolio.json",
                     "~/.astock_skills/portfolio.yaml"]
    if not config_path:
        for p in DEFAULT_PATHS:
            p = os.path.expanduser(p)
            if os.path.exists(p):
                config_path = p
                break
    if not config_path or not os.path.exists(config_path):
        return "持仓配置文件不存在, 请先 init 生成 portfolio.yaml"

    # 加载
    try:
        if config_path.endswith((".yaml", ".yml")):
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                portfolio = yaml.safe_load(f) or {}
        else:
            with open(config_path, "r", encoding="utf-8") as f:
                portfolio = json.load(f)
    except Exception as e:
        return f"加载配置失败: {e}"

    positions = portfolio.get("positions", [])
    if not positions:
        return "持仓为空"

    md = f"# 📊 持仓报告 - {portfolio.get('name', '我的持仓')}\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

    # 计算
    rows = []
    total_cost = 0
    total_mv = 0
    for p in positions:
        code = p.get("code", "")
        if not code:
            continue
        try:
            import akshare as ak
            spot = ak.stock_zh_a_spot_em()
            target = spot[spot["代码"].astype(str) == str(code).zfill(6)]
            if target.empty:
                continue
            row = target.iloc[0]
            cost = float(p.get("cost", 0))
            shares = int(p.get("shares", 0))
            price = float(row.get("最新价", 0))
            mv = price * shares
            cv = cost * shares
            profit = mv - cv
            total_mv += mv
            total_cost += cv
            rows.append({
                "code": code, "name": p.get("name") or row.get("名称", ""),
                "cost": cost, "shares": shares, "price": price,
                "market_value": mv, "cost_value": cv,
                "profit": profit,
                "profit_pct": (price - cost) / cost * 100 if cost else 0,
                "pct_change_today": float(row.get("涨跌幅", 0)),
            })
        except Exception:
            continue

    # 总览
    total_profit = total_mv - total_cost
    profit_pct = total_profit / total_cost * 100 if total_cost else 0
    win_count = sum(1 for r in rows if r["profit"] > 0)

    md += "## 💰 一、总览\n\n"
    md += f"- 总市值: **{total_mv:,.0f}** 元\n"
    md += f"- 总成本: {total_cost:,.0f} 元\n"
    md += f"- 总盈亏: **{total_profit:+,.0f}** 元 ({profit_pct:+.2f}%)\n"
    md += f"- 持仓: {len(rows)} 只, 盈利 {win_count} 只\n\n"

    # 盈亏明细
    md += "## 💵 二、盈亏明细\n\n"
    md += "| 代码 | 名称 | 成本 | 现价 | 持仓 | 盈亏 | 收益率 |\n"
    md += "|------|------|------|------|------|------|--------|\n"
    for r in sorted(rows, key=lambda x: x["profit_pct"], reverse=True):
        md += f"| {r['code']} | {r['name']} | {r['cost']:.2f} | {r['price']:.2f} | "
        md += f"{r['shares']} | **{r['profit']:+,.0f}** | **{r['profit_pct']:+.2f}%** |\n"
    md += "\n"

    # 调仓建议
    md += "## 🎯 三、调仓建议\n\n"
    if total_mv > 0 and rows:
        max_pos = max(rows, key=lambda x: x["market_value"])
        if max_pos["market_value"] / total_mv > 0.3:
            md += f"- ⚠️ 单股仓位过重 ({max_pos['code']} {max_pos['market_value']/total_mv*100:.1f}%), 建议减仓分散\n"
        max_loss = min(rows, key=lambda x: x["profit_pct"])
        if max_loss["profit_pct"] < -20:
            md += f"- ⚠️ {max_loss['name']} 亏损 {max_loss['profit_pct']:.1f}%, 评估基本面\n"
        if len(rows) > 15:
            md += "- 💡 持仓数量过多, 难以深入跟踪\n"
        elif len(rows) < 3:
            md += "- 💡 持仓数量较少, 集中度风险较高\n"
        if not any(["⚠️" in md for _ in [1]]):
            md += "- ✅ 持仓结构合理\n"

    md += "\n---\n\n"
    md += "⚠️ 本报告基于实时行情自动生成, 不构成投资建议。\n"

    if save:
        path = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        md += f"\n报告已保存: `{path}`\n"
    return md


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="report (3合1)")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("daily", help="每日复盘")
    p.add_argument("--date")
    p.add_argument("--save", action="store_true")

    p = sub.add_parser("stock", help="个股研报")
    p.add_argument("code")
    p.add_argument("--save", action="store_true")

    p = sub.add_parser("portfolio", help="持仓报告")
    p.add_argument("--config")
    p.add_argument("--save", action="store_true")
    args = parser.parse_args()

    if args.cmd == "daily":
        print(report_daily(args.date, args.save))
    elif args.cmd == "stock":
        print(report_stock(args.code, args.save))
    elif args.cmd == "portfolio":
        print(report_portfolio(args.config, args.save))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
