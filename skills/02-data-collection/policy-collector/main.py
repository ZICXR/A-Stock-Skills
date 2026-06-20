#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""policy-collector: 政策资讯采集"""

import sys
import argparse
import pandas as pd
from typing import List, Dict


# 政策关键词词典
POLICY_KEYWORDS = {
    "货币政策": ["降准", "降息", "MLF", "LPR", "逆回购", "央行"],
    "财政政策": ["减税", "降费", "补贴", "财政", "国债"],
    "产业政策-半导体": ["半导体", "芯片", "集成电路", "光刻机", "EDA"],
    "产业政策-新能源": ["新能源", "光伏", "锂电", "储能", "新能源汽车"],
    "产业政策-AI": ["人工智能", "AI", "大模型", "算力", "数字经济"],
    "产业政策-医药": ["医药", "创新药", "集采", "医保"],
    "产业政策-汽车": ["汽车", "智驾", "新能源车", "以旧换新"],
    "监管政策": ["证监会", "银保监", "交易所", "退市", "注册制"],
    "房地产": ["房地产", "楼市", "限购", "首付比例"],
}


def get_latest_policies(days: int = 7) -> List[Dict]:
    """获取最新政策(基于关键词模拟)"""
    # 实际生产环境应接入专业政策API
    # 此处基于公开财经新闻关键字识别
    sample_policies = [
        {
            "date": "2024-12-30",
            "source": "央行",
            "title": "央行开展 3000 亿元 MLF 操作",
            "category": "货币政策",
            "content": "中国人民银行公告, 为维护银行体系流动性合理充裕, 12月30日开展 3000 亿元中期借贷便利 (MLF) 操作, 期限 1 年, 中标利率 2.50%",
        },
        {
            "date": "2024-12-29",
            "source": "证监会",
            "title": "证监会发布退市新规",
            "category": "监管政策",
            "content": "进一步严格退市标准, 加大对财务造假等违法行为的打击力度",
        },
        {
            "date": "2024-12-28",
            "source": "工信部",
            "title": "工信部:加快推动集成电路产业高质量发展",
            "category": "产业政策-半导体",
            "content": "工信部表示将继续加大对集成电路产业的支持力度",
        },
    ]
    return sample_policies[:min(len(sample_policies), days)]


def get_industry_policies(industry: str) -> List[Dict]:
    """行业政策"""
    all_policies = get_latest_policies(days=30)
    matched = [p for p in all_policies if industry in p.get("title", "") or industry in p.get("content", "")]
    return matched


def analyze_impact(policy_text: str) -> Dict:
    """政策影响分析"""
    direction = "中性"
    targets = []

    for category, keywords in POLICY_KEYWORDS.items():
        if any(kw in policy_text for kw in keywords):
            # 简化判断
            if any(bull in policy_text for bull in ["支持", "加快", "加大", "降准", "降息", "补贴"]):
                direction = "利好"
            elif any(bear in policy_text for bear in ["退市", "处罚", "严打", "限制"]):
                direction = "利空"
            targets.append(category)
            break

    return {
        "text": policy_text,
        "direction": direction,
        "targets": targets,
        "analysis": f"政策方向: {direction}, 涉及: {', '.join(targets) if targets else '未识别'}",
    }


def extract_beneficiaries(policy_text: str) -> List[str]:
    """提取受益方向"""
    beneficiaries = []
    if "半导体" in policy_text or "芯片" in policy_text:
        beneficiaries.append("半导体/芯片")
    if "新能源" in policy_text or "光伏" in policy_text:
        beneficiaries.append("新能源")
    if "AI" in policy_text or "人工智能" in policy_text:
        beneficiaries.append("AI/算力")
    if "汽车" in policy_text:
        beneficiaries.append("汽车")
    if "医药" in policy_text:
        beneficiaries.append("医药")
    if "降准" in policy_text or "降息" in policy_text:
        beneficiaries.extend(["银行", "地产", "基建"])
    return beneficiaries


def main():
    parser = argparse.ArgumentParser(description="policy-collector")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("latest", help="最新政策")
    p.add_argument("--days", type=int, default=7)
    p = sub.add_parser("industry", help="行业政策")
    p.add_argument("industry")
    p = sub.add_parser("analyze", help="分析影响")
    p.add_argument("text")
    p = sub.add_parser("beneficiaries", help="受益方向")
    p.add_argument("text")
    args = parser.parse_args()

    if args.cmd == "latest":
        policies = get_latest_policies(args.days)
        for p in policies:
            print(f"[{p['date']}] {p['source']}: {p['title']}")
    elif args.cmd == "industry":
        for p in get_industry_policies(args.industry):
            print(f"[{p['date']}] {p['title']}")
    elif args.cmd == "analyze":
        r = analyze_impact(args.text)
        print(f"方向: {r['direction']}, 涉及: {r['targets']}")
    elif args.cmd == "beneficiaries":
        print(extract_beneficiaries(args.text))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
