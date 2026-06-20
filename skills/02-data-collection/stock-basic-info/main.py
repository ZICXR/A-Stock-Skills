#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-basic-info: 个股基本信息"""

import sys
import argparse
import pandas as pd
from typing import Dict


def get_stock_info(code: str) -> Dict:
    """公司基本信息"""
    try:
        import akshare as ak
        df = ak.stock_individual_info_em(symbol=str(code).zfill(6))
    except Exception as e:
        print(f"获取股票信息失败: {e}", file=sys.stderr)
        return {}

    if df.empty:
        return {}
    info = {}
    for _, row in df.iterrows():
        info[row.get("item", "")] = row.get("value", "")
    info["code"] = code
    return info


def get_realtime(code: str) -> Dict:
    """实时行情"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"].astype(str) == str(code).zfill(6)]
        if target.empty:
            return {}
        row = target.iloc[0]
        return {
            "code": row.get("代码", code),
            "name": row.get("名称", ""),
            "price": float(row.get("最新价", 0)),
            "change": float(row.get("涨跌额", 0)),
            "pct_change": float(row.get("涨跌幅", 0)),
            "open": float(row.get("今开", 0)),
            "high": float(row.get("最高", 0)),
            "low": float(row.get("最低", 0)),
            "pre_close": float(row.get("昨收", 0)),
            "volume": float(row.get("成交量", 0)),
            "amount": float(row.get("成交额", 0)),
            "turnover": float(row.get("换手率", 0)),
            "pe": float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else None,
            "pb": float(row.get("市净率", 0)) if row.get("市净率") else None,
            "total_mv": float(row.get("总市值", 0)),
            "circ_mv": float(row.get("流通市值", 0)),
        }
    except Exception as e:
        print(f"获取实时行情失败: {e}", file=sys.stderr)
        return {}


def get_top_holders(code: str, top_n: int = 10) -> pd.DataFrame:
    """前十大股东"""
    try:
        import akshare as ak
        df = ak.stock_main_holders_em(symbol=code)
    except Exception:
        try:
            import akshare as ak
            df = ak.stock_main_stock_holder(stock=code)
        except:
            return pd.DataFrame()
    if not df.empty and len(df) > top_n:
        df = df.head(top_n)
    return df


def get_main_business(code: str) -> Dict:
    """主营业务构成"""
    try:
        import akshare as ak
        df = ak.stock_zyjs_ths(symbol=code)
        return {"items": df.to_dict("records") if not df.empty else []}
    except Exception:
        return {"items": []}


def get_financial_summary(code: str) -> Dict:
    """业绩快报"""
    try:
        import akshare as ak
        df = ak.stock_yjkb_em(symbol=code)
        return {"items": df.to_dict("records") if not df.empty else []}
    except Exception:
        return {"items": []}


def get_stock_card(code: str) -> Dict:
    """完整信息卡"""
    return {
        "code": code,
        "info": get_stock_info(code),
        "realtime": get_realtime(code),
    }


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="stock-basic-info")
    sub = parser.add_subparsers(dest="cmd")

    for cmd, help_text in [
        ("info", "公司信息"), ("realtime", "实时行情"),
        ("business", "主营业务"), ("card", "完整信息卡"),
    ]:
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("code")

    p = sub.add_parser("holders", help="前十大股东")
    p.add_argument("code")
    p.add_argument("--top", type=int, default=10)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    code = args.code

    if args.cmd == "info":
        info = get_stock_info(code)
        for k, v in info.items():
            print(f"  {k}: {v}")

    elif args.cmd == "realtime":
        rt = get_realtime(code)
        for k, v in rt.items():
            print(f"  {k}: {v}")

    elif args.cmd == "holders":
        df = get_top_holders(code, args.top)
        if not df.empty:
            print(df.to_string())

    elif args.cmd == "business":
        b = get_main_business(code)
        for item in b.get("items", [])[:10]:
            print(f"  {item}")

    elif args.cmd == "card":
        c = get_stock_card(code)
        print("=== 公司信息 ===")
        for k, v in c["info"].items():
            print(f"  {k}: {v}")
        print("\n=== 实时行情 ===")
        for k, v in c["realtime"].items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
