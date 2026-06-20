#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""portfolio-optimizer: 投资组合优化"""

import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


def get_returns(codes: List[str], days: int = 252) -> pd.DataFrame:
    """获取历史日收益率"""
    all_returns = {}
    for code in codes:
        try:
            import akshare as ak
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=int(days * 1.5))).strftime("%Y%m%d")
            df = ak.stock_zh_a_hist(symbol=str(code).zfill(6), period="daily",
                                     start_date=start, end_date=end, adjust="qfq")
            if df.empty:
                continue
            df.columns = [c.lower() for c in df.columns]
            if "close" in df.columns:
                rets = df["close"].pct_change().dropna().tail(days)
                all_returns[code] = rets.values
        except Exception as e:
            print(f"获取 {code} 失败: {e}", file=sys.stderr)
            continue
    if not all_returns:
        return pd.DataFrame()
    min_len = min(len(v) for v in all_returns.values())
    data = {k: v[-min_len:] for k, v in all_returns.items()}
    return pd.DataFrame(data)


def calc_mean_returns(returns: pd.DataFrame) -> np.ndarray:
    """平均年化收益"""
    return returns.mean() * 252


def calc_cov_matrix(returns: pd.DataFrame) -> np.ndarray:
    """协方差矩阵 (年化)"""
    return returns.cov() * 252


def port_stats(weights: np.ndarray, mean_ret: np.ndarray, cov: np.ndarray, rf: float = 0.03) -> Dict:
    """组合统计"""
    ret = float(np.dot(weights, mean_ret))
    vol = float(np.sqrt(weights @ cov @ weights))
    sharpe = (ret - rf) / vol if vol > 0 else 0
    return {"return": ret, "volatility": vol, "sharpe": sharpe}


def optimize_max_sharpe(mean_ret: np.ndarray, cov: np.ndarray, rf: float = 0.03) -> Dict:
    """最大化夏普"""
    from scipy.optimize import minimize
    n = len(mean_ret)

    def neg_sharpe(w):
        s = port_stats(w, mean_ret, cov, rf)
        return -s["sharpe"]

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = tuple((0, 1) for _ in range(n))
    w0 = np.array([1 / n] * n)

    result = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        return {"weights": w0, "stats": port_stats(w0, mean_ret, cov, rf)}
    return {"weights": result.x, "stats": port_stats(result.x, mean_ret, cov, rf)}


def optimize_min_vol(mean_ret: np.ndarray, cov: np.ndarray, rf: float = 0.03) -> Dict:
    """最小化波动率"""
    from scipy.optimize import minimize
    n = len(mean_ret)

    def port_vol(w):
        return float(np.sqrt(w @ cov @ w))

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = tuple((0, 1) for _ in range(n))
    w0 = np.array([1 / n] * n)

    result = minimize(port_vol, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        return {"weights": w0, "stats": port_stats(w0, mean_ret, cov, rf)}
    return {"weights": result.x, "stats": port_stats(result.x, mean_ret, cov, rf)}


def optimize_risk_parity(cov: np.ndarray) -> Dict:
    """风险平价 (等风险贡献)"""
    from scipy.optimize import minimize
    n = cov.shape[0]

    def risk_parity_obj(w):
        port_vol = np.sqrt(w @ cov @ w)
        marginal = cov @ w
        risk_contrib = w * marginal / port_vol
        # 目标: 所有风险贡献相等
        target = port_vol / n
        return float(np.sum((risk_contrib - target) ** 2))

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = tuple((0.01, 1) for _ in range(n))
    w0 = np.array([1 / n] * n)

    result = minimize(risk_parity_obj, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        return {"weights": w0, "stats": {}}
    mean_ret = np.zeros(n)  # 风险平价不需要预期收益
    return {"weights": result.x, "stats": port_stats(result.x, mean_ret, cov)}


def optimize_equal_weight(codes: List[str]) -> Dict:
    """等权重"""
    n = len(codes)
    w = np.array([1 / n] * n)
    return {"weights": w, "stats": {}}


def optimize_portfolio(method: str, returns: pd.DataFrame) -> Dict:
    """统一优化入口"""
    if returns.empty:
        return {}
    codes = list(returns.columns)
    mean_ret = calc_mean_returns(returns)
    cov = calc_cov_matrix(returns)

    if method == "max_sharpe":
        r = optimize_max_sharpe(mean_ret, cov)
    elif method == "min_volatility":
        r = optimize_min_vol(mean_ret, cov)
    elif method == "risk_parity":
        r = optimize_risk_parity(cov)
    elif method == "equal_weight":
        r = optimize_equal_weight(codes)
    else:
        return {"error": f"未知方法: {method}"}

    weights_dict = {code: round(float(w) * 100, 2) for code, w in zip(codes, r["weights"])}
    return {
        "method": method,
        "weights": weights_dict,
        "stats": r.get("stats", {}),
    }


def efficient_frontier(returns: pd.DataFrame, n_points: int = 20) -> List[Dict]:
    """有效前沿"""
    if returns.empty:
        return []
    codes = list(returns.columns)
    mean_ret = calc_mean_returns(returns)
    cov = calc_cov_matrix(returns)

    min_vol = optimize_min_vol(mean_ret, cov)
    max_sharpe = optimize_max_sharpe(mean_ret, cov)

    min_ret = port_stats(min_vol["weights"], mean_ret, cov)["return"]
    max_ret = port_stats(max_sharpe["weights"], mean_ret, cov)["return"]

    target_returns = np.linspace(min_ret, max_ret, n_points)
    from scipy.optimize import minimize

    frontier = []
    for target in target_returns:
        n = len(codes)

        def port_vol(w):
            return float(np.sqrt(w @ cov @ w))

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w: np.dot(w, mean_ret) - target},
        ]
        bounds = tuple((0, 1) for _ in range(n))
        w0 = np.array([1 / n] * n)
        result = minimize(port_vol, w0, method="SLSQP", bounds=bounds, constraints=constraints)
        if result.success:
            stats = port_stats(result.x, mean_ret, cov)
            frontier.append({
                "return": round(stats["return"] * 100, 2),
                "volatility": round(stats["volatility"] * 100, 2),
                "sharpe": round(stats["sharpe"], 2),
            })
    return frontier


def main():
    parser = argparse.ArgumentParser(description="portfolio-optimizer")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("optimize", help="优化")
    p.add_argument("--codes", required=True)
    p.add_argument("--method", default="max_sharpe",
                   choices=["max_sharpe", "min_volatility", "risk_parity", "equal_weight"])
    p.add_argument("--days", type=int, default=252)
    p = sub.add_parser("frontier", help="有效前沿")
    p.add_argument("--codes", required=True)
    p.add_argument("--n", type=int, default=20)
    args = parser.parse_args()

    if args.cmd in ("optimize", "frontier"):
        codes = [c.strip() for c in args.codes.split(",")]
        returns = get_returns(codes, days=args.days if hasattr(args, "days") else 252)
        if returns.empty:
            print("无法获取数据")
            return

    if args.cmd == "optimize":
        r = optimize_portfolio(args.method, returns)
        print(f"\n=== 组合优化 ({args.method}) ===\n")
        if "error" in r:
            print(r["error"])
            return
        print("代码      权重")
        for code, w in r.get("weights", {}).items():
            print(f"{code}    {w:6.2f}%")
        if r.get("stats"):
            s = r["stats"]
            print(f"\n预期年化收益: {s.get('return', 0)*100:.2f}%")
            print(f"预期波动率:   {s.get('volatility', 0)*100:.2f}%")
            print(f"夏普比率:     {s.get('sharpe', 0):.2f}")
    elif args.cmd == "frontier":
        f = efficient_frontier(returns, args.n)
        print("\n=== 有效前沿 ===")
        print("收益(%)    风险(%)    夏普")
        for pt in f:
            print(f"{pt['return']:6.2f}    {pt['volatility']:6.2f}    {pt['sharpe']:.2f}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
