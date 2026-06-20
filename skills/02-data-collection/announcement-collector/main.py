#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""announcement-collector: 公司公告采集"""

import sys
import argparse
import pandas as pd
from typing import List, Dict


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


def classify(title: str) -> List[str]:
    """公告分类"""
    cats = []
    if not title:
        return cats
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in title for kw in keywords):
            cats.append(cat)
    if not cats:
        cats.append("其他")
    return cats


def is_key(title: str) -> bool:
    """是否关键公告"""
    if not title:
        return False
    key_words = ["重大", "停牌", "复牌", "重组", "中标", "签约", "业绩", "ST", "退市",
                 "增持", "回购", "分红", "处罚", "调查"]
    return any(w in title for w in key_words)


def filter_by_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """按分类筛选"""
    if df.empty or "categories" not in df.columns:
        return df
    return df[df["categories"].apply(lambda x: category in x)]


def filter_key(df: pd.DataFrame) -> pd.DataFrame:
    """筛选关键公告"""
    if df.empty or "is_key" not in df.columns:
        return df
    return df[df["is_key"] == True]


def summarize(df: pd.DataFrame) -> Dict:
    """汇总"""
    if df.empty:
        return {"total": 0, "key": 0, "by_category": {}}
    total = len(df)
    key_n = int(df["is_key"].sum()) if "is_key" in df.columns else 0
    cat_count = {}
    if "categories" in df.columns:
        for cats in df["categories"]:
            for c in cats:
                cat_count[c] = cat_count.get(c, 0) + 1
    return {"total": int(total), "key": key_n, "by_category": cat_count}


def get_announcements(code: str, max_count: int = 50) -> pd.DataFrame:
    """获取公告"""
    try:
        import akshare as ak
        df = ak.stock_announcement_report(symbol=str(code).zfill(6))
    except Exception as e:
        print(f"获取公告失败: {e}", file=sys.stderr)
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {"公告日期": "date", "公告标题": "title", "公告链接": "url",
                  "公告类型": "category"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "title" in df.columns:
        df["categories"] = df["title"].apply(classify)
        df["is_key"] = df["title"].apply(is_key)

    if len(df) > max_count:
        df = df.head(max_count)
    return df


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="announcement-collector")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("announcements", help="所有公告")
    p.add_argument("code")
    p.add_argument("--max", type=int, default=30)

    p = sub.add_parser("key", help="关键公告")
    p.add_argument("code")
    p.add_argument("--max", type=int, default=100)

    p = sub.add_parser("category", help="按分类筛选")
    p.add_argument("code")
    p.add_argument("--type", dest="cat", required=True)

    sub.add_parser("summary", help="汇总统计").add_argument("code")

    args = parser.parse_args()

    if args.cmd == "announcements":
        df = get_announcements(args.code, args.max)
        if not df.empty:
            cols = [c for c in ["date", "title", "categories", "is_key"] if c in df.columns]
            print(df[cols].to_string())

    elif args.cmd == "key":
        df = get_announcements(args.code, args.max)
        df = filter_key(df)
        if not df.empty:
            cols = [c for c in ["date", "title"] if c in df.columns]
            print(df[cols].to_string())
        else:
            print("无关键公告")

    elif args.cmd == "category":
        df = get_announcements(args.code)
        df = filter_by_category(df, args.cat)
        if not df.empty:
            cols = [c for c in ["date", "title"] if c in df.columns]
            print(df[cols].to_string())
        else:
            print(f"无 {args.cat} 类公告")

    elif args.cmd == "summary":
        df = get_announcements(args.code)
        s = summarize(df)
        print(f"总数: {s['total']}, 关键: {s['key']}")
        print("分类统计:")
        for cat, cnt in s["by_category"].items():
            print(f"  {cat}: {cnt}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
