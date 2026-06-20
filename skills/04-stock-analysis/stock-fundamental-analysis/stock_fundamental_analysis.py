"""
stock-fundamental-analysis: 个股基本面分析
==========================================

功能:
    - 财务指标 (ROE/ROA/毛利率/净利率)
    - 成长性分析 (营收/利润增长率)
    - 估值分析 (PE/PB/PEG/历史分位)
    - 财务健康度 (资产负债率/现金流)
    - 杜邦分析
    - 综合基本面评分
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

import sys
sys.path.insert(0, "skills/01-infra")
from astock_utils.astock_utils import normalize_stock_code

logger = logging.getLogger(__name__)


# ============================================================
# 1. 财务指标
# ============================================================
def get_financial_indicator(symbol: str) -> pd.DataFrame:
    """获取主要财务指标
    Args:
        symbol: 6位股票代码
    """
    try:
        import akshare as ak
        df = ak.stock_financial_abstract_ths(symbol=symbol)
    except Exception as e:
        try:
            import akshare as ak
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
        except:
            return pd.DataFrame()

    return df


# ============================================================
# 2. 业绩快报
# ============================================================
def get_performance_express(symbol: str) -> pd.DataFrame:
    """业绩快报"""
    try:
        import akshare as ak
        df = ak.stock_yjkb_em(symbol=symbol)
    except Exception as e:
        return pd.DataFrame()

    return df


# ============================================================
# 3. ROE / ROA 分析
# ============================================================
def analyze_profitability(fin_df: pd.DataFrame) -> Dict:
    """盈利能力分析"""
    if fin_df.empty:
        return {}

    result = {
        "roe": {},  # 净资产收益率
        "roa": {},  # 总资产收益率
        "gross_margin": {},  # 毛利率
        "net_margin": {},  # 净利率
    }

    # 尝试提取关键指标
    for _, row in fin_df.iterrows():
        period = str(row.get("日期", row.get("报告期", "")))
        if not period:
            continue
        for col in row.index:
            val = row.get(col)
            if pd.isna(val):
                continue
            col_str = str(col)
            if "ROE" in col_str or "净资产收益率" in col_str:
                result["roe"][period] = float(val) if val else None
            elif "ROA" in col_str or "总资产收益率" in col_str:
                result["roa"][period] = float(val) if val else None
            elif "毛利率" in col_str:
                result["gross_margin"][period] = float(val) if val else None
            elif "净利率" in col_str:
                result["net_margin"][period] = float(val) if val else None

    return result


# ============================================================
# 4. 成长性分析
# ============================================================
def analyze_growth(fin_df: pd.DataFrame) -> Dict:
    """成长性分析"""
    if fin_df.empty:
        return {}

    result = {
        "revenue_growth": {},
        "profit_growth": {},
        "eps_growth": {},
    }

    for _, row in fin_df.iterrows():
        period = str(row.get("日期", row.get("报告期", "")))
        if not period:
            continue
        for col in row.index:
            val = row.get(col)
            if pd.isna(val):
                continue
            col_str = str(col)
            if "营业总收入" in col_str and "增长" in col_str:
                result["revenue_growth"][period] = float(val) if val else None
            elif "净利润" in col_str and "增长" in col_str:
                result["profit_growth"][period] = float(val) if val else None
            elif "每股收益" in col_str and "增长" in col_str:
                result["eps_growth"][period] = float(val) if val else None

    return result


# ============================================================
# 5. 估值分析
# ============================================================
def analyze_valuation(symbol: str) -> Dict:
    """估值分析
    Returns:
        {
            "pe_ttm": ...,
            "pb": ...,
            "ps_ttm": ...,
            "history_pe": [...],  # 历史PE
            "current_percentile": ...  # 当前分位
        }
    """
    result = {}

    # 实时估值
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        target = df[df["代码"] == symbol]
        if not target.empty:
            row = target.iloc[0]
            result["pe_ttm"] = float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else None
            result["pe_static"] = float(row.get("市盈率", 0)) if row.get("市盈率") else None
            result["pb"] = float(row.get("市净率", 0)) if row.get("市净率") else None
            result["ps_ttm"] = float(row.get("市销率", 0)) if row.get("市销率") else None
    except Exception as e:
        logger.error(f"获取估值失败: {e}")

    # 历史PE分位
    try:
        import akshare as ak
        end = pd.Timestamp.now().strftime("%Y%m%d")
        start = (pd.Timestamp.now() - pd.Timedelta(days=365 * 3)).strftime("%Y%m%d")
        hist_df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                     start_date=start, end_date=end, adjust="qfq")
        # 简化处理: 不做完整历史PE计算
        result["history_note"] = "历史PE需要历史财务数据, 请使用专业数据源"
    except:
        pass

    # PEG
    pe = result.get("pe_ttm", 0) or 0
    # PEG = PE / 净利润增长率
    # 需要净利润增长率数据, 简化处理

    return result


# ============================================================
# 6. 财务健康度
# ============================================================
def analyze_financial_health(fin_df: pd.DataFrame) -> Dict:
    """财务健康度"""
    if fin_df.empty:
        return {}

    health_score = 0
    issues = []

    # 资产负债率
    for _, row in fin_df.iterrows():
        for col in row.index:
            val = row.get(col)
            if pd.isna(val):
                continue
            col_str = str(col)
            if "资产负债率" in col_str:
                v = float(val) if val else 0
                if v > 70:
                    issues.append(f"资产负债率过高: {v:.1f}%")
                    health_score -= 1
                elif v < 30:
                    health_score += 1
            elif "流动比率" in col_str:
                v = float(val) if val else 0
                if v < 1:
                    issues.append(f"流动比率过低: {v:.2f}")
                    health_score -= 1

    return {
        "score": health_score,
        "issues": issues,
        "level": "健康" if health_score > 0 else "需关注" if health_score < 0 else "中性",
    }


# ============================================================
# 7. 综合基本面评分
# ============================================================
def full_fundamental_analysis(symbol: str) -> Dict:
    """综合基本面分析
    评分维度:
        - 盈利能力 (ROE/ROA/毛利率)
        - 成长性 (营收增长/利润增长)
        - 估值 (PE/PB)
        - 财务健康度
    """
    fin_df = get_financial_indicator(symbol)
    profitability = analyze_profitability(fin_df)
    growth = analyze_growth(fin_df)
    valuation = analyze_valuation(symbol)
    health = analyze_financial_health(fin_df)

    # 综合评分
    score = 0
    max_score = 0

    # 盈利
    if profitability.get("roe"):
        latest_roe = list(profitability["roe"].values())[0] if profitability["roe"] else 0
        if latest_roe > 15:
            score += 2
        elif latest_roe > 10:
            score += 1
        max_score += 2

    # 增长
    if growth.get("revenue_growth"):
        latest_rg = list(growth["revenue_growth"].values())[0] if growth["revenue_growth"] else 0
        if latest_rg > 30:
            score += 2
        elif latest_rg > 15:
            score += 1
        max_score += 2

    if growth.get("profit_growth"):
        latest_pg = list(growth["profit_growth"].values())[0] if growth["profit_growth"] else 0
        if latest_pg > 30:
            score += 2
        elif latest_pg > 15:
            score += 1
        max_score += 2

    # 估值
    pe = valuation.get("pe_ttm") or 0
    if 0 < pe < 20:
        score += 2
    elif 0 < pe < 40:
        score += 1
    max_score += 2

    pb = valuation.get("pb") or 0
    if 0 < pb < 2:
        score += 1
    max_score += 1

    # 健康度
    score += health.get("score", 0)
    max_score += 3

    final_score = (score / max(max_score, 1)) * 100

    if final_score >= 70:
        rating = "优"
    elif final_score >= 50:
        rating = "良"
    elif final_score >= 30:
        rating = "中"
    else:
        rating = "差"

    return {
        "symbol": symbol,
        "profitability": profitability,
        "growth": growth,
        "valuation": valuation,
        "health": health,
        "score": round(final_score, 2),
        "rating": rating,
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    symbol = "000001"
    print(f"=== {symbol} 基本面分析 ===")
    result = full_fundamental_analysis(symbol)
    if result:
        print(f"\n综合评分: {result['score']} ({result['rating']})")

        print(f"\n【盈利能力】")
        for k, v in result['profitability'].items():
            if v:
                print(f"  {k}: {v}")

        print(f"\n【成长性】")
        for k, v in result['growth'].items():
            if v:
                print(f"  {k}: {v}")

        print(f"\n【估值】")
        for k, v in result['valuation'].items():
            if v is not None:
                print(f"  {k}: {v}")

        print(f"\n【财务健康】 {result['health'].get('level')}")
        if result['health'].get('issues'):
            for issue in result['health']['issues']:
                print(f"  - {issue}")
