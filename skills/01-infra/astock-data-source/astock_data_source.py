"""
astock-data-source: A股多源数据源统一管理
===========================================

功能:
    - 统一封装 akshare / tushare / 东方财富 三大数据源
    - 自动降级与重试机制
    - 统一的接口规范
    - 限流控制

作者: A-Stock-Skills Team
版本: 1.0.0
"""

import os
import time
import json
import logging
from functools import wraps
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================
# 全局配置
# ============================================================
DATA_SOURCES = ["akshare", "tushare", "eastmoney"]
DEFAULT_SOURCE = "akshare"
CACHE_DIR = os.path.expanduser("~/.astock_skills/cache")
os.makedirs(CACHE_DIR, exist_ok=True)


# ============================================================
# 装饰器: 重试 + 限流
# ============================================================
def with_retry(max_retries: int = 3, delay: float = 1.0):
    """请求失败自动重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    logger.warning(f"[{func.__name__}] 第{i+1}次重试, 错误: {e}")
                    time.sleep(delay * (i + 1))
            raise RuntimeError(f"[{func.__name__}] 重试{max_retries}次仍失败: {last_err}")
        return wrapper
    return decorator


def with_rate_limit(calls_per_second: float = 2.0):
    """限流装饰器"""
    min_interval = 1.0 / calls_per_second
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


# ============================================================
# 数据源客户端封装
# ============================================================
class AkShareClient:
    """AkShare 数据源封装 (免费、稳定、覆盖全)"""

    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
        except ImportError:
            logger.warning("akshare 未安装: pip install akshare")
            self.available = False

    @with_retry()
    @with_rate_limit(2.0)
    def stock_zh_a_spot(self) -> pd.DataFrame:
        """全A股实时行情"""
        return self.ak.stock_zh_a_spot_em()

    @with_retry()
    @with_rate_limit(2.0)
    def stock_zh_a_hist(self, symbol: str, period: str = "daily",
                        start_date: str = "", end_date: str = "",
                        adjust: str = "qfq") -> pd.DataFrame:
        """A股历史K线
        Args:
            symbol: 6位股票代码 (如 000001)
            period: daily/weekly/monthly
            adjust: qfq前复权/hfq后复权/不复权
        """
        return self.ak.stock_zh_a_hist(
            symbol=symbol, period=period,
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust=adjust
        )

    @with_retry()
    @with_rate_limit(2.0)
    def stock_news_em(self, symbol: str) -> pd.DataFrame:
        """东方财富个股新闻"""
        return self.ak.stock_news_em(symbol=symbol)

    @with_retry()
    @with_rate_limit(1.0)
    def stock_announcement_report(self, symbol: str) -> pd.DataFrame:
        """个股公告"""
        return self.ak.stock_announcement_report(symbol=symbol)

    @with_retry()
    @with_rate_limit(1.0)
    def sector_flow(self) -> pd.DataFrame:
        """板块资金流"""
        return self.ak.stock_sector_fund_flow_rank()

    @with_retry()
    @with_rate_limit(1.0)
    def stock_individual_fund_flow(self, stock: str, market: str = "sh") -> pd.DataFrame:
        """个股资金流"""
        return self.ak.stock_individual_fund_flow(stock=stock, market=market)

    @with_retry()
    @with_rate_limit(1.0)
    def stock_lhb_detail_em(self, start_date: str, end_date: str) -> pd.DataFrame:
        """龙虎榜"""
        return self.ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)

    @with_retry()
    @with_rate_limit(1.0)
    def stock_zt_pool_em(self, date: str) -> pd.DataFrame:
        """涨停板池"""
        return self.ak.stock_zt_pool_em(date=date)


class TushareClient:
    """Tushare Pro 数据源 (数据质量高, 需要token)"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("TUSHARE_TOKEN")
        if not self.token:
            logger.warning("Tushare Token 未配置, 数据源不可用")
            self.available = False
            return
        try:
            import tushare as ts
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            self.available = True
        except ImportError:
            logger.warning("tushare 未安装: pip install tushare")
            self.available = False

    @with_retry()
    @with_rate_limit(5.0)  # tushare 限流更严
    def daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """日线行情"""
        return self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

    @with_retry()
    @with_rate_limit(2.0)
    def stock_basic(self, list_status: str = "L") -> pd.DataFrame:
        """股票基本信息"""
        return self.pro.stock_basic(list_status=list_status)

    @with_retry()
    @with_rate_limit(2.0)
    def index_daily(self, ts_code: str, start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """指数日线"""
        return self.pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

    @with_retry()
    @with_rate_limit(2.0)
    def fina_indicator(self, ts_code: str, period: str = "") -> pd.DataFrame:
        """财务指标"""
        return self.pro.fina_indicator(ts_code=ts_code, period=period)

    @with_retry()
    @with_rate_limit(2.0)
    def top_list(self, trade_date: str) -> pd.DataFrame:
        """龙虎榜"""
        return self.pro.top_list(trade_date=trade_date)


class EastMoneyClient:
    """东方财富直连 (备选)"""

    def __init__(self):
        try:
            import requests
            self.requests = requests
            self.available = True
        except ImportError:
            self.available = False

    @with_retry()
    @with_rate_limit(3.0)
    def get_realtime(self, secid: str) -> Dict:
        """东财实时行情直连
        Args:
            secid: 格式如 1.600000 (1=沪, 0=深)
        """
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": secid,
            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170,f171",
        }
        r = self.requests.get(url, params=params, timeout=10)
        return r.json()


# ============================================================
# 统一调度器
# ============================================================
class DataSourceManager:
    """数据源统一管理器: 自动选择/降级/缓存"""

    def __init__(self, tushare_token: Optional[str] = None, primary: str = DEFAULT_SOURCE):
        self.primary = primary
        self.akshare = AkShareClient()
        self.tushare = TushareClient(token=tushare_token)
        self.eastmoney = EastMoneyClient()

        self._cache: Dict[str, Any] = {}
        self._cache_expire: Dict[str, float] = {}

    def _cache_get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if time.time() < self._cache_expire.get(key, 0):
                return self._cache[key]
            else:
                self._cache.pop(key, None)
        return None

    def _cache_set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        self._cache_expire[key] = time.time() + ttl

    def call(self, source: str, method: str, *args, **kwargs) -> Any:
        """统一调用入口
        Args:
            source: akshare/tushare/eastmoney
            method: 方法名
        """
        cache_key = f"{source}:{method}:{args}:{kwargs}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        client = getattr(self, source, None)
        if not client or not client.available:
            logger.warning(f"数据源 {source} 不可用, 尝试降级")
            return self._fallback(source, method, *args, **kwargs)

        func = getattr(client, method, None)
        if not func:
            raise AttributeError(f"{source} 没有方法 {method}")

        result = func(*args, **kwargs)
        self._cache_set(cache_key, result)
        return result

    def _fallback(self, primary: str, method: str, *args, **kwargs):
        """数据源降级"""
        order = [s for s in DATA_SOURCES if s != primary]
        for src in order:
            client = getattr(self, src, None)
            if not client or not client.available:
                continue
            func = getattr(client, method, None)
            if not func:
                continue
            try:
                logger.info(f"降级到数据源: {src}")
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"数据源 {src} 调用失败: {e}")
                continue
        raise RuntimeError(f"所有数据源均不可用, 方法: {method}")


# ============================================================
# 便捷函数
# ============================================================
_manager: Optional[DataSourceManager] = None

def get_manager(tushare_token: Optional[str] = None) -> DataSourceManager:
    """获取全局数据源管理器"""
    global _manager
    if _manager is None:
        _manager = DataSourceManager(tushare_token=tushare_token)
    return _manager


def health_check() -> Dict[str, bool]:
    """健康检查: 各数据源是否可用"""
    m = get_manager()
    return {
        "akshare": m.akshare.available,
        "tushare": m.tushare.available,
        "eastmoney": m.eastmoney.available,
    }


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    print("=== astock-data-source 健康检查 ===")
    status = health_check()
    for src, ok in status.items():
        print(f"  {src}: {'✅' if ok else '❌'}")

    if status.get("akshare"):
        m = get_manager()
        print("\n=== 测试: 获取实时行情前5条 ===")
        df = m.akshare.stock_zh_a_spot()
        print(df.head())
        print(f"\n共 {len(df)} 只股票")
