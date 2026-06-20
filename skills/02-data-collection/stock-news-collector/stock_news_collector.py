"""
stock-news-collector: 财经新闻采集
====================================

功能:
    - 个股新闻 (东方财富/同花顺)
    - 财经快讯
    - 关键词筛选
    - 情绪分析
"""

import re
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


# ============================================================
# 情感关键词
# ============================================================
POSITIVE_WORDS = [
    "涨停", "大涨", "突破", "新高", "利好", "中标", "签约", "盈利",
    "增长", "受益", "龙头", "首板", "连板", "妖股", "主线", "风口",
    "增持", "回购", "分红", "业绩超预期", "订单", "扩产", "并购",
    "重组", "战略合作", "获批", "授权", "独家", "重大", "突破性"
]
NEGATIVE_WORDS = [
    "跌停", "大跌", "破位", "新低", "利空", "亏损", "下滑", "风险",
    "减持", "套现", "违规", "处罚", "诉讼", "调查", "退市", "ST",
    "业绩不及预期", "召回", "停产", "关闭", "暴跌", "崩盘", "踩雷"
]


def calc_sentiment(text: str) -> Dict[str, any]:
    """简易情感打分"""
    if not text:
        return {"score": 0, "label": "neutral", "positive": 0, "negative": 0}
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)
    score = pos - neg
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"
    return {"score": score, "label": label, "positive": pos, "negative": neg}


# ============================================================
# 1. 个股新闻
# ============================================================
def get_stock_news(symbol: str, max_count: int = 50) -> pd.DataFrame:
    """获取个股新闻
    Args:
        symbol: 6位股票代码
        max_count: 最大数量
    Returns:
        DataFrame: [date, title, content, url, source, sentiment]
    """
    try:
        import akshare as ak
        df = ak.stock_news_em(symbol=symbol)
    except Exception as e:
        logger.error(f"akshare 获取新闻失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    # 标准化
    rename_map = {
        "发布时间": "date", "新闻标题": "title", "新闻内容": "content",
        "新闻链接": "url", "文章来源": "source",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "title" in df.columns:
        df["sentiment"] = df["title"].apply(lambda x: calc_sentiment(str(x))["label"])
        df["sent_score"] = df["title"].apply(lambda x: calc_sentiment(str(x))["score"])

    if len(df) > max_count:
        df = df.head(max_count)

    return df


# ============================================================
# 2. 财经快讯
# ============================================================
def get_market_news(max_count: int = 100) -> pd.DataFrame:
    """获取全市场财经快讯"""
    try:
        import akshare as ak
        df = ak.stock_info_global_em()
    except Exception as e:
        logger.error(f"akshare 获取全球快讯失败: {e}")
        try:
            import akshare as ak
            df = ak.stock_info_global_cls()
        except:
            return pd.DataFrame()

    if not df.empty and "标题" in df.columns:
        df = df.rename(columns={"标题": "title", "内容": "content",
                                 "发布时间": "date", "来源": "source"})
        df["sentiment"] = df["title"].apply(lambda x: calc_sentiment(str(x))["label"])
    return df.head(max_count)


# ============================================================
# 3. 关键词筛选
# ============================================================
def filter_by_keyword(news_df: pd.DataFrame, keywords: List[str],
                     match_col: str = "title") -> pd.DataFrame:
    """按关键词筛选新闻"""
    if news_df.empty or match_col not in news_df.columns:
        return news_df
    pattern = "|".join([re.escape(k) for k in keywords])
    return news_df[news_df[match_col].str.contains(pattern, na=False, regex=True)]


# ============================================================
# 4. 情绪汇总
# ============================================================
def summarize_sentiment(news_df: pd.DataFrame) -> Dict:
    """汇总新闻情绪"""
    if news_df.empty or "sentiment" not in news_df.columns:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0,
                "score": 0, "label": "neutral"}

    total = len(news_df)
    pos = (news_df["sentiment"] == "positive").sum()
    neg = (news_df["sentiment"] == "negative").sum()
    neu = (news_df["sentiment"] == "neutral").sum()

    if total == 0:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0, "score": 0, "label": "neutral"}

    score = (pos - neg) / total * 100
    if score > 20:
        label = "very_positive"
    elif score > 5:
        label = "positive"
    elif score < -20:
        label = "very_negative"
    elif score < -5:
        label = "negative"
    else:
        label = "neutral"

    return {
        "total": int(total),
        "positive": int(pos),
        "negative": int(neg),
        "neutral": int(neu),
        "score": round(score, 2),
        "label": label,
    }


# ============================================================
# 5. 板块热点新闻
# ============================================================
def get_hot_sector_news(top_n: int = 10) -> pd.DataFrame:
    """获取热点板块/概念新闻"""
    try:
        import akshare as ak
        # 热门概念
        df = ak.stock_board_concept_name_em()
        return df.head(top_n)
    except Exception as e:
        logger.error(f"获取热点板块失败: {e}")
        return pd.DataFrame()


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 个股新闻: 平安银行 000001 ===")
    df = get_stock_news("000001", max_count=10)
    if not df.empty:
        print(df[["date", "title", "sentiment"]].to_string())
        print("\n=== 情绪汇总 ===")
        print(summarize_sentiment(df))
