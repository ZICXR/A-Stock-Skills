"""
example_02_limit_up_analysis.py - 涨停板分析示例
=================================================

运行: python examples/02_limit_up_analysis.py

功能: 分析当日涨停板, 找出强势涨停股
"""

import sys
sys.path.insert(0, ".")

from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import (
    get_zt_pool, evaluate_zt_strength, get_consecutive_zt,
    calc_break_rate, summarize_zt_reasons
)


def main():
    print("=" * 60)
    print("🚀  涨停板深度分析")
    print("=" * 60)

    # 1. 涨停统计
    zt = get_zt_pool()
    print(f"\n📊 当日涨停统计")
    print(f"  涨停数: {len(zt)}")

    # 2. 炸板率
    br = calc_break_rate()
    if br:
        print(f"  炸板率: {br.get('break_rate', 0)}%")
        print(f"  炸板数: {br.get('broken', 0)}")

    # 3. 连板梯队
    cons = get_consecutive_zt(days=5)
    if not cons.empty:
        print(f"\n📈 连板梯队")
        for _, row in cons.iterrows():
            stocks = ", ".join(row.get("stocks", [])[:3])
            print(f"  {row['consecutive']}板: {row['count']}只 ({stocks})")

    # 4. 涨停原因分布
    reasons = summarize_zt_reasons(zt)
    if not reasons.empty:
        print(f"\n🏷️  涨停原因分布 Top 5")
        for _, row in reasons.head(5).iterrows():
            print(f"  {row['category']}: {row['count']}只")

    # 5. 强势涨停 (强度 >= 4)
    print(f"\n💪 强势涨停股 (强度>=4)")
    strong_zt = []
    for _, row in zt.iterrows():
        strength = evaluate_zt_strength(row)
        if strength["score"] >= 4:
            strong_zt.append({
                "name": row.get("name", ""),
                "code": row.get("code", ""),
                "consecutive": row.get("consecutive", 1),
                "score": strength["score"],
                "level": strength["level"],
                "factors": strength["factors"],
            })

    # 按强度排序
    strong_zt.sort(key=lambda x: x["score"], reverse=True)
    for i, s in enumerate(strong_zt[:10], 1):
        print(f"  {i}. {s['code']} {s['name']} ({s['level']}, {s['score']}分)")
        print(f"     {s['consecutive']}连板, {', '.join(s['factors'][:2])}")


if __name__ == "__main__":
    main()
