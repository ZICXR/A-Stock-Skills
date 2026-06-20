#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""limit-up-tracker: 涨停板追踪"""

import sys
import argparse
import pandas as pd
from datetime import datetime
from typing import Dict


REASON_CATEGORIES = {
    "AI/科技": ["AI", "人工智能", "算力", "大模型", "GPT", "芯片", "半导体", "科技", "数字"],
    "新能源": ["锂电", "光伏", "新能源", "储能", "充电桩", "电池"],
    "汽车": ["汽车", "整车", "新能源车", "造车", "智驾", "无人驾驶"],
    "医药": ["医药", "生物", "创新药", "CXO", "医疗器械", "中药"],
    "军工": ["军工", "国防", "航天", "航空"],
    "消费": ["消费", "白酒", "食品", "饮料", "零售", "餐饮"],
    "金融": ["证券", "银行", "保险", "金融"],
    "房地产": ["房地产", "地产", "建筑"],
    "重组": ["重组", "并购", "借壳", "收购", "股权转让"],
    "高送转": ["高送转", "分红", "送股"],
    "政策": ["政策", "国务院", "发改委", "工信部"],
}


def categorize_zt_reason(reason: str) -> str:
    if not reason:
        return "未知"
    for cat, kws in REASON_CATEGORIES.items():
        if any(kw in reason for kw in kws):
            return cat
    return "其他"


def get_zt_pool(date: str = None) -> pd.DataFrame:
    """涨停板池"""
    if not date:
        date = datetime.now().strftime("%Y%m%d")
    try:
        import akshare as ak
        df = ak.stock_zt_pool_em(date=date)
    except Exception as e:
        print(f"获取涨停板失败: {e}", file=sys.stderr)
        return pd.DataFrame()
    if df.empty:
        return df
    rm = {"代码": "code", "名称": "name", "涨跌幅": "pct_change", "最新价": "price",
          "成交额": "amount", "流通市值": "circ_mv", "总市值": "total_mv",
          "换手率": "turnover", "封板资金": "limit_funds",
          "首次封板时间": "first_time", "最后封板时间": "last_time",
          "炸板次数": "limit_break_count", "连板数": "consecutive",
          "所属行业": "industry", "涨停原因": "reason"}
    return df.rename(columns={k: v for k, v in rm.items() if k in df.columns})


def evaluate_zt_strength(row: pd.Series) -> Dict:
    """涨停强度评估"""
    score = 0
    factors = []

    funds = row.get("limit_funds", 0) or 0
    if funds > 1e8:
        score += 2; factors.append("封单>1亿")
    elif funds > 5e7:
        score += 1; factors.append("封单>5000万")
    elif funds > 0:
        factors.append(f"封单{funds/1e4:.0f}万")

    first_time = row.get("first_time", "")
    if first_time:
        try:
            t = pd.to_datetime(str(first_time), format="%H:%M:%S", errors="coerce")
            if pd.notna(t) and t.hour < 10:
                score += 2; factors.append("早盘封板")
            elif pd.notna(t) and t.hour < 13:
                score += 1; factors.append("午盘前封板")
        except:
            pass

    brk = row.get("limit_break_count", 0) or 0
    if brk == 0:
        score += 1; factors.append("无炸板")
    elif brk >= 2:
        score -= 1; factors.append(f"炸板{brk}次")

    cons = row.get("consecutive", 1) or 1
    if cons >= 5:
        score += 2; factors.append(f"{cons}连板(高位妖股)")
    elif cons >= 3:
        score += 1; factors.append(f"{cons}连板")

    mv = row.get("circ_mv", 0) or 0
    if 0 < mv < 5e9:
        score += 1; factors.append("小盘股")
    elif mv > 5e10:
        factors.append("大盘股")

    reason = str(row.get("reason", ""))
    main_themes = ["AI", "新能源", "汽车", "重组", "高送转"]
    if any(t in reason for t in main_themes):
        score += 2; factors.append("主流题材")

    if score >= 6: level = "极强"
    elif score >= 4: level = "强"
    elif score >= 2: level = "中"
    elif score >= 0: level = "弱"
    else: level = "极弱"

    return {"score": score, "level": level, "factors": factors}


def get_consecutive_zt(days: int = 5) -> pd.DataFrame:
    """连板梯队"""
    end = datetime.now()
    rows = []
    for i in range(days):
        date = (end - pd.Timedelta(days=i)).strftime("%Y%m%d")
        df = get_zt_pool(date)
        if not df.empty and "consecutive" in df.columns:
            rows.append(df)
    if not rows:
        return pd.DataFrame()

    latest = rows[0]
    if "consecutive" not in latest.columns:
        return pd.DataFrame()
    stats = []
    for n in [1, 2, 3, 4, 5]:
        sub = latest[latest["consecutive"] == n]
        stats.append({
            "consecutive": f"{n}板",
            "count": len(sub),
            "stocks": sub["name"].tolist()[:5] if "name" in sub.columns else [],
        })
    high = latest[latest["consecutive"] >= 5]
    if not high.empty:
        stats.append({
            "consecutive": "5+板",
            "count": len(high),
            "stocks": high["name"].tolist()[:5] if "name" in high.columns else [],
        })
    return pd.DataFrame(stats)


def calc_break_rate(date: str = None) -> Dict:
    """炸板率"""
    if not date:
        date = datetime.now().strftime("%Y%m%d")
    try:
        import akshare as ak
        zt_df = ak.stock_zt_pool_em(date=date)
        zt_zb_df = ak.stock_zt_pool_zbgc_em(date=date)
    except Exception:
        return {}
    zt_count = len(zt_df) if not zt_df.empty else 0
    zbgc_count = len(zt_zb_df) if not zt_zb_df.empty else 0
    broken = max(0, zbgc_count - zt_count)
    rate = round(broken / zbgc_count * 100, 2) if zbgc_count > 0 else 0
    return {"zt_count": zt_count, "zb_count": zbgc_count, "broken": broken, "break_rate": rate}


def summarize_zt_reasons(zt_df: pd.DataFrame) -> pd.DataFrame:
    """涨停原因汇总"""
    if zt_df.empty or "reason" not in zt_df.columns:
        return pd.DataFrame()
    zt_df = zt_df.copy()
    zt_df["category"] = zt_df["reason"].apply(categorize_zt_reason)
    summary = zt_df.groupby("category").size().reset_index(name="count")
    return summary.sort_values("count", ascending=False).reset_index(drop=True)


def zt_daily_report(date: str = None) -> Dict:
    """涨停板综合日报"""
    if not date:
        date = datetime.now().strftime("%Y%m%d")
    pool = get_zt_pool(date)
    cons = get_consecutive_zt(days=5)
    br = calc_break_rate(date)
    return {
        "date": date,
        "zt_pool": pool,
        "consecutive": cons,
        "break_info": br,
        "reasons": summarize_zt_reasons(pool),
    }


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="limit-up-tracker")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("pool", help="涨停板")
    p.add_argument("--date")
    p = sub.add_parser("consecutive", help="连板梯队")
    p.add_argument("--days", type=int, default=5)
    sub.add_parser("break", help="炸板率")
    p = sub.add_parser("reasons", help="涨停原因")
    p.add_argument("--date")
    p = sub.add_parser("report", help="综合日报")
    p.add_argument("--date")
    p = sub.add_parser("evaluate", help="评估强度")
    p.add_argument("code")

    args = parser.parse_args()

    if args.cmd == "pool":
        df = get_zt_pool(args.date)
        if not df.empty:
            cols = [c for c in ["code", "name", "pct_change", "consecutive", "reason"] if c in df.columns]
            print(f"涨停数: {len(df)}")
            print(df[cols].head(20).to_string())

    elif args.cmd == "consecutive":
        df = get_consecutive_zt(args.days)
        if not df.empty:
            print(df.to_string())

    elif args.cmd == "break":
        br = calc_break_rate(args.date)
        for k, v in br.items():
            print(f"  {k}: {v}")

    elif args.cmd == "reasons":
        df = get_zt_pool(args.date)
        rs = summarize_zt_reasons(df)
        if not rs.empty:
            print(rs.to_string())

    elif args.cmd == "report":
        r = zt_daily_report(args.date)
        print(f"日期: {r['date']}")
        if r.get('break_info'):
            print(f"涨停数: {r['break_info'].get('zt_count', 0)}, 炸板率: {r['break_info'].get('break_rate', 0)}%")

    elif args.cmd == "evaluate":
        df = get_zt_pool()
        if not df.empty and "code" in df.columns:
            target = df[df["code"].astype(str) == str(args.code).zfill(6)]
            if not target.empty:
                s = evaluate_zt_strength(target.iloc[0])
                print(f"强度: {s['level']} ({s['score']}分)")
                print(f"因素: {', '.join(s['factors'])}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
