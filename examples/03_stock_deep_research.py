"""
example_03_stock_deep_research.py - 个股深度研究示例
=====================================================

运行: python examples/03_stock_deep_research.py

功能: 对单只股票做多维度深度分析
"""

import sys
sys.path.insert(0, ".")

from skills.02-data-collection.stock-basic-info.stock_basic_info import (
    get_stock_realtime, get_stock_info
)
from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
from skills.04-stock-analysis.stock-fundamental-analysis.stock_fundamental_analysis import full_fundamental_analysis
from skills.02-data-collection.stock-news-collector.stock_news_collector import get_stock_news, summarize_sentiment
from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis import get_stock_fund_flow


def deep_research(code: str):
    """对单只股票做深度研究"""
    print("=" * 60)
    print(f"🔬  个股深度研究: {code}")
    print("=" * 60)

    # 1. 基础信息
    print(f"\n【1】基础信息")
    rt = get_stock_realtime(code)
    info = get_stock_info(code)
    if rt:
        print(f"  名称: {rt.get('name', '')}")
        print(f"  现价: {rt.get('price', 0):.2f} ({rt.get('pct_change', 0):+.2f}%)")
        print(f"  PE: {rt.get('pe', 'N/A')}, PB: {rt.get('pb', 'N/A')}")
        print(f"  总市值: {rt.get('total_mv', 0)/1e8:.2f}亿")

    # 2. 技术面
    print(f"\n【2】技术面")
    tech = full_technical_analysis(code)
    if tech:
        print(f"  趋势: {tech['trend']['trend']} (评分: {tech['trend']['score']})")
        print(f"  信号: {tech['trading_signal']['signal']} ({tech['trading_signal']['strength']})")
        print(f"  超买超卖: {tech['overbought_oversold']['level']}")
        print(f"  关键信号:")
        for s in tech['trend']['signals'][:5]:
            print(f"    - {s['name']}: {s['desc']}")

    # 3. 基本面
    print(f"\n【3】基本面")
    fund = full_fundamental_analysis(code)
    if fund:
        print(f"  综合评分: {fund['score']} ({fund['rating']})")
        print(f"  财务健康: {fund['health'].get('level', 'N/A')}")
        if fund['health'].get('issues'):
            print(f"  关注点:")
            for issue in fund['health']['issues']:
                print(f"    - {issue}")

    # 4. 资金面
    print(f"\n【4】资金面 (近5日)")
    flow = get_stock_fund_flow(code, days=5)
    if not flow.empty:
        print(f"  数据条数: {len(flow)}")

    # 5. 舆情
    print(f"\n【5】舆情")
    news = get_stock_news(code, max_count=20)
    sent = summarize_sentiment(news)
    print(f"  情绪: {sent.get('label', 'N/A')} (分数: {sent.get('score', 0)})")
    print(f"  利好: {sent.get('positive', 0)} 条, 利空: {sent.get('negative', 0)} 条")

    # 6. 综合建议
    print(f"\n【6】综合建议")
    tech_signal = tech.get('trading_signal', {}).get('signal', '观望')
    fund_rating = fund.get('rating', '中')
    sent_label = sent.get('label', 'neutral')

    if tech_signal == "买入" and fund_rating in ("优", "良"):
        if sent_label in ("positive", "very_positive"):
            advice = "✅ 积极配置"
        else:
            advice = "👍 逢低关注"
    elif tech_signal == "卖出":
        advice = "❌ 建议回避"
    else:
        advice = "⚠️  观望为主"
    print(f"  {advice}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 分析平安银行
    deep_research("000001")
