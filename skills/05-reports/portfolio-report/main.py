#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""portfolio-report: 持仓报告"""

import os
import sys
import json
import argparse
import pandas as pd
from typing import Dict, List
from datetime import datetime


DEFAULT_CONFIG_PATHS = [
    "./portfolio.yaml", "./portfolio.yml", "./portfolio.json",
    "~/.astock_skills/portfolio.yaml",
]


def load_portfolio(path: str = None) -> Dict:
    """加载持仓"""
    if not path:
        for p in DEFAULT_CONFIG_PATHS:
            p = os.path.expanduser(p)
            if os.path.exists(p):
                path = p
                break
    if not path or not os.path.exists(path):
        return {"positions": [], "name": "默认"}
    try:
        if path.endswith((".yaml", ".yml")):
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载失败: {e}", file=sys.stderr)
        return {}


def save_portfolio_template(path: str = "./portfolio.yaml"):
    """生成模板"""
    template = """# A股持仓配置
name: 我的持仓
initial_capital: 100000  # 初始资金 (可选)
benchmark: "000300"      # 对标基准 (沪深300)

positions:
  - code: "000001"
    name: "平安银行"
    cost: 12.50
    shares: 1000
  - code: "600519"
    name: "贵州茅台"
    cost: 1650.00
    shares: 100
  - code: "300750"
    name: "宁德时代"
    cost: 220.00
    shares: 500
  - code: "000858"
    name: "五粮液"
    cost: 145.00
    shares: 200
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"持仓模板已生成: {path}")


def get_quote(code: str) -> Dict:
    """获取实时行情"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return {}
        row = target.iloc[0]
        return {
            "name": row.get("名称", ""),
            "price": float(row.get("最新价", 0)),
            "pct_change": float(row.get("涨跌幅", 0)),
            "industry": row.get("所属行业", ""),
        }
    except Exception:
        return {}


# ============================================================
# 核心计算
# ============================================================
def calc_positions(portfolio: Dict) -> List[Dict]:
    """计算持仓"""
    result = []
    for pos in portfolio.get("positions", []):
        code = pos.get("code", "")
        if not code:
            continue
        quote = get_quote(code)
        cost = float(pos.get("cost", 0))
        shares = int(pos.get("shares", 0))
        current_price = quote.get("price", 0)
        market_value = current_price * shares
        cost_value = cost * shares
        profit = market_value - cost_value
        profit_pct = (profit / cost_value * 100) if cost_value else 0
        result.append({
            "code": code,
            "name": pos.get("name") or quote.get("name", ""),
            "cost": cost,
            "shares": shares,
            "cost_value": cost_value,
            "current_price": current_price,
            "market_value": market_value,
            "profit": profit,
            "profit_pct": profit_pct,
            "pct_change_today": quote.get("pct_change", 0),
            "industry": quote.get("industry", ""),
        })
    return result


def calc_summary(positions: List[Dict]) -> Dict:
    """汇总"""
    if not positions:
        return {}
    total_mv = sum(p["market_value"] for p in positions)
    total_cost = sum(p["cost_value"] for p in positions)
    total_profit = total_mv - total_cost
    profit_pct = (total_profit / total_cost * 100) if total_cost else 0
    return {
        "total_mv": total_mv,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "profit_pct": profit_pct,
        "position_count": len(positions),
        "win_count": sum(1 for p in positions if p["profit"] > 0),
        "loss_count": sum(1 for p in positions if p["profit"] < 0),
    }


def analyze_sector_distribution(positions: List[Dict]) -> Dict:
    """行业分布"""
    total_mv = sum(p["market_value"] for p in positions)
    sector_map = {}
    for p in positions:
        sector = p.get("industry") or "未知"
        if sector not in sector_map:
            sector_map[sector] = {"value": 0, "count": 0}
        sector_map[sector]["value"] += p["market_value"]
        sector_map[sector]["count"] += 1
    # 计算占比
    for sector, data in sector_map.items():
        data["pct"] = data["value"] / total_mv * 100 if total_mv else 0
    # 排序
    return dict(sorted(sector_map.items(), key=lambda x: x[1]["value"], reverse=True))


def analyze_risk(positions: List[Dict]) -> Dict:
    """风险分析"""
    total_mv = sum(p["market_value"] for p in positions)
    if not total_mv or not positions:
        return {}
    # 集中度
    max_pos = max(positions, key=lambda p: p["market_value"])
    max_pct = max_pos["market_value"] / total_mv * 100
    # 最大亏损
    max_loss = min(positions, key=lambda p: p["profit_pct"])
    # 平均盈利
    avg_profit = sum(p["profit_pct"] for p in positions) / len(positions)
    return {
        "max_position_pct": round(max_pct, 2),
        "max_position": f"{max_loss.get('code', '')} {max_loss.get('name', '')}",
        "max_loss_pct": round(max_loss["profit_pct"], 2),
        "avg_profit_pct": round(avg_profit, 2),
        "concentration_risk": "高" if max_pct > 30 else "中" if max_pct > 20 else "低",
    }


def generate_advice(positions: List[Dict], risk: Dict) -> List[str]:
    """调仓建议"""
    advice = []
    if not risk:
        return advice
    # 集中度
    if risk["max_position_pct"] > 30:
        advice.append(f"⚠️ 单股仓位过重 ({risk['max_position_pct']:.1f}%), 建议减仓分散风险")
    # 行业集中度
    sector_dist = analyze_sector_distribution(positions)
    if sector_dist:
        top_sector, top_data = next(iter(sector_dist.items()))
        if top_data["pct"] > 50:
            advice.append(f"⚠️ 行业集中度过高 ({top_sector} 占 {top_data['pct']:.1f}%), 建议跨行业配置")
    # 个股亏损
    if risk["max_loss_pct"] < -20:
        advice.append(f"⚠️ {risk['max_position']} 亏损 {risk['max_loss_pct']:.1f}%, 评估基本面")
    elif risk["max_loss_pct"] < -10:
        advice.append(f"⚠️ {risk['max_position']} 亏损较大, 关注止盈止损")
    # 持仓数量
    if len(positions) > 15:
        advice.append("💡 持仓数量过多 (>15), 难以深入跟踪, 建议精简")
    elif len(positions) < 3:
        advice.append("💡 持仓数量较少 (<3), 集中度风险较高")
    if not advice:
        advice.append("✅ 持仓结构合理, 继续保持")
    return advice


# ============================================================
# 报告生成
# ============================================================
def generate_report(config_path: str = None, save: bool = False) -> str:
    """生成报告"""
    portfolio = load_portfolio(config_path)
    positions = calc_positions(portfolio)
    if not positions:
        return "持仓为空, 请检查配置文件"

    summary = calc_summary(positions)
    sector_dist = analyze_sector_distribution(positions)
    risk = analyze_risk(positions)
    advice = generate_advice(positions, risk)

    md = f"# 📊 持仓报告 - {portfolio.get('name', '我的持仓')}\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"

    # 总览
    md += "## 💰 一、总览\n\n"
    md += f"- **总市值**: {summary['total_mv']:,.0f} 元\n"
    md += f"- **总成本**: {summary['total_cost']:,.0f} 元\n"
    md += f"- **总盈亏**: **{summary['total_profit']:+,.0f}** 元 ({summary['profit_pct']:+.2f}%)\n"
    md += f"- **持仓数量**: {summary['position_count']} 只\n"
    md += f"- **盈利/亏损**: {summary['win_count']}/{summary['loss_count']}\n\n"

    # 盈亏明细
    md += "## 💵 二、盈亏明细\n\n"
    md += "| 代码 | 名称 | 成本 | 现价 | 持仓 | 市值 | 盈亏 | 收益率 | 今日 |\n"
    md += "|------|------|------|------|------|------|------|--------|------|\n"
    for p in sorted(positions, key=lambda x: x["profit_pct"], reverse=True):
        md += f"| {p['code']} | {p['name']} | {p['cost']:.2f} | {p['current_price']:.2f} | "
        md += f"{p['shares']} | {p['market_value']:,.0f} | "
        md += f"**{p['profit']:+,.0f}** | **{p['profit_pct']:+.2f}%** | "
        md += f"{p['pct_change_today']:+.2f}% |\n"
    md += "\n"

    # 行业分布
    md += "## 🏭 三、行业分布\n\n"
    md += "| 行业 | 持仓数 | 市值 | 占比 |\n"
    md += "|------|--------|------|------|\n"
    for sector, data in sector_dist.items():
        md += f"| {sector} | {data['count']} | {data['value']:,.0f} | {data['pct']:.2f}% |\n"
    md += "\n"

    # 风险敞口
    md += "## ⚠️ 四、风险敞口\n\n"
    md += f"- **最大单股仓位**: {risk['max_position_pct']:.2f}% ({risk['max_position']})\n"
    md += f"- **最大亏损个股**: {risk['max_position']} ({risk['max_loss_pct']:+.2f}%)\n"
    md += f"- **平均收益率**: {risk['avg_profit_pct']:+.2f}%\n"
    md += f"- **集中度风险**: {risk['concentration_risk']}\n\n"

    # 调仓建议
    md += "## 🎯 五、调仓建议\n\n"
    for a in advice:
        md += f"- {a}\n"
    md += "\n"

    md += "---\n\n"
    md += "⚠️ 本报告基于实时行情自动生成, 仅供研究参考, 不构成投资建议。\n"

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
    parser = argparse.ArgumentParser(description="portfolio-report")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("report", help="完整报告")
    p.add_argument("--config")
    p.add_argument("--save", action="store_true")
    p = sub.add_parser("pnl", help="盈亏")
    p.add_argument("--config")
    p = sub.add_parser("sectors", help="行业分布")
    p.add_argument("--config")
    p = sub.add_parser("advice", help="调仓建议")
    p.add_argument("--config")
    p = sub.add_parser("init", help="初始化模板")
    p.add_argument("--path", default="./portfolio.yaml")
    args = parser.parse_args()

    if args.cmd == "init":
        save_portfolio_template(args.path)
        return

    portfolio = load_portfolio(args.config if hasattr(args, "config") else None)
    positions = calc_positions(portfolio)

    if args.cmd == "report":
        print(generate_report(args.config, args.save))
    elif args.cmd == "pnl":
        s = calc_summary(positions)
        if s:
            print(f"总市值: {s['total_mv']:,.0f} 元")
            print(f"总成本: {s['total_cost']:,.0f} 元")
            print(f"总盈亏: {s['total_profit']:+,.0f} 元 ({s['profit_pct']:+.2f}%)")
            for p in positions:
                print(f"  {p['code']} {p['name']}: {p['profit_pct']:+.2f}% ({p['profit']:+,.0f}元)")
    elif args.cmd == "sectors":
        d = analyze_sector_distribution(positions)
        for sector, data in d.items():
            print(f"  {sector}: {data['pct']:.2f}% ({data['count']}只)")
    elif args.cmd == "advice":
        risk = analyze_risk(positions)
        for a in generate_advice(positions, risk):
            print(f"  {a}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
