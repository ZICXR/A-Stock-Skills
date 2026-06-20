"""
capital-flow-analysis: 资金流向分析
====================================

功能:
    - 大盘资金流 (主力/超大单/大单/中单/小单)
    - 北向资金 (沪股通/深股通)
    - 两融余额
    - 个股资金流
    - 资金信号识别
"""

import logging
import pandas as pd
from typing import Dict, List, Optional

import sys
sys.path.insert(0, "skills/01-infra")
from astock_utils.astock_utils import normalize_stock_code

logger = logging.getLogger(__name__)


# ============================================================
# 1. 大盘资金流
# ============================================================
def get_market_fund_flow() -> Dict:
    """获取大盘整体资金流
    Returns:
        {
            "shanghai": {...},
            "shenzhen": {...},
            "total": {...}
        }
    """
    result = {}
    try:
        import akshare as ak
        df = ak.stock_market_fund_flow()
    except Exception as e:
        logger.error(f"akshare 获取大盘资金流失败: {e}")
        return result

    if df.empty:
        return result

    rename_map = {
        "日期": "date", "主力净流入-净额": "main_net",
        "主力净流入-净占比": "main_ratio", "超大单净流入-净额": "super_net",
        "超大单净流入-净占比": "super_ratio", "大单净流入-净额": "big_net",
        "大单净流入-净占比": "big_ratio", "中单净流入-净额": "mid_net",
        "中单净流入-净占比": "mid_ratio", "小单净流入-净额": "small_net",
        "小单净流入-净占比": "small_ratio"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "市场" in df.columns:
        for market in df["市场"].unique():
            sub = df[df["市场"] == market]
            if not sub.empty:
                result[market] = sub.iloc[-1].to_dict()

    return result


# ============================================================
# 2. 北向资金
# ============================================================
def get_north_bound_flow(days: int = 30) -> pd.DataFrame:
    """北向资金历史
    Args:
        days: 天数
    """
    try:
        import akshare as ak
        df = ak.stock_hsgt_fund_flow_summary_em()
    except Exception as e:
        logger.error(f"akshare 获取北向资金失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {
        "日期": "date", "资金净流入": "net_inflow",
        "沪股通": "sh_connect", "深股通": "sz_connect",
        "成交总额": "total_amount",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date", ascending=False).head(days).reset_index(drop=True)

    return df


def get_north_bound_today() -> Dict:
    """北向资金今日实时"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_north_net_flow_in_em()
    except Exception as e:
        logger.error(f"akshare 获取北向实时失败: {e}")
        return {}

    if df.empty:
        return {}

    return df.iloc[-1].to_dict()


# ============================================================
# 3. 个股资金流
# ============================================================
def get_stock_fund_flow(symbol: str, days: int = 10) -> pd.DataFrame:
    """个股资金流
    Args:
        symbol: 6位股票代码
        days: 天数
    """
    try:
        import akshare as ak
        # 个股资金流 (东方财富)
        market = "sh" if symbol.startswith(("60", "68", "9")) else "sz"
        df = ak.stock_individual_fund_flow(stock=symbol, market=market)
    except Exception as e:
        logger.error(f"akshare 获取个股资金流失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    if "日期" in df.columns:
        df = df.sort_values("日期", ascending=False).head(days).reset_index(drop=True)
    return df


# ============================================================
# 4. 资金信号识别
# ============================================================
def analyze_fund_signal(flow_df: pd.DataFrame) -> Dict:
    """根据资金数据生成信号"""
    if flow_df.empty:
        return {"signal": "unknown"}

    last = flow_df.iloc[-1]
    main_net = last.get("main_net", 0) or last.get("主力净流入-净额", 0)
    super_net = last.get("super_net", 0) or last.get("超大单净流入-净额", 0)

    if main_net > 0 and super_net > 0:
        signal = "主力大幅流入"
        score = 2
    elif main_net > 0:
        signal = "主力净流入"
        score = 1
    elif main_net < 0 and super_net < 0:
        signal = "主力大幅流出"
        score = -2
    elif main_net < 0:
        signal = "主力净流出"
        score = -1
    else:
        signal = "持平"
        score = 0

    return {
        "signal": signal,
        "score": score,
        "main_net": float(main_net) if main_net else 0,
    }


# ============================================================
# 5. 资金流综合分析
# ============================================================
def full_capital_analysis(symbol: Optional[str] = None) -> Dict:
    """综合资金分析
    Args:
        symbol: 个股代码, None=大盘
    """
    result = {
        "market_flow": get_market_fund_flow(),
        "north_bound": {
            "today": get_north_bound_today(),
            "history": get_north_bound_flow(days=10).to_dict("records") if not get_north_bound_flow(days=10).empty else [],
        }
    }

    if symbol:
        result["stock_flow"] = get_stock_fund_flow(symbol, days=10)
        if not result["stock_flow"].empty:
            result["stock_signal"] = analyze_fund_signal(result["stock_flow"])

    return result


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 大盘资金流 ===")
    mf = get_market_fund_flow()
    for market, data in mf.items():
        print(f"\n{market}:")
        for k, v in data.items():
            print(f"  {k}: {v}")

    print("\n=== 北向资金 (近10日) ===")
    df = get_north_bound_flow(days=10)
    if not df.empty:
        print(df.head(10).to_string())

    print("\n=== 个股资金流: 000001 ===")
    df = get_stock_fund_flow("000001", days=5)
    if not df.empty:
        print(df.to_string())
