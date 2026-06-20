"""
announcement-collector: 公司公告采集
======================================

功能:
    - 个股公告 (巨潮资讯/上交所/深交所)
    - 公告分类 (业绩/分红/重组/增减持等)
    - 关键公告识别
    - 公告情绪分析
"""

import re
import logging
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


# 公告分类关键词
CATEGORY_KEYWORDS = {
    "业绩": ["业绩", "盈利", "净利润", "营业收入", "扭亏", "预增", "预减", "业绩快报"],
    "分红": ["分红", "派息", "送股", "转增", "股权激励", "回购"],
    "重组": ["重组", "并购", "收购", "合并", "资产置换", "重大资产"],
    "股东": ["股东", "减持", "增持", "持股", "质押", "解押"],
    "风险": ["风险", "停牌", "复牌", "退市", "ST", "*ST", "处罚", "调查", "诉讼", "违规"],
    "经营": ["中标", "签约", "订单", "合同", "战略合作", "投资", "扩产", "设立"],
    "治理": ["高管", "董事", "监事", "股东大会", "换届", "辞职", "聘任"],
}


def classify_announcement(title: str) -> List[str]:
    """对公告标题进行分类"""
    cats = []
    if not title:
        return cats
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in title for kw in keywords):
            cats.append(cat)
    if not cats:
        cats.append("其他")
    return cats


def is_key_announcement(title: str) -> bool:
    """判断是否关键公告"""
    if not title:
        return False
    key_words = ["重大", "停牌", "复牌", "重组", "中标", "签约", "业绩", "ST", "退市",
                 "增持", "回购", "分红", "处罚", "调查"]
    return any(w in title for w in key_words)


# ============================================================
# 1. 个股公告
# ============================================================
def get_stock_announcements(symbol: str, max_count: int = 50) -> pd.DataFrame:
    """获取个股公告列表
    Args:
        symbol: 6位股票代码
        max_count: 最大数量
    Returns:
        DataFrame: [date, title, url, categories, is_key]
    """
    try:
        import akshare as ak
        df = ak.stock_announcement_report(symbol=symbol)
    except Exception as e:
        logger.error(f"akshare 获取公告失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    # 标准化列名
    rename_map = {
        "公告日期": "date", "公告标题": "title", "公告链接": "url",
        "公告类型": "category", "code": "code", "name": "name",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "title" in df.columns:
        df["categories"] = df["title"].apply(classify_announcement)
        df["is_key"] = df["title"].apply(is_key_announcement)

    if len(df) > max_count:
        df = df.head(max_count)

    return df


# ============================================================
# 2. 关键公告筛选
# ============================================================
def filter_key_announcements(ann_df: pd.DataFrame) -> pd.DataFrame:
    """筛选关键公告"""
    if ann_df.empty or "is_key" not in ann_df.columns:
        return ann_df
    return ann_df[ann_df["is_key"] == True]


# ============================================================
# 3. 按分类筛选
# ============================================================
def filter_by_category(ann_df: pd.DataFrame, category: str) -> pd.DataFrame:
    """按分类筛选
    Args:
        category: 业绩/分红/重组/股东/风险/经营/治理
    """
    if ann_df.empty or "categories" not in ann_df.columns:
        return ann_df
    return ann_df[ann_df["categories"].apply(lambda x: category in x)]


# ============================================================
# 4. 公告统计
# ============================================================
def summarize_announcements(ann_df: pd.DataFrame) -> Dict:
    """汇总公告统计"""
    if ann_df.empty:
        return {"total": 0, "key": 0, "by_category": {}}

    total = len(ann_df)
    key_n = ann_df["is_key"].sum() if "is_key" in ann_df.columns else 0

    # 分类统计
    cat_count = {}
    if "categories" in ann_df.columns:
        for cats in ann_df["categories"]:
            for c in cats:
                cat_count[c] = cat_count.get(c, 0) + 1

    return {
        "total": int(total),
        "key": int(key_n),
        "by_category": cat_count,
    }


# ============================================================
# 5. 最近N天的特定类型公告
# ============================================================
def get_recent_announcements_by_type(symbol: str, category: str,
                                    days: int = 30) -> pd.DataFrame:
    """获取最近N天的某类公告"""
    df = get_stock_announcements(symbol, max_count=200)
    if df.empty:
        return df

    df = filter_by_category(df, category)
    if "date" in df.columns and days > 0:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        df = df[df["date"] >= cutoff]

    return df


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 公告: 平安银行 000001 ===")
    df = get_stock_announcements("000001", max_count=20)
    if not df.empty:
        cols = [c for c in ["date", "title", "categories", "is_key"] if c in df.columns]
        print(df[cols].head(10).to_string())
        print("\n=== 统计 ===")
        print(summarize_announcements(df))

        print("\n=== 关键公告 ===")
        key_df = filter_key_announcements(df)
        print(f"共 {len(key_df)} 条关键公告")
