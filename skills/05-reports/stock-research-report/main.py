#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-research-report: 个股深度研报生成器"""

import sys
import argparse
import pandas as pd
from datetime import datetime
from typing import Optional


def build_company_section(code: str) -> str:
    """公司概况"""
    md = "## 📌 一、公司概况\n\n"
    try:
        import akshare as ak
        # 实时行情
        spot = ak.stock_zh_a_spot_em()
        target = spot[spot["代码"].astype(str) == str(code).zfill(6)]
        if not target.empty:
            row = target.iloc[0]
            md += f"- **股票名称**: {row.get('名称', '')}\n"
            md += f"- **股票代码**: {row.get('代码', '')}\n"
            md += f"- **最新价**: {row.get('最新价', 0):.2f}\n"
            md += f"- **涨跌幅**: {row.get('涨跌幅', 0):+.2f}%\n"
            md += f"- **总市值**: {float(row.get('总市值', 0))/1e8:.2f}亿\n"
            md += f"- **流通市值**: {float(row.get('流通市值', 0))/1e8:.2f}亿\n"
            md += f"- **换手率**: {row.get('换手率', 0):.2f}%\n"
        # 公司信息
        try:
            df = ak.stock_individual_info_em(symbol=code)
            for _, row in df.iterrows():
                item = row.get("item", "")
                val = row.get("value", "")
                if item in ["股票简称", "所属行业", "上市日期", "总股本", "流通股本", "公司全称"]:
                    md += f"- **{item}**: {val}\n"
        except Exception:
            pass
    except Exception as e:
        md += f"获取失败: {e}\n"
    return md + "\n"


def build_technical_section(code: str) -> str:
    """技术面"""
    md = "## 📈 二、技术面分析\n\n"
    try:
        import akshare as ak
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=200)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=str(code).zfill(6), period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if df.empty:
            return md + "无数据\n\n"
        df.columns = [c.lower() for c in df.columns]

        # 计算指标
        df["MA5"] = df["close"].rolling(5).mean()
        df["MA20"] = df["close"].rolling(20).mean()
        df["MA60"] = df["close"].rolling(60).mean()
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["DIF"] = ema12 - ema26
        df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
        df["MACD"] = (df["DIF"] - df["DEA"]) * 2

        last = df.iloc[-1]
        prev = df.iloc[-2]
        signals = []
        score = 0

        # 均线
        if last["MA5"] > last["MA20"] > last["MA60"]:
            signals.append(("均线多头", 2, "短期多头排列"))
            score += 2
        elif last["MA5"] < last["MA20"] < last["MA60"]:
            signals.append(("均线空头", -2, "短期空头排列"))
            score -= 2
        if last["close"] > last["MA20"]:
            signals.append(("站上MA20", 1, ""))
            score += 1
        elif last["close"] < last["MA20"]:
            signals.append(("跌破MA20", -1, ""))
            score -= 1

        # MACD
        if last["DIF"] > last["DEA"] and prev["DIF"] <= prev["DEA"]:
            signals.append(("MACD金叉", 2, "DIF上穿DEA"))
            score += 2
        elif last["DIF"] < last["DEA"] and prev["DIF"] >= prev["DEA"]:
            signals.append(("MACD死叉", -2, "DIF下穿DEA"))
            score -= 2

        if score >= 3:
            trend = "强势上涨"
        elif score >= 1:
            trend = "偏多"
        elif score <= -3:
            trend = "强势下跌"
        elif score <= -1:
            trend = "偏空"
        else:
            trend = "震荡"

        md += f"- **趋势研判**: {trend} (评分: {score})\n"
        md += f"- **关键点位**:\n"
        md += f"  - MA5: {last['MA5']:.2f}\n"
        md += f"  - MA20: {last['MA20']:.2f}\n"
        md += f"  - MA60: {last['MA60']:.2f}\n"
        md += f"- **MACD**: DIF={last['DIF']:.4f}, DEA={last['DEA']:.4f}\n"
        md += f"- **技术信号**:\n"
        for s in signals:
            md += f"  - {s[0]}: {s[2]}\n"
    except Exception as e:
        md += f"获取失败: {e}\n"
    return md + "\n"


def build_fundamental_section(code: str) -> str:
    """基本面"""
    md = "## 💼 三、基本面分析\n\n"
    try:
        import akshare as ak
        df = ak.stock_financial_abstract_ths(symbol=code)
        if df.empty:
            return md + "无数据\n\n"
        # 提取关键指标
        latest_row = df.iloc[0] if len(df) > 0 else None
        if latest_row is not None:
            md += f"**最新报告期数据**:\n\n"
            for col in df.columns:
                val = latest_row[col]
                if val is not None and not (hasattr(pd, 'isna') and pd.isna(val)):
                    if any(kw in str(col) for kw in ["ROE", "净利率", "毛利率", "负债率", "周转率", "增长率", "每股"]):
                        try:
                            md += f"- {col}: {float(val):.2f}\n"
                        except (ValueError, TypeError):
                            md += f"- {col}: {val}\n"
    except Exception as e:
        md += f"获取失败: {e}\n"
    return md + "\n"


def build_valuation_section(code: str) -> str:
    """估值"""
    md = "## 💰 四、估值分析\n\n"
    try:
        import akshare as ak
        spot = ak.stock_zh_a_spot_em()
        target = spot[spot["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return md + "无数据\n\n"
        row = target.iloc[0]
        pe = float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else 0
        pb = float(row.get("市净率", 0)) if row.get("市净率") else 0
        ps = float(row.get("市销率", 0)) if row.get("市销率") else 0

        md += f"- **PE(TTM)**: {pe:.2f}\n"
        md += f"- **PB**: {pb:.2f}\n"
        md += f"- **PS(TTM)**: {ps:.2f}\n\n"

        if pe < 0:
            rating = "亏损"
        elif pe < 15:
            rating = "严重低估"
        elif pe < 25:
            rating = "低估"
        elif pe < 40:
            rating = "合理"
        elif pe < 60:
            rating = "合理偏高"
        else:
            rating = "高估"
        md += f"**估值评级**: {rating}\n\n"
    except Exception as e:
        md += f"获取失败: {e}\n"
    return md + "\n"


def build_capital_section(code: str) -> str:
    """资金面"""
    md = "## 💸 五、资金面分析\n\n"
    try:
        import akshare as ak
        market = "sh" if str(code).startswith(("60", "68", "9")) else "sz"
        df = ak.stock_individual_fund_flow(stock=str(code).zfill(6), market=market)
        if df.empty:
            return md + "无数据\n\n"
        md += "**最近 5 日资金流**:\n\n"
        md += "| 日期 | 主力净流入 | 涨跌幅 |\n"
        md += "|------|------------|--------|\n"
        for _, row in df.head(5).iterrows():
            date = str(row.get("日期", ""))[:10]
            main_net = float(row.get("主力净流入-净额", 0)) if row.get("主力净流入-净额") else 0
            pct = float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0
            md += f"| {date} | {main_net/1e8:+.2f}亿 | {pct:+.2f}% |\n"
        md += "\n"
    except Exception as e:
        md += f"获取失败: {e}\n"
    return md + "\n"


def build_sentiment_section(code: str) -> str:
    """舆情"""
    md = "## 📰 六、舆情分析\n\n"
    try:
        import akshare as ak
        news = ak.stock_news_em(symbol=code)
        if news.empty:
            return md + "无新闻数据\n\n"
        md += f"**最近 {min(10, len(news))} 条新闻**:\n\n"
        for _, row in news.head(10).iterrows():
            title = str(row.get("新闻标题", ""))
            date = str(row.get("发布时间", ""))[:10]
            md += f"- [{date}] {title}\n"
        md += "\n"
    except Exception as e:
        md += f"获取失败: {e}\n"
    return md + "\n"


def build_advice_section(code: str) -> str:
    """投资建议"""
    md = "## 🎯 七、投资建议\n\n"
    md += "**综合评分**:\n\n"
    md += "- 技术面: 详见第二部分\n"
    md += "- 基本面: 详见第三部分\n"
    md += "- 估值: 详见第四部分\n"
    md += "- 资金: 详见第五部分\n"
    md += "- 舆情: 详见第六部分\n\n"
    md += "**操作建议**:\n\n"
    md += "- 综合判断需要结合多个维度, 不可仅凭单一指标\n"
    md += "- 建议同时关注大盘环境, 顺势而为\n"
    md += "- 设置止损位 (5%-8%)\n"
    md += "- 控制单只股票仓位 (建议 < 20%)\n\n"
    md += "⚠️ **免责声明**: 本报告由程序自动生成, 仅供研究参考, 不构成投资建议\n"
    return md + "\n"


def generate_research(code: str, save: bool = False, save_path: Optional[str] = None) -> str:
    """生成个股研报"""
    md = f"# 🔬 个股深度研究报告: {code}\n\n"
    md += f"**生成日期**: {datetime.now().strftime('%Y-%m-%d')}\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"

    sections = [
        build_company_section,
        build_technical_section,
        build_fundamental_section,
        build_valuation_section,
        build_capital_section,
        build_sentiment_section,
        build_advice_section,
    ]
    for builder in sections:
        try:
            md += builder(code)
        except Exception as e:
            md += f"## 错误: {e}\n\n"

    if save:
        if save_path is None:
            save_path = f"research_{code}_{datetime.now().strftime('%Y%m%d')}.md"
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(md)
            md += f"\n---\n\n报告已保存: `{save_path}`\n"
        except Exception as e:
            md += f"\n保存失败: {e}\n"

    return md


def main():
    parser = argparse.ArgumentParser(description="stock-research-report")
    parser.add_argument("code")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--path")
    args = parser.parse_args()

    if not args.code:
        parser.print_help()
        return

    report = generate_research(args.code, save=args.save, save_path=args.path)
    print(report)


if __name__ == "__main__":
    main()
