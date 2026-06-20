"""
daily-market-report: 每日大盘复盘报告
======================================

功能:
    - 整合所有分析模块
    - 生成结构化日报
    - 输出 Markdown / Text 格式
    - 大盘 + 板块 + 涨停 + 资金 全景报告
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys

logger = logging.getLogger(__name__)

# 引入各模块
sys.path.insert(0, "skills/01-infra")
sys.path.insert(0, "skills/02-data-collection")
sys.path.insert(0, "skills/03-market-analysis")
sys.path.insert(0, "skills/04-stock-analysis")

from astock_utils.astock_utils import (
    normalize_stock_code, fmt_volume, fmt_money, fmt_pct
)

from market_data_collector.market_data_collector import (
    get_major_indices, get_market_breadth, calc_market_strength
)
from sector_data_collector.sector_data_collector import (
    get_industry_sectors, get_concept_sectors, get_sector_fund_flow
)
from capital_flow_analysis.capital_flow_analysis import (
    get_market_fund_flow, get_north_bound_today, get_north_bound_flow
)
from dragon_tiger_analysis.dragon_tiger_analysis import lhb_daily_report
from limit_up_tracker.limit_up_tracker import (
    get_zt_pool, get_consecutive_zt, calc_break_rate, summarize_zt_reasons
)
from sector_analysis.sector_analysis import (
    identify_main_themes, detect_rotation_signal
)


# ============================================================
# 1. 大盘部分
# ============================================================
def build_market_section() -> str:
    """构建大盘部分"""
    md = "## 📊 一、大盘表现\n\n"

    # 主要指数
    df = get_major_indices()
    if not df.empty:
        md += "### 主要指数\n\n"
        md += "| 名称 | 代码 | 收盘 | 涨跌幅 | 涨跌额 |\n"
        md += "|------|------|------|--------|--------|\n"
        for _, row in df.iterrows():
            md += f"| {row.get('name', '')} | {row.get('code', '')} | "
            md += f"{row.get('price', 0):.2f} | {fmt_pct(row.get('pct_change', 0))} | "
            md += f"{row.get('change', 0):.2f} |\n"
        md += "\n"

    # 市场广度
    breadth = get_market_breadth()
    if breadth:
        strength = calc_market_strength(breadth)
        md += "### 市场广度\n\n"
        md += f"- **上涨家数**: {breadth.get('up', 0)}\n"
        md += f"- **下跌家数**: {breadth.get('down', 0)}\n"
        md += f"- **平盘家数**: {breadth.get('flat', 0)}\n"
        md += f"- **涨停**: {breadth.get('limit_up', 0)} 家\n"
        md += f"- **跌停**: {breadth.get('limit_down', 0)} 家\n"
        md += f"- **上涨比例**: {breadth.get('up_ratio', 0)}%\n"
        md += f"- **市场强度**: {strength.get('desc', 'N/A')} (评分: {strength.get('score', 0)})\n\n"

    # 大盘趋势
    try:
        from market_analysis.market_analysis import full_market_analysis
        result = full_market_analysis("000001", days=30)
        if result:
            md += f"### 大盘研判\n\n"
            md += f"- **趋势**: {result['trend']['overall']} (评分: {result['trend']['total_score']})\n"
            md += f"- **建议**: {result['advice']}\n"
            if result['volume_price']:
                md += f"- **量价**: {result['volume_price'].get('signal', 'N/A')}\n"
            md += "\n"
    except Exception as e:
        logger.warning(f"大盘分析失败: {e}")

    return md


# ============================================================
# 2. 板块部分
# ============================================================
def build_sector_section() -> str:
    """构建板块部分"""
    md = "## 🔥 二、板块热点\n\n"

    # 行业板块涨幅榜
    df = get_industry_sectors()
    if not df.empty:
        md += "### 行业板块涨幅 Top 10\n\n"
        md += "| 行业 | 涨跌幅 | 领涨股 | 领涨股涨幅 | 上涨/下跌 |\n"
        md += "|------|--------|--------|------------|-----------|\n"
        for _, row in df.nlargest(10, "pct_change").iterrows():
            md += f"| {row.get('name', '')} | {fmt_pct(row.get('pct_change', 0))} | "
            md += f"{row.get('leader', '')} | {fmt_pct(row.get('leader_pct', 0))} | "
            md += f"{row.get('up_count', 0)}/{row.get('down_count', 0)} |\n"
        md += "\n"

        # 跌幅榜
        md += "### 行业板块跌幅 Top 5\n\n"
        md += "| 行业 | 涨跌幅 | 领跌股 |\n"
        md += "|------|--------|--------|\n"
        for _, row in df.nsmallest(5, "pct_change").iterrows():
            md += f"| {row.get('name', '')} | {fmt_pct(row.get('pct_change', 0))} | "
            md += f"{row.get('leader', '')} |\n"
        md += "\n"

    # 资金流入榜
    ff = get_sector_fund_flow("今日")
    if not ff.empty:
        sort_col = "main_net" if "main_net" in ff.columns else None
        if sort_col:
            md += "### 资金流入 Top 5\n\n"
            md += "| 行业 | 涨跌幅 | 主力净流入 |\n"
            md += "|------|--------|------------|\n"
            for _, row in ff.nlargest(5, sort_col).iterrows():
                md += f"| {row.get('name', '')} | {fmt_pct(row.get('pct_change', 0))} | "
                md += f"{fmt_money(row.get(sort_col, 0))} |\n"
            md += "\n"

    # 主线板块
    try:
        themes = identify_main_themes(top_n=5)
        if themes.get("main_themes"):
            md += "### 🎯 主线板块识别\n\n"
            for t in themes["main_themes"][:5]:
                md += f"- **[{t['type']}] {t['name']}**: 涨幅{fmt_pct(t.get('pct_change', 0))}, "
                md += f"资金{fmt_money(t.get('main_net', 0))}, 龙头: {t.get('leader', 'N/A')}\n"
            md += "\n"
    except Exception as e:
        logger.warning(f"主线识别失败: {e}")

    return md


# ============================================================
# 3. 涨停部分
# ============================================================
def build_zt_section(date: Optional[str] = None) -> str:
    """构建涨停板部分"""
    md = "## 🚀 三、涨停板分析\n\n"

    zt_df = get_zt_pool(date)
    if zt_df.empty:
        md += "暂无涨停数据\n\n"
        return md

    md += f"### 当日涨停统计\n\n"
    md += f"- 涨停家数: **{len(zt_df)}**\n"

    # 炸板率
    br = calc_break_rate(date)
    if br:
        md += f"- 曾涨停数: {br.get('zb_count', 0)}\n"
        md += f"- 炸板数: {br.get('broken', 0)}\n"
        md += f"- 炸板率: **{br.get('break_rate', 0)}%**\n"
    md += "\n"

    # 连板梯队
    cons = get_consecutive_zt(days=5)
    if not cons.empty:
        md += "### 连板梯队\n\n"
        md += "| 连板数 | 数量 | 代表个股 |\n"
        md += "|--------|------|----------|\n"
        for _, row in cons.iterrows():
            stocks_str = ", ".join(row.get("stocks", [])[:3]) if row.get("stocks") else "-"
            md += f"| {row['consecutive']}板 | {row['count']} | {stocks_str} |\n"
        md += "\n"

    # 涨停原因
    reason_summary = summarize_zt_reasons(zt_df)
    if not reason_summary.empty:
        md += "### 涨停原因分布\n\n"
        md += "| 题材 | 数量 |\n"
        md += "|------|------|\n"
        for _, row in reason_summary.head(10).iterrows():
            md += f"| {row.get('category', '')} | {row.get('count', 0)} |\n"
        md += "\n"

    # 涨停个股 Top 10
    md += "### 涨停个股 Top 10 (按强度)\n\n"
    md += "| 代码 | 名称 | 涨跌幅 | 连板 | 封板资金 |\n"
    md += "|------|------|--------|------|----------|\n"
    top10 = zt_df.head(10)
    for _, row in top10.iterrows():
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
    """构建资金部分"""
    md = "## 💰 四、资金流向\n\n"

    # 北向资金
    nb_today = get_north_bound_today()
    if nb_today:
        md += "### 北向资金\n\n"
        for k, v in nb_today.items():
            if v is not None and pd.notna(v):
                md += f"- {k}: {v}\n"
        md += "\n"

    # 大盘资金流
    mf = get_market_fund_flow()
    if mf:
        md += "### 大盘资金流\n\n"
        for market, data in mf.items():
            md += f"**{market}**\n\n"
            for k, v in data.items():
                if v is not None and pd.notna(v):
                    md += f"- {k}: {v}\n"
            md += "\n"

    return md


# ============================================================
# 5. 龙虎榜部分
# ============================================================
def build_lhb_section() -> str:
    """构建龙虎榜部分"""
    md = "## 🐉 五、龙虎榜\n\n"
    try:
        report = lhb_daily_report()
        if report.get("summary"):
            summary = report["summary"]
            md += f"- 龙虎榜个股数: {summary.get('lhb_stocks', 0)}\n"
            md += f"- 涨停板: {summary.get('zt_stocks', 0)}\n"
            md += f"- 游资参与: {summary.get('hot_money_count', 0)} 条\n"
            md += f"- 机构参与: {summary.get('institution_count', 0)} 条\n\n"

        hot_money = report.get("hot_money")
        if hot_money is not None and not hot_money.empty:
            md += "### 知名游资动向\n\n"
            md += hot_money.head(5).to_markdown() if hasattr(hot_money, 'to_markdown') else ""
            md += "\n"
    except Exception as e:
        logger.warning(f"龙虎榜部分失败: {e}")
        md += "数据获取失败\n\n"
    return md


# ============================================================
# 6. 完整报告
# ============================================================
def generate_daily_report(date: Optional[str] = None, save_path: Optional[str] = None) -> str:
    """生成完整每日复盘报告
    Args:
        date: 日期 YYYY-MM-DD
        save_path: 保存路径, 默认 ./daily_report_{date}.md
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 标题
    md = f"# 📈 A股每日复盘报告\n\n"
    md += f"**日期**: {date}\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"

    # 拼装各部分
    sections = []
    try:
        sections.append(build_market_section())
    except Exception as e:
        md += f"## 大盘部分出错: {e}\n\n"

    try:
        sections.append(build_sector_section())
    except Exception as e:
        md += f"## 板块部分出错: {e}\n\n"

    try:
        sections.append(build_zt_section(date))
    except Exception as e:
        md += f"## 涨停部分出错: {e}\n\n"

    try:
        sections.append(build_capital_section())
    except Exception as e:
        md += f"## 资金部分出错: {e}\n\n"

    try:
        sections.append(build_lhb_section())
    except Exception as e:
        md += f"## 龙虎榜部分出错: {e}\n\n"

    for section in sections:
        md += section

    # 免责声明
    md += "---\n\n"
    md += "## ⚠️ 免责声明\n\n"
    md += "本报告由 A-Stock-Skills 自动生成, 所有数据来源于公开市场数据, 仅供学习研究使用, 不构成任何投资建议。投资有风险, 入市需谨慎。\n"

    # 保存
    if save_path is None:
        save_path = f"daily_report_{date}.md"
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(md)
        md += f"\n\n报告已保存到: `{save_path}`\n"
    except Exception as e:
        logger.error(f"保存报告失败: {e}")

    return md


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("正在生成每日复盘报告...")
    report = generate_daily_report()
    print(report[:2000])  # 打印前2000字符
    print(f"\n\n报告总长度: {len(report)} 字符")
