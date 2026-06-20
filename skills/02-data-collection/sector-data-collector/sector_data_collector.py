"""
sector-data-collector: 板块数据采集
====================================

功能:
    - 行业板块行情
    - 概念板块行情
    - 板块资金流
    - 板块成分股
"""

import logging
import pandas as pd
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


# ============================================================
# 1. 行业板块
# ============================================================
def get_industry_sectors() -> pd.DataFrame:
    """行业板块行情"""
    try:
        import akshare as ak
        df = ak.stock_board_industry_name_em()
    except Exception as e:
        logger.error(f"获取行业板块失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {"板块名称": "name", "板块代码": "code", "最新价": "price",
                  "涨跌幅": "pct_change", "涨跌额": "change",
                  "总市值": "total_mv", "流通市值": "circ_mv",
                  "换手率": "turnover", "上涨家数": "up_count",
                  "下跌家数": "down_count", "领涨股": "leader",
                  "领涨股涨跌幅": "leader_pct"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


# ============================================================
# 2. 概念板块
# ============================================================
def get_concept_sectors() -> pd.DataFrame:
    """概念板块行情"""
    try:
        import akshare as ak
        df = ak.stock_board_concept_name_em()
    except Exception as e:
        logger.error(f"获取概念板块失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {"板块名称": "name", "板块代码": "code", "最新价": "price",
                  "涨跌幅": "pct_change", "涨跌额": "change",
                  "总市值": "total_mv", "流通市值": "circ_mv",
                  "换手率": "turnover", "上涨家数": "up_count",
                  "下跌家数": "down_count", "领涨股": "leader",
                  "领涨股涨跌幅": "leader_pct"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


# ============================================================
# 3. 板块资金流
# ============================================================
def get_sector_fund_flow(period: str = "今日") -> pd.DataFrame:
    """行业板块资金流
    Args:
        period: 今日/3日/5日/10日
    """
    try:
        import akshare as ak
        df = ak.stock_sector_fund_flow_rank(indicator=period)
    except Exception as e:
        logger.error(f"获取板块资金流失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {"名称": "name", "今日涨跌幅": "pct_change",
                  "主力净流入-净额": "main_net", "主力净流入-净占比": "main_ratio",
                  "超大单净流入-净额": "super_net", "大单净流入-净额": "big_net",
                  "中单净流入-净额": "mid_net", "小单净流入-净额": "small_net"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


def get_concept_fund_flow(period: str = "今日") -> pd.DataFrame:
    """概念板块资金流"""
    try:
        import akshare as ak
        df = ak.stock_concept_fund_flow_rank(indicator=period)
    except Exception as e:
        logger.error(f"获取概念资金流失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {"名称": "name", "今日涨跌幅": "pct_change",
                  "主力净流入-净额": "main_net", "主力净流入-净占比": "main_ratio"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


# ============================================================
# 4. 板块成分股
# ============================================================
def get_sector_stocks(sector_code: str, sector_type: str = "industry") -> pd.DataFrame:
    """获取板块成分股
    Args:
        sector_code: 板块代码
        sector_type: industry / concept
    """
    try:
        import akshare as ak
        if sector_type == "industry":
            df = ak.stock_board_industry_cons_em(symbol=sector_code)
        else:
            df = ak.stock_board_concept_cons_em(symbol=sector_code)
    except Exception as e:
        logger.error(f"获取成分股失败: {e}")
        return pd.DataFrame()

    return df


# ============================================================
# 5. 板块强度排序
# ============================================================
def rank_sectors_by_strength(sector_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """按综合强度排序
    强度 = 涨跌幅 * 0.5 + 资金净流入占比 * 0.3 + (上涨家数-下跌家数)/成分数 * 0.2
    """
    if sector_df.empty:
        return sector_df

    df = sector_df.copy()
    # 确保有涨跌幅和资金流列
    if "pct_change" in df.columns:
        df["score"] = df["pct_change"] * 0.5
    else:
        df["score"] = 0

    if "main_ratio" in df.columns:
        df["score"] = df["score"] + df["main_ratio"].fillna(0) * 0.3

    if "up_count" in df.columns and "down_count" in df.columns:
        total = df["up_count"] + df["down_count"]
        df["up_ratio"] = (df["up_count"] / total.replace(0, 1)) * 100
        df["score"] = df["score"] + (df["up_ratio"] - 50) * 0.04

    return df.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)


# ============================================================
# 6. 板块轮动识别
# ============================================================
def detect_sector_rotation(historical_data: List[pd.DataFrame]) -> Dict:
    """检测板块轮动
    Args:
        historical_data: 多个时间点的板块数据列表
    """
    if not historical_data or len(historical_data) < 2:
        return {"rotating": False, "info": "数据不足"}

    # 取首尾对比
    first = historical_data[0]
    last = historical_data[-1]

    if "name" not in first.columns or "name" not in last.columns:
        return {"rotating": False, "info": "数据格式错误"}

    merged = first.merge(last, on="name", suffixes=("_prev", "_curr"))
    if "pct_change_prev" not in merged.columns or "pct_change_curr" not in merged.columns:
        return {"rotating": False, "info": "缺数据"}

    merged["change"] = merged["pct_change_curr"] - merged["pct_change_prev"]
    return {
        "rotating": True,
        "improved": merged.nlargest(5, "change")[["name", "change"]].to_dict("records"),
        "deteriorated": merged.nsmallest(5, "change")[["name", "change"]].to_dict("records"),
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 行业板块 Top 10 ===")
    df = get_industry_sectors()
    if not df.empty:
        cols = [c for c in ["name", "pct_change", "leader", "leader_pct", "up_count", "down_count"] if c in df.columns]
        print(df.nlargest(10, "pct_change")[cols].to_string())

    print("\n=== 概念板块 Top 10 ===")
    df = get_concept_sectors()
    if not df.empty:
        cols = [c for c in ["name", "pct_change", "leader", "leader_pct"] if c in df.columns]
        print(df.nlargest(10, "pct_change")[cols].to_string())

    print("\n=== 行业资金流入 Top 10 ===")
    ff = get_sector_fund_flow()
    if not ff.empty:
        sort_col = "main_net" if "main_net" in ff.columns else "主力净流入-净额"
        if sort_col in ff.columns:
            cols = [c for c in ["name", "pct_change", "main_net", "main_ratio"] if c in ff.columns]
            print(ff.nlargest(10, sort_col)[cols].to_string())
