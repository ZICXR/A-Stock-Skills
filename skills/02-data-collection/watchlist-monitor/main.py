#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watchlist-monitor: 自选股实时监控"""

import os
import sys
import json
import time
import argparse
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime


# ============================================================
# 配置加载
# ============================================================
DEFAULT_CONFIG_PATHS = [
    "./watchlist.yaml",
    "./watchlist.yml",
    "./watchlist.json",
    "~/.astock_skills/watchlist.yaml",
    "~/.astock_skills/watchlist.json",
]


def load_yaml(path: str) -> Dict:
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        print("需要安装 pyyaml: pip install pyyaml", file=sys.stderr)
        return {}


def load_json(path: str) -> Dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载 JSON 失败: {e}", file=sys.stderr)
        return {}


def load_watchlist(path: Optional[str] = None) -> Dict:
    """加载自选股配置"""
    if path:
        if not os.path.exists(path):
            print(f"配置文件不存在: {path}", file=sys.stderr)
            return {"stocks": [], "alerts": {}}
        if path.endswith((".yaml", ".yml")):
            return load_yaml(path)
        else:
            return load_json(path)

    # 自动查找默认配置
    for p in DEFAULT_CONFIG_PATHS:
        p = os.path.expanduser(p)
        if os.path.exists(p):
            print(f"使用配置: {p}", file=sys.stderr)
            if p.endswith((".yaml", ".yml")):
                return load_yaml(p)
            return load_json(p)

    print("未找到配置文件, 使用空配置", file=sys.stderr)
    return {"stocks": [], "alerts": {}}


def save_watchlist_template(path: str = "./watchlist.yaml"):
    """生成配置模板"""
    template = """# A股自选股监控配置
# 用法: python main.py monitor --config watchlist.yaml

# ============== 自选股列表 ==============
stocks:
  - code: "000001"
    name: "平安银行"
    cost: 12.50        # 持仓成本 (可选, 用于计算盈亏)
    shares: 1000       # 持仓数量 (可选)
    note: "银行龙头"   # 备注 (可选)
  - code: "600519"
    name: "贵州茅台"
  - code: "300750"
    name: "宁德时代"
  - code: "000858"
    name: "五粮液"

# ============== 告警阈值 ==============
alerts:
  # 涨跌幅告警 (%)
  pct_change_up: 5.0      # 涨幅超过此值告警
  pct_change_down: -3.0   # 跌幅超过此值告警

  # 价格告警 (元)
  price_above: 100        # 价格突破此值告警
  price_below: 50         # 价格跌破此值告警

  # 量能告警
  volume_ratio: 3.0       # 量比超过此值告警

  # 涨跌停告警
  limit_up: true          # 涨停提醒
  limit_down: true        # 跌停提醒

# ============== 数据源 (高级) ==============
# 留空则使用 akshare 本地
# source:
#   type: "ths"            # 同花顺
#   cookie: "your_cookie"  # 需要登录后从浏览器获取
#   # 或
#   type: "eastmoney"      # 东方财富
#   cookie: "your_cookie"
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"配置模板已生成: {path}")


# ============================================================
# 数据获取
# ============================================================
def get_realtime_quotes(codes: List[str], source_cookie: Optional[str] = None) -> List[Dict]:
    """批量获取实时行情"""
    quotes = []
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df.empty:
            return quotes
        df["代码"] = df["代码"].astype(str)
        for code in codes:
            code = str(code).zfill(6)
            target = df[df["代码"] == code]
            if target.empty:
                quotes.append({
                    "code": code, "name": "", "price": 0, "pct_change": 0,
                    "found": False,
                })
                continue
            row = target.iloc[0]
            quotes.append({
                "code": code,
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
                "pe": row.get("市盈率-动态"),
                "pb": row.get("市净率"),
                "total_mv": float(row.get("总市值", 0)),
                "circ_mv": float(row.get("流通市值", 0)),
                "found": True,
            })
    except Exception as e:
        print(f"获取行情失败: {e}", file=sys.stderr)
    return quotes


def get_volume_ratio(code: str) -> float:
    """获取量比 (简化: 当日成交量/5日均量)"""
    try:
        import akshare as ak
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=20)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=str(code).zfill(6), period="daily",
                                 start_date=start, end_date=end, adjust="qfq")
        if df.empty or len(df) < 6:
            return 1.0
        df.columns = [c.lower() for c in df.columns]
        if "volume" in df.columns:
            today_vol = float(df["volume"].iloc[-1])
            avg_5 = float(df["volume"].tail(5).mean())
            if avg_5 > 0:
                return round(today_vol / avg_5, 2)
        return 1.0
    except Exception:
        return 1.0


# ============================================================
# 告警检查
# ============================================================
def check_alerts(quotes: List[Dict], alerts: Dict, stock_configs: List[Dict]) -> List[Dict]:
    """检查告警"""
    triggered = []
    cost_map = {s["code"]: s for s in stock_configs if "code" in s}

    for q in quotes:
        if not q.get("found"):
            continue
        code = q["code"]
        price = q.get("price", 0)
        pct = q.get("pct_change", 0)

        # 涨幅告警
        if "pct_change_up" in alerts and pct >= alerts["pct_change_up"]:
            triggered.append({
                "code": code, "name": q["name"], "type": "pct_change_up",
                "value": pct, "message": f"涨幅 {pct:+.2f}%, 超过阈值 {alerts['pct_change_up']}%"
            })
        # 跌幅告警
        if "pct_change_down" in alerts and pct <= alerts["pct_change_down"]:
            triggered.append({
                "code": code, "name": q["name"], "type": "pct_change_down",
                "value": pct, "message": f"跌幅 {pct:+.2f}%, 超过阈值 {alerts['pct_change_down']}%"
            })
        # 价格上限
        if "price_above" in alerts and price >= alerts["price_above"]:
            triggered.append({
                "code": code, "name": q["name"], "type": "price_above",
                "value": price, "message": f"价格 {price}, 突破 {alerts['price_above']}"
            })
        # 价格下限
        if "price_below" in alerts and price <= alerts["price_below"]:
            triggered.append({
                "code": code, "name": q["name"], "type": "price_below",
                "value": price, "message": f"价格 {price}, 跌破 {alerts['price_below']}"
            })
        # 涨停
        if alerts.get("limit_up") and pct >= 9.9:
            triggered.append({
                "code": code, "name": q["name"], "type": "limit_up",
                "value": pct, "message": f"涨停! +{pct:.2f}%"
            })
        # 跌停
        if alerts.get("limit_down") and pct <= -9.9:
            triggered.append({
                "code": code, "name": q["name"], "type": "limit_down",
                "value": pct, "message": f"跌停! {pct:.2f}%"
            })

    return triggered


# ============================================================
# 显示
# ============================================================
def print_quotes(quotes: List[Dict], stock_configs: List[Dict]):
    """打印行情"""
    cost_map = {s["code"]: s for s in stock_configs if "code" in s}
    print(f"\n📊 自选股监控 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 70)
    for q in quotes:
        if not q.get("found"):
            print(f"❌ {q['code']:<8} 未找到")
            continue
        pct = q.get("pct_change", 0)
        icon = "🔺" if pct > 0 else "🔻" if pct < 0 else "➖"
        cost_str = ""
        cfg = cost_map.get(q["code"])
        if cfg and "cost" in cfg:
            profit = (q["price"] - cfg["cost"]) * cfg.get("shares", 0)
            profit_pct = (q["price"] - cfg["cost"]) / cfg["cost"] * 100
            cost_str = f"  盈亏: {profit:+,.0f} ({profit_pct:+.2f}%)"
        print(f"{icon} {q['code']:<6} {q['name']:<8} {q['price']:>8.2f}  {pct:+6.2f}%{cost_str}")
    print("=" * 70)


def print_alerts(alerts: List[Dict]):
    """打印告警"""
    if not alerts:
        print("\n✅ 无告警")
        return
    print(f"\n🚨 触发告警 {len(alerts)} 条:")
    for a in alerts:
        print(f"  [{a['type']}] {a['code']} {a['name']}: {a['message']}")


# ============================================================
# 监控主循环
# ============================================================
def monitor_once(config_path: Optional[str] = None) -> Dict:
    """单次监控"""
    config = load_watchlist(config_path)
    stocks = config.get("stocks", [])
    alert_cfg = config.get("alerts", {})
    source = config.get("source", {})

    if not stocks:
        print("自选股为空, 请先配置 watchlist.yaml", file=sys.stderr)
        return {}

    codes = [s["code"] for s in stocks]
    quotes = get_realtime_quotes(codes, source.get("cookie"))
    print_quotes(quotes, stocks)

    alerts = check_alerts(quotes, alert_cfg, stocks)
    print_alerts(alerts)

    return {"quotes": quotes, "alerts": alerts}


def monitor_loop(config_path: Optional[str] = None, interval: int = 30):
    """持续监控"""
    print(f"⏰ 持续监控, 间隔 {interval} 秒, Ctrl+C 停止")
    try:
        while True:
            monitor_once(config_path)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n已停止监控")


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="watchlist-monitor")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("monitor", help="单次监控")
    p.add_argument("--config", help="配置文件路径")
    p.add_argument("--codes", help="股票代码, 逗号分隔")

    p = sub.add_parser("loop", help="持续监控")
    p.add_argument("--config")
    p.add_argument("--interval", type=int, default=30)

    p = sub.add_parser("init", help="生成配置模板")
    p.add_argument("--path", default="./watchlist.yaml")

    p = sub.add_parser("alerts", help="仅检查告警")
    p.add_argument("--config")

    args = parser.parse_args()

    if args.cmd == "init":
        save_watchlist_template(args.path)
    elif args.cmd == "monitor":
        if args.codes:
            codes = [c.strip() for c in args.codes.split(",")]
            quotes = get_realtime_quotes(codes)
            print_quotes(quotes, [{"code": c} for c in codes])
        else:
            monitor_once(args.config)
    elif args.cmd == "loop":
        monitor_loop(args.config, args.interval)
    elif args.cmd == "alerts":
        r = monitor_once(args.config)
        # monitor_once 已打印告警
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
