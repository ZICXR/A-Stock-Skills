"""
sector-analysis: 板块轮动分析
================================

功能:
    - 板块涨跌幅排名
    - 板块资金流入榜
    - 板块强度评分
    - 板块轮动信号
    - 主线板块识别
"""

import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

import sys
sys.path.insert(0, "skills/02-data-collection/sector-data-collector")
from sector_data_collector import (
    get_industry_sectors, get_concept_sectors,
    get_sector_fund_flow, get_concept_fund_flow
)

logger = logging.getLogger(__name__)


# ============================================================
# 1. 板块综合排名
# ============================================================
def rank_sectors(sector_type: str = "industry", top_n: int = 20) -> pd.DataFrame:
    """板块综合排名
    Args:
        sector_type: industry / concept
        top_n: 返回前N名
    """
    if sector_type == "industry":
        df = get_industry_sectors()
    else:
        df = get_concept_sectors()

    if df.empty or "pct_change" not in df.columns:
        return df

    return df.sort_values("pct_change", ascending=False).head(top_n).reset_index(drop=True)


# ============================================================
# 2. 板块资金流榜
# ============================================================
def top_fund_inflow(period: str = "今日", sector_type: str = "industry", top_n: int = 10) -> pd.DataFrame:
    """资金流入榜
    Args:
        period: 今日/3日/5日/10日
        sector_type: industry / concept
    """
    if sector_type == "industry":
        df = get_sector_fund_flow(period)
    else:
        df = get_concept_fund_flow(period)

    if df.empty:
        return df

    sort_col = "main_net" if "main_net" in df.columns else None
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=False).head(top_n)

    return df.reset_index(drop=True)


def top_fund_outflow(period: str = "今日", sector_type: str = "industry", top_n: int = 10) -> pd.DataFrame:
    """资金流出榜"""
    if sector_type == "industry":
        df = get_sector_fund_flow(period)
    else:
        df = get_concept_fund_flow(period)

    if df.empty:
        return df

    sort_col = "main_net" if "main_net" in df.columns else None
    if sort_col and sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=True).head(top_n)

    return df.reset_index(drop=True)


# ============================================================
# 3. 板块强度评分
# ============================================================
def calc_sector_score(sector_df: pd.DataFrame, flow_df: pd.DataFrame) -> pd.DataFrame:
    """计算板块综合强度评分
    评分维度:
        - 涨跌幅 (40%)
        - 资金净流入 (40%)
        - 上涨家数占比 (20%)
    """
    if sector_df.empty or flow_df.empty:
        return sector_df

    # 合并
    df = sector_df.merge(flow_df[["name", "main_net"]], on="name", how="left")
    if df.empty:
        return sector_df

    # 归一化
    max_change = df["pct_change"].abs().max() if "pct_change" in df.columns else 1
    df["score_change"] = df["pct_change"] / max_change * 40 if "pct_change" in df.columns else 0

    max_flow = df["main_net"].abs().max() if "main_net" in df.columns else 1
    df["score_flow"] = df["main_net"] / max_flow * 40 if "main_net" in df.columns else 0

    if "up_count" in df.columns and "down_count" in df.columns:
        total = df["up_count"] + df["down_count"]
        df["up_ratio"] = df["up_count"] / total.replace(0, 1)
        df["score_up"] = (df["up_ratio"] - 0.5) * 40  # 0.5为中性
    else:
        df["score_up"] = 0

    df["total_score"] = df["score_change"] + df["score_flow"] + df["score_up"]
    return df.sort_values("total_score", ascending=False).reset_index(drop=True)


# ============================================================
# 4. 板块轮动信号
# ============================================================
def detect_rotation_signal(industry_df: pd.DataFrame) -> Dict:
    """检测板块轮动信号
    信号类型:
        - 普涨: 80%以上板块上涨
        - 普跌: 80%以上板块下跌
        - 剧烈分化: 涨跌家数比差异大
        - 资金切换: 流入榜与流出榜分布
    """
    if industry_df.empty or "pct_change" not in industry_df.columns:
        return {"signal": "unknown", "info": "数据不足"}

    up = (industry_df["pct_change"] > 0).sum()
    down = (industry_df["pct_change"] < 0).sum()
    total = len(industry_df)
    up_ratio = up / total if total else 0

    info = {
        "up": int(up),
        "down": int(down),
        "total": int(total),
        "up_ratio": round(up_ratio * 100, 2),
    }

    if up_ratio > 0.8:
        info["signal"] = "普涨"
        info["desc"] = "市场普涨, 风险偏好高, 注意后续分化"
    elif up_ratio < 0.2:
        info["signal"] = "普跌"
        info["desc"] = "市场普跌, 风险偏好低, 关注政策/护盘信号"
    elif up_ratio > 0.6:
        info["signal"] = "结构性上涨"
        info["desc"] = "结构性行情, 抓主线"
    elif up_ratio < 0.4:
        info["signal"] = "结构性下跌"
        info["desc"] = "多数板块下跌, 谨慎"
    else:
        info["signal"] = "分化"
        info["desc"] = "板块分化, 精选个股"

    return info


# ============================================================
# 5. 主线板块识别
# ============================================================
def identify_main_themes(top_n: int = 5) -> Dict:
    """识别市场主线板块
    主线条件:
        - 涨幅居前
        - 资金大幅流入
        - 上涨家数占比高
        - 概念热度高
    """
    industry_df = get_industry_sectors()
    concept_df = get_concept_sectors()
    flow_df = get_sector_fund_flow("今日")

    if industry_df.empty:
        return {"main_themes": [], "info": "数据不足"}

    # 行业板块综合评分
    industry_scored = calc_sector_score(industry_df, flow_df)
    concept_scored = calc_sector_score(concept_df, flow_df) if not concept_df.empty else pd.DataFrame()

    main_themes = []
    if not industry_scored.empty:
        for _, row in industry_scored.head(top_n).iterrows():
            main_themes.append({
                "type": "行业",
                "name": row.get("name", ""),
                "pct_change": row.get("pct_change", 0),
                "main_net": row.get("main_net", 0),
                "score": row.get("total_score", 0),
                "leader": row.get("leader", ""),
            })

    if not concept_scored.empty:
        for _, row in concept_scored.head(top_n).iterrows():
            main_themes.append({
                "type": "概念",
                "name": row.get("name", ""),
                "pct_change": row.get("pct_change", 0),
                "main_net": row.get("main_net", 0),
                "score": row.get("total_score", 0),
                "leader": row.get("leader", ""),
            })

    # 按总分排序
    main_themes.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "main_themes": main_themes[:top_n * 2],
        "info": f"识别到 {len(main_themes[:top_n*2])} 个主线热点",
    }


# ============================================================
# 6. 板块共振分析
# ============================================================
def sector_resonance_analysis(sector_name: str, stock_codes: List[str]) -> Dict:
    """分析板块内个股共振情况
    Args:
        sector_name: 板块名
        stock_codes: 关注个股列表
    """
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
    except Exception as e:
        return {"error": str(e)}

    if df.empty:
        return {}

    df["代码"] = df["代码"].astype(str)
    sub = df[df["代码"].isin(stock_codes)]

    if sub.empty:
        return {"info": "未找到关注个股"}

    up = (sub["涨跌幅"] > 0).sum()
    down = (sub["涨跌幅"] < 0).sum()
    flat = (sub["涨跌幅"] == 0).sum()

    avg_change = sub["涨跌幅"].mean() if not sub.empty else 0
    max_change = sub["涨跌幅"].max() if not sub.empty else 0
    min_change = sub["涨跌幅"].min() if not sub.empty else 0

    return {
        "sector": sector_name,
        "watch_count": len(stock_codes),
        "found": len(sub),
        "up": int(up),
        "down": int(down),
        "flat": int(flat),
        "avg_pct_change": round(float(avg_change), 2),
        "max_pct_change": round(float(max_change), 2),
        "min_pct_change": round(float(min_change), 2),
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 行业板块涨幅 Top 10 ===")
    df = rank_sectors("industry", top_n=10)
    if not df.empty:
        cols = [c for c in ["name", "pct_change", "leader", "leader_pct"] if c in df.columns]
        print(df[cols].to_string())

    print("\n=== 行业资金流入 Top 5 ===")
    df = top_fund_inflow("今日", "industry", top_n=5)
    if not df.empty:
        print(df.to_string())

    print("\n=== 主线板块识别 ===")
    themes = identify_main_themes(top_n=5)
    for t in themes.get("main_themes", []):
        print(f"  [{t['type']}] {t['name']}: 涨幅{t['pct_change']:.2f}%, 资金{t.get('main_net', 0):.0f}, 龙头{t['leader']}")
