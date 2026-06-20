"""
example_01_daily_review.py - 每日复盘工作流示例
================================================

运行: python examples/01_daily_review.py

功能: 自动生成每日 A 股复盘报告
"""

import sys
sys.path.insert(0, ".")

from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report


def main():
    print("=" * 60)
    print("📈  A股每日复盘报告生成器")
    print("=" * 60)

    # 生成报告
    report = generate_daily_report()

    # 显示报告预览
    lines = report.split("\n")
    print(f"\n报告总行数: {len(lines)}")
    print(f"报告总字符: {len(report)}\n")
    print("=" * 60)
    print("报告预览 (前30行):")
    print("=" * 60)
    for line in lines[:30]:
        print(line)

    print("\n...")
    print("=" * 60)
    print("✅ 报告已生成完毕!")


if __name__ == "__main__":
    main()
