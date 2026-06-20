#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-news-collector: 财经新闻采集与情绪分析"""

import sys
import re
import argparse
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime


# ============================================================
# 情绪词典
# ============================================================
POSITIVE_WORDS = [
    "涨停", "大涨", "突破", "新高", "利好", "中标", "签约", "盈利",
    "增长", "受益", "龙头", "首板", "连板", "妖股", "主线", "风口",
    "增持", "回购", "分红", "业绩超预期", "订单", "扩产", "并购",
    "重组", "战略合作", "获批", "授权", "独家", "重大", "突破性",
    "净利", "提振", "发力", "创新高", "走强"
]

NEGATIVE_WORDS = [
    "跌停", "大跌", "破位", "新低", "利空", "亏损", "下滑", "风险",
    "减持", "套现", "违规", "处罚", "诉讼", "调查", "退市", "ST",
    "业绩不及预期", "召回", "停产", "关闭", "暴跌", "崩盘", "踩雷",
    "净亏", "下滑", "下降", "走弱", "创新低", "重挫", "跳水", "低迷"
]


def calc_sentiment(text: str) -> Dict:
    """单条新闻情绪打分"""
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


def summarize_sentiment(news_df: pd.DataFrame) -> Dict:
    """汇总新闻情绪"""
    if news_df.empty or "sentiment" not in news_df.columns:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0,
                "score": 0, "label": "neutral"}

    total = len(news_df)
    pos = (news_df["sentiment"] == "positive").sum()
    neg = (news_df["sentiment"] == "negative").sum()
    neu = (news_df["sentiment"] == "neutral").sum()
    score = (pos - neg) / total * 100 if total else 0

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
        "score": round(float(score), 2),
        "label": label,
    }


def filter_by_keyword(news_df: pd.DataFrame, keywords: List[str], match_col: str = "title") -> pd.DataFrame:
    if news_df.empty or match_col not in news_df.columns:
        return news_df
    pattern = "|".join([re.escape(k) for k in keywords])
    return news_df[news_df[match_col].astype(str).str.contains(pattern, na=False, regex=True)]


# ============================================================
# 数据获取
# ============================================================
def get_stock_news(code: str, max_count: int = 50) -> pd.DataFrame:
    """获取个股新闻"""
    try:
        import akshare as ak
        df = ak.stock_news_em(symbol=str(code).zfill(6))
    except Exception as e:
        print(f"获取新闻失败: {e}", file=sys.stderr)
        return pd.DataFrame()

    if df.empty:
        return df

    # 标准化列名
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


def get_market_news(max_count: int = 100) -> pd.DataFrame:
    """获取全市场快讯"""
    try:
        import akshare as ak
        df = ak.stock_info_global_em()
    except Exception:
        try:
            import akshare as ak
            df = ak.stock_info_global_cls()
        except:
            return pd.DataFrame()

    if not df.empty and "标题" in df.columns:
        df = df.rename(columns={"标题": "title", "内容": "content",
                                 "发布时间": "date", "来源": "source"})
        if "title" in df.columns:
            df["sentiment"] = df["title"].apply(lambda x: calc_sentiment(str(x))["label"])
    return df.head(max_count)


def get_hot_sector_news(top_n: int = 10) -> pd.DataFrame:
    """获取热点板块新闻"""
    try:
        import akshare as ak
        return ak.stock_board_concept_name_em().head(top_n)
    except Exception:
        return pd.DataFrame()


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="stock-news-collector")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("stock-news", help="个股新闻")
    p.add_argument("code")
    p.add_argument("--max", type=int, default=20)

    p = sub.add_parser("market-news", help="市场快讯")
    p.add_argument("--max", type=int, default=50)

    p = sub.add_parser("sentiment", help="个股情绪汇总")
    p.add_argument("code")
    p.add_argument("--max", type=int, default=20)

    p = sub.add_parser("hot-sectors", help="热点板块")
    p.add_argument("--top", type=int, default=10)

    args = parser.parse_args()

    if args.cmd == "stock-news":
        df = get_stock_news(args.code, args.max)
        if not df.empty:
            cols = [c for c in ["date", "title", "sentiment"] if c in df.columns]
            print(df[cols].to_string())
        else:
            print("暂无数据")

    elif args.cmd == "market-news":
        df = get_market_news(args.max)
        if not df.empty:
            cols = [c for c in ["date", "title", "sentiment"] if c in df.columns]
            print(df[cols].head(args.max).to_string())

    elif args.cmd == "sentiment":
        df = get_stock_news(args.code, args.max)
        summary = summarize_sentiment(df)
        print(f"情绪: {summary['label']} (分数: {summary['score']})")
        print(f"  利好: {summary['positive']}, 利空: {summary['negative']}, 中性: {summary['neutral']}")

    elif args.cmd == "hot-sectors":
        df = get_hot_sector_news(args.top)
        if not df.empty:
            print(df.to_string())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
