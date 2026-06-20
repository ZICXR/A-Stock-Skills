"""
example_04_sector_rotation.py - 板块轮动分析
=============================================

运行: python examples/04_sector_rotation.py

功能: 找出当前主线板块, 追踪资金流向
"""

import sys
sys.path.insert(0, ".")

from skills.03-market-analysis.sector-analysis.sector_analysis import (
    identify_main_themes, top_fund_inflow, top_fund_outflow, detect_rotation_signal
)
from skills.02-data-collection.sector-data-collector.sector_data_collector import (
    get_industry_sectors, get_concept_sectors
)


def main():
    print("=" * 60)
    print("🔥  板块轮动分析")
    print("=" * 60)

    # 1. 主线板块
    print(f"\n【1】主线板块 Top 5")
    themes = identify_main_themes(top_n=5)
    for i, t in enumerate(themes.get("main_themes", [])[:5], 1):
        print(f"  {i}. [{t['type']}] {t['name']}")
        print(f"     涨幅: {t.get('pct_change', 0):+.2f}%")
        print(f"     资金: {t.get('main_net', 0)/1e8:+.2f}亿")
        print(f"     龙头: {t.get('leader', 'N/A')}")

    # 2. 资金流入榜
    print(f"\n【2】今日资金流入 Top 5")
    inflow = top_fund_inflow("今日", "industry", top_n=5)
    if not inflow.empty:
        sort_col = "main_net" if "main_net" in inflow.columns else None
        if sort_col:
            for _, row in inflow.iterrows():
                print(f"  {row.get('name', '')}: "
                      f"涨幅{row.get('pct_change', 0):+.2f}%, "
                      f"资金{row.get(sort_col, 0)/1e8:+.2f}亿")

    # 3. 资金流出榜
    print(f"\n【3】今日资金流出 Top 5")
    outflow = top_fund_outflow("今日", "industry", top_n=5)
    if not outflow.empty:
        sort_col = "main_net" if "main_net" in outflow.columns else None
        if sort_col:
            for _, row in outflow.iterrows():
                print(f"  {row.get('name', '')}: "
                      f"涨幅{row.get('pct_change', 0):+.2f}%, "
                      f"资金{row.get(sort_col, 0)/1e8:+.2f}亿")

    # 4. 3日资金流入 (判断持续性)
    print(f"\n【4】3日资金流入 Top 5 (持续性)")
    flow_3d = top_fund_inflow("3日", "industry", top_n=5)
    if not flow_3d.empty:
        for _, row in flow_3d.iterrows():
            print(f"  {row.get('name', '')}: "
                  f"3日资金{row.get('main_net', 0)/1e8:+.2f}亿")

    # 5. 轮动信号
    print(f"\n【5】市场轮动信号")
    industry_df = get_industry_sectors()
    if not industry_df.empty:
        signal = detect_rotation_signal(industry_df)
        print(f"  信号: {signal.get('signal', 'N/A')}")
        print(f"  说明: {signal.get('desc', 'N/A')}")
        print(f"  上涨比例: {signal.get('up_ratio', 0)}%")


if __name__ == "__main__":
    main()
