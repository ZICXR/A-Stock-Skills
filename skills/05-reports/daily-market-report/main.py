#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily-market-report: 每日复盘报告生成器"""

import sys
import os
import argparse
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


# ============================================================
# 工具函数
# ============================================================
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
    except:
        return str(v)


def fmt_pct(v):
    if v is None or (hasattr(pd, 'isna') and pd.isna(v)):
        return "-"
    try:
        return f"{float(v):+.2f}%"
    except:
        return str(v)


# ============================================================
# 1. 大盘部分
# ============================================================
def build_market_section() -> str:
    md = "## 📊 一、大盘表现\n\n"

    # 主要指数
    try:
        import akshare as ak
        df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
    except Exception as e:
        return md + f"获取指数失败: {e}\n\n"

    if df.empty:
        return md + "无指数数据\n\n"

    # 重要指数
    major = ["000001", "399001", "399006", "000688", "000300", "000905", "000852", "000016"]
    df["代码"] = df["代码"].astype(str)
    df = df[df["代码"].isin(major)]

    md += "### 主要指数\n\n"
    md += "| 名称 | 代码 | 收盘 | 涨跌幅 |\n"
    md += "|------|------|------|--------|\n"
    for _, row in df.iterrows():
        md += f"| {row.get('名称', '')} | {row.get('代码', '')} | "
        md += f"{row.get('最新价', 0):.2f} | {fmt_pct(row.get('涨跌幅', 0))} |\n"
    md += "\n"

    # 市场广度
    try:
        spot_df = ak.stock_zh_a_spot_em()
        if not spot_df.empty and "涨跌幅" in spot_df.columns:
            up = int((spot_df["涨跌幅"] > 0).sum())
            down = int((spot_df["涨跌幅"] < 0).sum())
            flat = int((spot_df["涨跌幅"] == 0).sum())
            zt = int((spot_df["涨跌幅"] >= 9.9).sum())
            dt = int((spot_df["涨跌幅"] <= -9.9).sum())
            ratio = round(up / len(spot_df) * 100, 2) if len(spot_df) else 0
            md += "### 市场广度\n\n"
            md += f"- 上涨: **{up}** 家\n"
            md += f"- 下跌: **{down}** 家\n"
            md += f"- 平盘: {flat} 家\n"
            md += f"- 涨停: **{zt}** 家\n"
            md += f"- 跌停: **{dt}** 家\n"
            md += f"- 上涨比例: {ratio}%\n\n"
    except Exception:
        pass

    return md


# ============================================================
# 2. 板块部分
# ============================================================
def build_sector_section() -> str:
    md = "## 🔥 二、板块热点\n\n"

    # 行业板块
    try:
        import akshare as ak
        df = ak.stock_board_industry_name_em()
    except Exception:
        return md + "获取板块失败\n\n"

    if df.empty:
        return md + "无板块数据\n\n"

    rename_map = {"板块名称": "name", "涨跌幅": "pct_change",
                  "领涨股": "leader", "领涨股涨跌幅": "leader_pct",
                  "上涨家数": "up_count", "下跌家数": "down_count"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    md += "### 行业板块涨幅 Top 10\n\n"
    md += "| 行业 | 涨跌幅 | 领涨股 | 上涨/下跌 |\n"
    md += "|------|--------|--------|-----------|\n"
    for _, row in df.nlargest(10, "pct_change").iterrows():
        md += f"| {row.get('name', '')} | {fmt_pct(row.get('pct_change', 0))} | "
        md += f"{row.get('leader', '')} | "
        md += f"{row.get('up_count', 0)}/{row.get('down_count', 0)} |\n"
    md += "\n"

    md += "### 行业板块跌幅 Top 5\n\n"
    md += "| 行业 | 涨跌幅 | 领涨股 |\n"
    md += "|------|--------|--------|\n"
    for _, row in df.nsmallest(5, "pct_change").iterrows():
        md += f"| {row.get('name', '')} | {fmt_pct(row.get('pct_change', 0))} | "
        md += f"{row.get('leader', '')} |\n"
    md += "\n"

    # 资金流入榜
    try:
        flow = ak.stock_sector_fund_flow_rank(indicator="今日")
        if not flow.empty and "主力净流入-净额" in flow.columns:
            md += "### 资金流入 Top 5\n\n"
            md += "| 行业 | 涨跌幅 | 主力净流入 |\n"
            md += "|------|--------|------------|\n"
            for _, row in flow.nlargest(5, "主力净流入-净额").iterrows():
                md += f"| {row.get('名称', '')} | {fmt_pct(row.get('今日涨跌幅', 0))} | "
                md += f"{fmt_money(row.get('主力净流入-净额', 0))} |\n"
            md += "\n"
    except Exception:
        pass

    return md


# ============================================================
# 3. 涨停部分
# ============================================================
def build_zt_section(date: Optional[str] = None) -> str:
    md = "## 🚀 三、涨停板分析\n\n"

    if not date:
        date = datetime.now().strftime("%Y%m%d")

    try:
        import akshare as ak
        zt = ak.stock_zt_pool_em(date=date)
    except Exception:
        return md + "获取涨停板失败\n\n"

    if zt.empty:
        return md + "无涨停数据\n\n"

    md += f"### 当日涨停统计\n\n"
    md += f"- 涨停家数: **{len(zt)}**\n"

    # 炸板率
    try:
        zt_zb = ak.stock_zt_pool_zbgc_em(date=date)
        if not zt_zb.empty:
            zt_count = len(zt)
            zbgc_count = len(zt_zb)
            broken = max(0, zbgc_count - zt_count)
            rate = round(broken / zbgc_count * 100, 2) if zbgc_count else 0
            md += f"- 曾涨停: {zbgc_count}\n"
            md += f"- 炸板: {broken}\n"
            md += f"- 炸板率: **{rate}%**\n"
    except Exception:
        pass
    md += "\n"

    # 涨停原因归类
    REASON_CATS = {
        "AI/科技": ["AI", "人工智能", "算力", "大模型", "芯片", "半导体", "数字"],
        "新能源": ["锂电", "光伏", "新能源", "储能", "电池"],
        "汽车": ["汽车", "整车", "造车", "智驾", "无人驾驶"],
        "医药": ["医药", "生物", "创新药"],
        "军工": ["军工", "国防", "航天"],
        "消费": ["消费", "白酒", "食品", "饮料"],
        "金融": ["证券", "银行", "保险"],
        "重组": ["重组", "并购", "借壳", "收购"],
    }

    def cat_reason(r):
        if not r:
            return "其他"
        for c, kws in REASON_CATS.items():
            if any(k in str(r) for k in kws):
                return c
        return "其他"

    if "涨停原因" in zt.columns:
        zt["_cat"] = zt["涨停原因"].apply(cat_reason)
        cat_count = zt["_cat"].value_counts()
        md += "### 涨停原因分布\n\n"
        md += "| 题材 | 数量 |\n"
        md += "|------|------|\n"
        for c, n in cat_count.head(8).items():
            md += f"| {c} | {n} |\n"
        md += "\n"

    # 涨停 Top 10
    rename_map = {"代码": "code", "名称": "name", "涨跌幅": "pct_change",
                  "连板数": "consecutive", "封板资金": "limit_funds"}
    zt = zt.rename(columns={k: v for k, v in rename_map.items() if k in zt.columns})

    md += "### 涨停个股 Top 10\n\n"
    md += "| 代码 | 名称 | 涨跌幅 | 连板 | 封板资金 |\n"
    md += "|------|------|--------|------|----------|\n"
    for _, row in zt.head(10).iterrows():
        md += f"| {row.get('code', '')} | {row.get('name', '')} | "
        md += f"{fmt_pct(row.get('pct_change', 0))} | "
        md += f"{row.get('consecutive', '-')} | "
        md += f"{fmt_money(row.get('limit_funds', 0))} |\n"
    md += "\n"

    return md


# ============================================================
# 4. 资金部分
# ============================================================
def build_capital_section() -> str:
    md = "## 💰 四、资金流向\n\n"

    # 大盘资金流
    try:
        import akshare as ak
        mf = ak.stock_market_fund_flow()
        if not mf.empty:
            md += "### 大盘资金流\n\n"
            md += "| 市场 | 主力净流入 | 超大单 | 大单 | 中单 | 小单 |\n"
            md += "|------|-----------|--------|------|------|------|\n"
            for _, row in mf.iterrows():
                md += f"| {row.get('市场', '')} | "
                md += f"{fmt_money(row.get('主力净流入-净额', 0))} | "
                md += f"{fmt_money(row.get('超大单净流入-净额', 0))} | "
                md += f"{fmt_money(row.get('大单净流入-净额', 0))} | "
                md += f"{fmt_money(row.get('中单净流入-净额', 0))} | "
                md += f"{fmt_money(row.get('小单净流入-净额', 0))} |\n"
            md += "\n"
    except Exception:
        pass

    # 北向资金
    try:
        import akshare as ak
        nb = ak.stock_hsgt_fund_flow_summary_em()
        if not nb.empty:
            md += "### 北向资金 (近5日)\n\n"
            md += "| 日期 | 资金净流入 | 成交总额 |\n"
            md += "|------|-----------|----------|\n"
            for _, row in nb.head(5).iterrows():
                md += f"| {row.get('日期', '')} | "
                md += f"{fmt_money(row.get('资金净流入', 0))} | "
                md += f"{fmt_money(row.get('成交总额', 0))} |\n"
            md += "\n"
    except Exception:
        pass

    return md


# ============================================================
# 5. 龙虎榜部分
# ============================================================
def build_lhb_section() -> str:
    md = "## 🐉 五、龙虎榜\n\n"

    try:
        import akshare as ak
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        lhb = ak.stock_lhb_detail_em(start_date=date, end_date=date)
        if not lhb.empty and "代码" in lhb.columns:
            unique_stocks = lhb["代码"].unique()
            md += f"- 龙虎榜个股数: **{len(unique_stocks)}**\n"
            md += f"- 总记录数: {len(lhb)}\n\n"

            # 上榜次数最多的
            top = lhb["代码"].value_counts().head(10)
            md += "### 上榜次数 Top 10\n\n"
            md += "| 代码 | 名称 | 上榜次数 |\n"
            md += "|------|------|----------|\n"
            for code, count in top.items():
                name = lhb[lhb["代码"] == code]["名称"].iloc[0] if "名称" in lhb.columns else ""
                md += f"| {code} | {name} | {count} |\n"
            md += "\n"
        else:
            md += "无龙虎榜数据\n\n"
    except Exception as e:
        md += f"获取龙虎榜失败: {e}\n\n"

    return md


# ============================================================
# 6. 完整报告
# ============================================================
def generate_daily_report(date: Optional[str] = None, save_path: Optional[str] = None) -> str:
    """生成完整每日复盘报告"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    md = f"# 📈 A股每日复盘报告\n\n"
    md += f"**日期**: {date}\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"

    sections = []
    for builder in [build_market_section, build_sector_section,
                    lambda: build_zt_section(date), build_capital_section,
                    build_lhb_section]:
        try:
            sections.append(builder())
        except Exception as e:
            md += f"## 部分出错: {e}\n\n"

    for s in sections:
        md += s

    md += "---\n\n"
    md += "## ⚠️ 免责声明\n\n"
    md += "本报告由 A-Stock-Skills 自动生成, 所有数据来源于公开市场数据, 仅供学习研究使用, 不构成任何投资建议。投资有风险, 入市需谨慎。\n"

    if save_path is None:
        save_path = f"daily_report_{date}.md"
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(md)
    except Exception as e:
        print(f"保存失败: {e}", file=sys.stderr)

    return md


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="daily-market-report")
    parser.add_argument("--date", help="日期 YYYY-MM-DD")
    parser.add_argument("--save", help="保存路径")
    parser.add_argument("--section", choices=["market", "sector", "zt", "capital", "lhb", "full"],
                        default="full", help="输出部分")
    args = parser.parse_args()

    if args.section == "market":
        print(build_market_section())
    elif args.section == "sector":
        print(build_sector_section())
    elif args.section == "zt":
        date = args.date.replace("-", "") if args.date else None
        print(build_zt_section(date))
    elif args.section == "capital":
        print(build_capital_section())
    elif args.section == "lhb":
        print(build_lhb_section())
    else:
        report = generate_daily_report(args.date, args.save)
        print(report)


if __name__ == "__main__":
    main()
