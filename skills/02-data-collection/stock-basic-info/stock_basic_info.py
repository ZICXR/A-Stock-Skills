"""
stock-basic-info: 个股基本信息采集
====================================

功能:
    - 股票基本信息 (代码/名称/行业/上市日期/总股本)
    - 公司概况
    - 主要股东
    - 主营业务
    - 财务数据快照
"""

import logging
import pandas as pd
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


# ============================================================
# 1. 个股基本信息
# ============================================================
def get_stock_info(symbol: str) -> Dict:
    """获取股票基本信息
    Args:
        symbol: 6位股票代码
    """
    try:
        import akshare as ak
        df = ak.stock_individual_info_em(symbol=symbol)
    except Exception as e:
        logger.error(f"akshare 获取股票信息失败: {e}")
        return {}

    if df.empty:
        return {}

    # 转成dict
    info = {}
    for _, row in df.iterrows():
        key = row.get("item", "")
        val = row.get("value", "")
        info[key] = val
    info["code"] = symbol
    return info


# ============================================================
# 2. 股票实时行情
# ============================================================
def get_stock_realtime(symbol: str) -> Dict:
    """个股实时行情快照"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"] == symbol]
        if target.empty:
            return {}
        row = target.iloc[0]
        return {
            "code": row.get("代码", symbol),
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
        logger.error(f"获取实时行情失败: {e}")
        return {}


# ============================================================
# 3. 主要股东
# ============================================================
def get_top_holders(symbol: str, top_n: int = 10) -> pd.DataFrame:
    """前十大股东
    Args:
        symbol: 6位股票代码
    """
    try:
        import akshare as ak
        df = ak.stock_main_holders_em(symbol=symbol)
    except Exception as e:
        logger.error(f"akshare 获取股东失败: {e}")
        try:
            import akshare as ak
            df = ak.stock_main_stock_holder(stock=symbol)
        except:
            return pd.DataFrame()

    if not df.empty and len(df) > top_n:
        df = df.head(top_n)
    return df


# ============================================================
# 4. 主营业务/产品
# ============================================================
def get_main_business(symbol: str) -> Dict:
    """主营业务构成"""
    try:
        import akshare as ak
        df = ak.stock_zyjs_ths(symbol=symbol)  # 同花顺主营业务
    except Exception as e:
        logger.error(f"获取主营业务失败: {e}")
        return {}

    if df.empty:
        return {"info": "暂无数据"}

    return {
        "主营构成": df.to_dict("records") if not df.empty else [],
        "data": df,
    }


# ============================================================
# 5. 财务报表快照
# ============================================================
def get_financial_summary(symbol: str) -> Dict:
    """财务摘要"""
    try:
        import akshare as ak
        df = ak.stock_financial_report_sina(stock=symbol, indicator="业绩快报")
    except Exception as e:
        logger.error(f"获取财务摘要失败: {e}")
        return {}

    return {
        "summary": df.to_dict("records") if not df.empty else [],
    }


# ============================================================
# 6. 完整信息卡
# ============================================================
def get_stock_card(symbol: str) -> Dict:
    """获取股票完整信息卡 (聚合所有信息)"""
    card = {
        "code": symbol,
        "basic": get_stock_info(symbol),
        "realtime": get_stock_realtime(symbol),
    }

    # 合并实时价格
    if card["realtime"] and card["basic"]:
        card["basic"]["最新价"] = card["realtime"].get("price")
        card["basic"]["涨跌幅"] = card["realtime"].get("pct_change")

    return card


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    code = "000001"
    print(f"=== {code} 实时行情 ===")
    rt = get_stock_realtime(code)
    for k, v in rt.items():
        print(f"  {k}: {v}")

    print(f"\n=== {code} 基本信息 ===")
    info = get_stock_info(code)
    for k, v in info.items():
        print(f"  {k}: {v}")

    print(f"\n=== {code} 前十大股东 ===")
    holders = get_top_holders(code)
    if not holders.empty:
        print(holders.head(10).to_string())
