"""
dragon-tiger-analysis: 龙虎榜分析
====================================

功能:
    - 龙虎榜每日统计
    - 游资席位追踪
    - 机构席位
    - 知名游资识别
    - 主力动向分析
"""

import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# 知名游资席位 (常见活跃游资)
KNOWN_HOT_MONEY = [
    "方新侠", "作手新一", "赵老哥", "孙哥", "章盟主", "炒股养家",
    "欢乐海", "佛山系", "成都系", "上海溧阳路", "深圳益田路",
    "荣超商务中心", "杭州延安路", "南京中山东路", "宁波桑田路",
    "财通杭州", "华鑫上海分公司", "东方上海源深路"
]


def is_hot_money(branch: str) -> bool:
    """判断是否知名游资"""
    if not branch:
        return False
    for name in KNOWN_HOT_MONEY:
        if name in branch:
            return True
    return False


# ============================================================
# 1. 龙虎榜个股明细
# ============================================================
def get_lhb_detail(date: Optional[str] = None) -> pd.DataFrame:
    """获取龙虎榜明细
    Args:
        date: 日期 YYYY-MM-DD, 默认昨天
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        import akshare as ak
        df = ak.stock_lhb_detail_em(start_date=date, end_date=date)
    except Exception as e:
        logger.error(f"akshare 获取龙虎榜失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    return df


# ============================================================
# 2. 龙虎榜游资追踪
# ============================================================
def track_hot_money(date: Optional[str] = None) -> pd.DataFrame:
    """追踪知名游资动向"""
    df = get_lhb_detail(date)
    if df.empty:
        return df

    # 标记游资席位
    branch_cols = [c for c in df.columns if "营业部" in c or "branch" in c.lower()]
    if not branch_cols:
        return pd.DataFrame()

    # 找出知名游资相关记录
    hot_records = []
    for _, row in df.iterrows():
        for col in branch_cols:
            branch = str(row.get(col, ""))
            if is_hot_money(branch):
                hot_records.append(row)
                break

    return pd.DataFrame(hot_records)


# ============================================================
# 3. 机构席位汇总
# ============================================================
def get_institution_summary(date: Optional[str] = None) -> pd.DataFrame:
    """机构买卖汇总"""
    try:
        import akshare as ak
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        df = ak.stock_lhb_jgmmtj_em(start_date=date, end_date=date)
    except Exception as e:
        logger.error(f"akshare 获取机构买卖汇总失败: {e}")
        return pd.DataFrame()

    return df


# ============================================================
# 4. 个股龙虎榜
# ============================================================
def get_stock_lhb(symbol: str, days: int = 30) -> pd.DataFrame:
    """个股龙虎榜历史
    Args:
        symbol: 6位股票代码
        days: 天数
    """
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        df = ak.stock_lhb_stock_statistic_em(symbol=start, end=end)
    except Exception as e:
        try:
            import akshare as ak
            df = ak.stock_lhb_ggtj_sina(symbol=symbol)
        except:
            return pd.DataFrame()

    if df.empty or "代码" not in df.columns:
        return df

    return df[df["代码"] == symbol].reset_index(drop=True)


# ============================================================
# 5. 涨停游资榜
# ============================================================
def get_zt_hot_money(date: Optional[str] = None) -> pd.DataFrame:
    """涨停板中游资参与的个股"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        import akshare as ak
        df = ak.stock_zt_pool_em(date=date)
    except Exception as e:
        logger.error(f"akshare 获取涨停板失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    return df


# ============================================================
# 6. 综合龙虎榜报告
# ============================================================
def lhb_daily_report(date: Optional[str] = None) -> Dict:
    """每日龙虎榜报告"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    detail = get_lhb_detail(date)
    hot_money = track_hot_money(date)
    inst = get_institution_summary(date)
    zt_pool = get_zt_pool(date)

    summary = {
        "date": date,
        "lhb_stocks": len(detail["代码"].unique()) if not detail.empty and "代码" in detail.columns else 0,
        "hot_money_count": len(hot_money),
        "institution_count": len(inst),
        "zt_stocks": len(zt_pool),
    }

    return {
        "summary": summary,
        "detail": detail,
        "hot_money": hot_money,
        "institution": inst,
        "zt_pool": zt_pool,
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 龙虎榜明细 ===")
    df = get_lhb_detail()
    if not df.empty:
        print(f"共 {len(df)} 条记录")
        print(df.head(5).to_string())

    print("\n=== 游资动向 ===")
    df = track_hot_money()
    if not df.empty:
        print(df.head(10).to_string())

    print("\n=== 机构席位 ===")
    df = get_institution_summary()
    if not df.empty:
        print(df.head(10).to_string())
