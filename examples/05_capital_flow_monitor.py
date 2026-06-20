"""
example_05_capital_flow_monitor.py - 资金流监控
================================================

运行: python examples/05_capital_flow_monitor.py

功能: 监控大盘资金流和北向资金动向
"""

import sys
sys.path.insert(0, ".")

from skills.03-market-analysis.capital-flow-analysis.capital_flow_analysis import (
    get_market_fund_flow, get_north_bound_today, get_north_bound_flow
)


def main():
    print("=" * 60)
    print("💰  资金流向监控")
    print("=" * 60)

    # 1. 大盘资金流
    print(f"\n【1】大盘资金流 (主力/超大单/大单/中单/小单)")
    mf = get_market_fund_flow()
    for market, data in mf.items():
        print(f"\n  【{market}】")
        main_net = data.get("main_net", data.get("主力净流入-净额", 0))
        if main_net is not None:
            try:
                print(f"    主力净流入: {float(main_net)/1e8:+.2f}亿")
            except:
                pass
        for k, v in data.items():
            if "净流入" in str(k) and "净占比" not in str(k):
                try:
                    val = float(v)
                    if val != 0:
                        print(f"    {k}: {val/1e8:+.2f}亿")
                except:
                    pass

    # 2. 北向资金今日
    print(f"\n【2】北向资金今日")
    nb = get_north_bound_today()
    if nb:
        for k, v in nb.items():
            if v is not None and pd.notna(v) if 'pd' in dir() else v is not None:
                print(f"  {k}: {v}")

    # 3. 北向资金近10日
    print(f"\n【3】北向资金近10日")
    nb_hist = get_north_bound_flow(days=10)
    if not nb_hist.empty:
        print(nb_hist.head(10).to_string())


if __name__ == "__main__":
    import pandas as pd
    main()
