#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""market-data-collector: 大盘数据采集"""

import sys
import argparse
import pandas as pd
from typing import Dict
from datetime import datetime, timedelta


MAJOR_INDICES = {
    "000001": "上证指数", "399001": "深证成指", "399006": "创业板指",
    "000688": "科创50", "000300": "沪深300", "000905": "中证500",
    "000852": "中证1000", "000016": "上证50",
}


def get_major_indices() -> pd.DataFrame:
    """主要指数实时"""
    try:
        import akshare as ak
        df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
    except Exception as e:
        print(f"获取指数失败: {e}", file=sys.stderr)
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {"代码": "code", "名称": "name", "最新价": "price",
                  "涨跌幅": "pct_change", "涨跌额": "change",
                  "成交量": "volume", "成交额": "amount"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if "code" in df.columns:
        df["code"] = df["code"].astype(str)
        df = df[df["code"].isin(MAJOR_INDICES.keys())].copy()
    return df


def get_index_kline(symbol: str, days: int = 60) -> pd.DataFrame:
    """指数 K 线"""
    try:
        import akshare as ak
        if str(symbol).startswith(("000", "6", "9")):
            sym = f"sh{symbol}"
        else:
            sym = f"sz{symbol}"
        df = ak.stock_zh_index_daily(symbol=sym)
    except Exception as e:
        print(f"获取指数K线失败: {e}", file=sys.stderr)
        return pd.DataFrame()

    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    return df[df["date"] >= cutoff].reset_index(drop=True)


def get_market_breadth() -> Dict:
    """市场广度"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
    except Exception as e:
        print(f"获取市场广度失败: {e}", file=sys.stderr)
        return {}

    if df.empty:
        return {}

    rename_map = {"涨跌幅": "pct_change"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if "pct_change" not in df.columns:
        return {}

    up = int((df["pct_change"] > 0).sum())
    down = int((df["pct_change"] < 0).sum())
    flat = int((df["pct_change"] == 0).sum())
    limit_up = int((df["pct_change"] >= 9.9).sum())
    limit_down = int((df["pct_change"] <= -9.9).sum())
    return {
        "up": up, "down": down, "flat": flat,
        "limit_up": limit_up, "limit_down": limit_down,
        "total": int(len(df)),
        "up_ratio": round(up / len(df) * 100, 2) if len(df) else 0,
    }


def calc_market_strength(breadth: Dict) -> Dict:
    """市场强度评分"""
    if not breadth or "up_ratio" not in breadth:
        return {"score": 0, "level": "unknown", "desc": "数据不足"}
    ratio = breadth["up_ratio"]
    if ratio < 30:
        return {"score": round(-2 + ratio/30, 2), "level": "very_weak", "desc": "极度弱势"}
    elif ratio < 50:
        return {"score": round(-1 + (ratio-30)/20, 2), "level": "weak", "desc": "弱势震荡"}
    elif ratio < 70:
        return {"score": round((ratio-50)/20, 2), "level": "neutral", "desc": "震荡偏强"}
    else:
        return {"score": round(1 + (ratio-70)/30, 2), "level": "strong", "desc": "强势"}


def get_shanghai_summary() -> Dict:
    """上证指数详细"""
    try:
        import akshare as ak
        df = ak.stock_sh_index_spot_em()
        if df.empty:
            return {}
        row = df.iloc[0]
        return {
            "name": row.get("名称", "上证指数"),
            "code": row.get("代码", "000001"),
            "price": float(row.get("最新价", 0)),
            "change": float(row.get("涨跌额", 0)),
            "pct_change": float(row.get("涨跌幅", 0)),
            "amount": float(row.get("成交额", 0)),
        }
    except Exception:
        return {}


def get_amount_trend(days: int = 30) -> pd.DataFrame:
    """成交额趋势"""
    try:
        import akshare as ak
        df = ak.stock_market_activity_legu()
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date", ascending=False).head(days)
        return df.reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="market-data-collector")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("indices", help="主要指数")
    sub.add_parser("breadth", help="市场广度")
    sub.add_parser("strength", help="市场强度")
    sub.add_parser("shanghai", help="上证详细")
    p = sub.add_parser("kline", help="指数K线")
    p.add_argument("symbol")
    p.add_argument("--days", type=int, default=60)
    p = sub.add_parser("amount", help="成交额趋势")
    p.add_argument("--days", type=int, default=30)

    args = parser.parse_args()

    if args.cmd == "indices":
        df = get_major_indices()
        if not df.empty:
            cols = [c for c in ["code", "name", "price", "pct_change", "change"] if c in df.columns]
            print(df[cols].to_string())

    elif args.cmd == "breadth":
        b = get_market_breadth()
        if b:
            for k, v in b.items():
                print(f"  {k}: {v}")

    elif args.cmd == "strength":
        b = get_market_breadth()
        s = calc_market_strength(b)
        print(f"强度: {s['level']} (分数: {s['score']}, 描述: {s['desc']})")

    elif args.cmd == "shanghai":
        s = get_shanghai_summary()
        for k, v in s.items():
            print(f"  {k}: {v}")

    elif args.cmd == "kline":
        df = get_index_kline(args.symbol, args.days)
        if not df.empty:
            print(df.tail(args.days).to_string())

    elif args.cmd == "amount":
        df = get_amount_trend(args.days)
        if not df.empty:
            print(df.to_string())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
