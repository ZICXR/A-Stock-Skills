"""
limit-up-tracker: 涨停板追踪
=============================

功能:
    - 当日涨停板
    - 连板梯队
    - 涨停原因分析
    - 炸板率统计
    - 涨停强度评估
"""

import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import sys
sys.path.insert(0, "skills/01-infra")
from astock_utils.astock_utils import normalize_stock_code

logger = logging.getLogger(__name__)


# ============================================================
# 1. 当日涨停板
# ============================================================
def get_zt_pool(date: Optional[str] = None) -> pd.DataFrame:
    """获取当日涨停板池
    Args:
        date: YYYY-MM-DD, 默认今天
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    try:
        import akshare as ak
        df = ak.stock_zt_pool_em(date=date)
    except Exception as e:
        logger.error(f"akshare 获取涨停板失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {
        "代码": "code", "名称": "name", "涨跌幅": "pct_change",
        "最新价": "price", "成交额": "amount", "流通市值": "circ_mv",
        "总市值": "total_mv", "换手率": "turnover", "封板资金": "limit_funds",
        "首次封板时间": "first_time", "最后封板时间": "last_time",
        "炸板次数": "limit_break_count", "连板数": "consecutive",
        "所属行业": "industry", "涨停原因": "reason"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


# ============================================================
# 2. 连板梯队
# ============================================================
def get_consecutive_zt(days: int = 5) -> pd.DataFrame:
    """连板梯队分析
    Returns:
        各连板数 (1/2/3/4/5+) 的股票数量和代表个股
    """
    end = datetime.now()
    start = end - timedelta(days=days)
    all_zt = []

    for i in range(days):
        date = (end - timedelta(days=i)).strftime("%Y%m%d")
        df = get_zt_pool(date)
        if not df.empty and "consecutive" in df.columns:
            all_zt.append(df)

    if not all_zt:
        return pd.DataFrame()

    # 合并取最后一天的连板数据
    latest = all_zt[0]
    consecutive_col = "consecutive" if "consecutive" in latest.columns else None
    if not consecutive_col:
        return pd.DataFrame()

    # 统计各梯队
    stats = []
    for n in [1, 2, 3, 4, 5]:
        subset = latest[latest[consecutive_col] == n]
        stats.append({
            "consecutive": n,
            "count": len(subset),
            "stocks": subset["name"].tolist()[:5] if "name" in subset.columns else [],
        })

    # 5板以上
    high_subset = latest[latest[consecutive_col] >= 5]
    if not high_subset.empty:
        stats.append({
            "consecutive": "5+",
            "count": len(high_subset),
            "stocks": high_subset["name"].tolist()[:5] if "name" in high_subset.columns else [],
        })

    return pd.DataFrame(stats)


# ============================================================
# 3. 涨停强度评估
# ============================================================
def evaluate_zt_strength(zt_row: pd.Series) -> Dict:
    """评估涨停强度"""
    score = 0
    factors = []

    # 1. 封单金额
    limit_funds = zt_row.get("limit_funds", 0) or 0
    if limit_funds > 1e8:
        score += 2
        factors.append("封单>1亿, 强势封板")
    elif limit_funds > 5e7:
        score += 1
        factors.append("封单>5000万")
    elif limit_funds > 0:
        factors.append(f"封单{limit_funds/1e4:.0f}万")
    else:
        factors.append("封单未公布")

    # 2. 涨停时间
    first_time = zt_row.get("first_time", "")
    if first_time:
        try:
            t = pd.to_datetime(first_time, format="%H:%M:%S", errors="coerce")
            if pd.notna(t) and t.hour < 10:
                score += 2
                factors.append("早盘封板, 强度高")
            elif pd.notna(t) and t.hour < 13:
                score += 1
                factors.append("午盘前封板")
            elif pd.notna(t):
                factors.append("尾盘封板, 强度一般")
        except:
            pass

    # 3. 炸板次数
    break_count = zt_row.get("limit_break_count", 0) or 0
    if break_count == 0:
        score += 1
        factors.append("一字/快速封板, 无炸板")
    elif break_count >= 2:
        score -= 1
        factors.append(f"炸板{break_count}次, 强度弱")

    # 4. 连板数
    consecutive = zt_row.get("consecutive", 1) or 1
    if consecutive >= 5:
        score += 2
        factors.append(f"{consecutive}连板, 高位妖股")
    elif consecutive >= 3:
        score += 1
        factors.append(f"{consecutive}连板, 强趋势")

    # 5. 流通市值
    circ_mv = zt_row.get("circ_mv", 0) or 0
    if 0 < circ_mv < 5e9:  # 5亿以下小盘
        score += 1
        factors.append("小盘股, 易拉升")
    elif circ_mv > 5e10:  # 500亿大盘
        factors.append("大盘股, 涨停稀缺")

    # 强度等级
    if score >= 6:
        level = "极强"
    elif score >= 4:
        level = "强"
    elif score >= 2:
        level = "中"
    elif score >= 0:
        level = "弱"
    else:
        level = "极弱"

    return {
        "score": score,
        "level": level,
        "factors": factors,
    }


# ============================================================
# 4. 涨停原因归类
# ============================================================
def categorize_zt_reason(reason: str) -> str:
    """涨停原因归类"""
    if not reason:
        return "未知"

    reason_categories = {
        "AI/科技": ["AI", "人工智能", "算力", "大模型", "GPT", "芯片", "半导体", "科技", "数字"],
        "新能源": ["锂电", "光伏", "新能源", "储能", "充电桩", "电池"],
        "汽车": ["汽车", "整车", "新能源车", "造车", "智驾", "无人驾驶"],
        "医药": ["医药", "生物", "创新药", "CXO", "医疗器械", "中药"],
        "军工": ["军工", "国防", "航天", "航空"],
        "消费": ["消费", "白酒", "食品", "饮料", "零售", "餐饮"],
        "金融": ["证券", "银行", "保险", "金融", "多元金融"],
        "房地产": ["房地产", "地产", "建筑"],
        "重组": ["重组", "并购", "借壳", "收购", "股权转让"],
        "高送转": ["高送转", "分红", "送股"],
        "政策": ["政策", "国务院", "发改委", "工信部"],
    }

    for cat, keywords in reason_categories.items():
        if any(kw in reason for kw in keywords):
            return cat

    return "其他"


def summarize_zt_reasons(zt_df: pd.DataFrame) -> pd.DataFrame:
    """涨停原因汇总"""
    if zt_df.empty or "reason" not in zt_df.columns:
        return pd.DataFrame()

    zt_df = zt_df.copy()
    zt_df["category"] = zt_df["reason"].apply(categorize_zt_reason)

    summary = zt_df.groupby("category").size().reset_index(name="count")
    summary = summary.sort_values("count", ascending=False).reset_index(drop=True)

    return summary


# ============================================================
# 5. 炸板率统计
# ============================================================
def calc_break_rate(date: Optional[str] = None) -> Dict:
    """计算炸板率
    Args:
        date: YYYY-MM-DD
    """
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    try:
        import akshare as ak
        # 涨停板
        zt_df = ak.stock_zt_pool_em(date=date)
        # 曾涨停 (含炸板)
        zt_zb_df = ak.stock_zt_pool_zbgc_em(date=date)
    except Exception as e:
        logger.error(f"akshare 获取炸板数据失败: {e}")
        return {}

    zt_count = len(zt_df) if not zt_df.empty else 0
    zbgc_count = len(zt_zb_df) if not zt_zb_df.empty else 0

    # 炸板数 = 曾涨停 - 涨停
    broken = max(0, zbgc_count - zt_count)
    break_rate = (broken / zbgc_count * 100) if zbgc_count > 0 else 0

    return {
        "date": date,
        "zt_count": zt_count,
        "zb_count": zbgc_count,
        "broken": broken,
        "break_rate": round(break_rate, 2),
    }


# ============================================================
# 6. 涨停综合报告
# ============================================================
def zt_daily_report(date: Optional[str] = None) -> Dict:
    """涨停板综合日报"""
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    zt_pool = get_zt_pool(date)
    consecutive = get_consecutive_zt(days=5)
    break_info = calc_break_rate(date)

    # 给每只涨停股打强度
    if not zt_pool.empty:
        zt_pool["strength"] = zt_pool.apply(evaluate_zt_strength, axis=1)

    return {
        "date": date,
        "zt_pool": zt_pool,
        "consecutive": consecutive,
        "break_info": break_info,
        "reason_summary": summarize_zt_reasons(zt_pool),
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 当日涨停板 ===")
    df = get_zt_pool()
    if not df.empty:
        print(f"涨停数: {len(df)}")
        cols = [c for c in ["code", "name", "pct_change", "consecutive", "reason"] if c in df.columns]
        print(df[cols].head(10).to_string())

    print("\n=== 涨停原因汇总 ===")
    if not df.empty:
        print(summarize_zt_reasons(df).to_string())

    print("\n=== 炸板率 ===")
    info = calc_break_rate()
    print(info)
