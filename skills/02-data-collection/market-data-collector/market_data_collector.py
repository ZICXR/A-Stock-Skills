"""
market-data-collector: 大盘数据采集
====================================

功能:
    - 主要指数实时行情 (上证/深证/创业板/科创50/沪深300/中证500)
    - 指数历史K线
    - 市场情绪指标 (涨跌家数/成交量)
    - 实时成交概况
"""

import logging
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# 常用指数代码
MAJOR_INDICES = {
    "000001": "上证指数",
    "399001": "深证成指",
    "399006": "创业板指",
    "000688": "科创50",
    "000300": "沪深300",
    "000905": "中证500",
    "000852": "中证1000",
    "399905": "中证500(深)",
    "000016": "上证50",
}


# ============================================================
# 1. 实时行情
# ============================================================
def get_index_spot() -> pd.DataFrame:
    """获取主要指数实时行情"""
    try:
        import akshare as ak
        df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
    except Exception as e:
        logger.error(f"akshare 获取指数实时行情失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    rename_map = {"代码": "code", "名称": "name", "最新价": "price",
                  "涨跌幅": "pct_change", "涨跌额": "change",
                  "成交量": "volume", "成交额": "amount"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


def get_major_indices() -> pd.DataFrame:
    """获取常用主要指数"""
    df = get_index_spot()
    if df.empty or "code" not in df.columns:
        return df
    df["code"] = df["code"].astype(str)
    major_codes = list(MAJOR_INDICES.keys())
    return df[df["code"].isin(major_codes)].copy()


# ============================================================
# 2. 指数历史K线
# ============================================================
def get_index_hist(symbol: str, period: str = "daily",
                  start_date: str = "", end_date: str = "") -> pd.DataFrame:
    """获取指数历史K线
    Args:
        symbol: 6位指数代码, 如 000001
        period: daily/weekly/monthly
    """
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol=f"sh{symbol}" if symbol.startswith("000") else f"sz{symbol}")
    except Exception as e:
        logger.error(f"akshare 获取指数K线失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]

    return df.reset_index(drop=True)


# ============================================================
# 3. 大盘情绪
# ============================================================
def get_market_breadth() -> Dict:
    """市场广度: 上涨/下跌/平/停牌家数, 涨停/跌停数"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
    except Exception as e:
        logger.error(f"akshare 获取实时行情失败: {e}")
        return {}

    if df.empty:
        return {}

    rename_map = {"涨跌幅": "pct_change", "最新价": "price"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "pct_change" not in df.columns:
        return {}

    up = (df["pct_change"] > 0).sum()
    down = (df["pct_change"] < 0).sum()
    flat = (df["pct_change"] == 0).sum()
    limit_up = (df["pct_change"] >= 9.9).sum()
    limit_down = (df["pct_change"] <= -9.9).sum()

    return {
        "up": int(up),
        "down": int(down),
        "flat": int(flat),
        "limit_up": int(limit_up),
        "limit_down": int(limit_down),
        "total": int(len(df)),
        "up_ratio": round(up / len(df) * 100, 2) if len(df) else 0,
    }


# ============================================================
# 4. 市场强度评分
# ============================================================
def calc_market_strength(breadth: Dict) -> Dict:
    """根据市场广度计算强度评分
    评分规则:
        - 上涨比例 < 30%: 弱势 (-2 ~ -1)
        - 30-50%: 震荡 (-1 ~ 0)
        - 50-70%: 偏强 (0 ~ 1)
        - > 70%: 强势 (1 ~ 2)
    """
    if not breadth or "up_ratio" not in breadth:
        return {"score": 0, "level": "unknown", "desc": "数据不足"}

    ratio = breadth["up_ratio"]
    limit_up = breadth.get("limit_up", 0)
    limit_down = breadth.get("limit_down", 0)
    zt_ratio = (limit_up - limit_down) / max(breadth.get("total", 1), 1) * 100

    if ratio < 30:
        level, desc = "very_weak", "极度弱势"
        score = -2 + (ratio / 30)
    elif ratio < 50:
        level, desc = "weak", "弱势震荡"
        score = -1 + (ratio - 30) / 20
    elif ratio < 70:
        level, desc = "neutral", "震荡偏强"
        score = (ratio - 50) / 20
    else:
        level, desc = "strong", "强势"
        score = 1 + (ratio - 70) / 30

    score = max(-2, min(2, score + zt_ratio / 50))
    return {
        "score": round(float(score), 2),
        "level": level,
        "desc": desc,
    }


# ============================================================
# 5. 上证指数实时盘口
# ============================================================
def get_shanghai_summary() -> Dict:
    """上证指数详细盘口"""
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
            "volume": float(row.get("成交量", 0)),
            "amount": float(row.get("成交额", 0)),
        }
    except Exception as e:
        logger.error(f"获取上证指数失败: {e}")
        return {}


# ============================================================
# 6. 历史成交数据
# ============================================================
def get_market_amount_trend(days: int = 30) -> pd.DataFrame:
    """最近N日两市成交额趋势"""
    try:
        import akshare as ak
        df = ak.stock_market_activity_legu()
    except Exception as e:
        logger.error(f"获取市场活跃度失败: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date", ascending=False).head(days)
    return df.reset_index(drop=True)


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== 主要指数实时行情 ===")
    df = get_major_indices()
    if not df.empty:
        cols = [c for c in ["code", "name", "price", "pct_change", "change"] if c in df.columns]
        print(df[cols].to_string())

    print("\n=== 市场广度 ===")
    breadth = get_market_breadth()
    print(breadth)
    if breadth:
        strength = calc_market_strength(breadth)
        print("\n=== 市场强度 ===")
        print(strength)
