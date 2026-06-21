"""AKShare 数据源实现 — A 股行情获取"""
import asyncio
import json
import os
import time
import logging
from datetime import datetime

import akshare as ak
import pandas as pd
from curl_cffi import requests as curl_requests

from app.services.data_source import DataSourceInterface
from app.config import settings

logger = logging.getLogger(__name__)

# AKShare period 参数映射
PERIOD_MAP = {
    "daily": "daily",
    "weekly": "weekly",
    "monthly": "monthly",
    "60min": "60",
    "30min": "30",
    "15min": "15",
    "5min": "5",
    "1min": "1",
}

# 腾讯财经 K 线 period 映射
TENCENT_PERIOD_MAP = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
}

# 预加载的股票列表（从 JSON 文件读取，搜索时优先使用）
_STOCK_LIST: list[dict] | None = None


def _load_stock_list() -> list[dict]:
    """从 JSON 文件加载股票列表"""
    global _STOCK_LIST
    if _STOCK_LIST is not None:
        return _STOCK_LIST

    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stock_list.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            _STOCK_LIST = json.load(f)
        logger.info(f"从 JSON 加载了 {len(_STOCK_LIST)} 只股票")
    except Exception as e:
        logger.warning(f"加载股票列表 JSON 失败: {e}")
        _STOCK_LIST = []
    return _STOCK_LIST


class AKShareSource(DataSourceInterface):
    """AKShare A 股数据源

    关键设计：
    - AKShare 是同步库，用 asyncio.to_thread() 包装避免阻塞事件循环
    - stock_zh_a_spot_em() 一次返回全部 A 股行情，效率极高
    - 内部限速机制，避免触发反爬
    - 清除代理环境变量，确保直接访问东方财富接口
    """

    def __init__(self):
        # 清除代理设置，确保 AKShare 直接访问东方财富（不走 VPN/代理）
        for proxy_var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]:
            os.environ.pop(proxy_var, None)
        logger.info("已清除代理环境变量，AKShare 将直接访问东方财富")

        self._last_realtime_call: float = 0.0
        self._realtime_lock = asyncio.Lock()
        self._spot_cache: pd.DataFrame | None = None
        self._spot_cache_time: float = 0.0

    async def get_hist_kline(
        self,
        stock_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
        adjust: str = "qfq",
    ) -> list[dict]:
        # 分钟级周期路由到专用接口
        if period in ("1min", "5min", "15min", "30min", "60min"):
            minute_period = PERIOD_MAP.get(period, "5")
            return await self.get_intraday_minutes(stock_code, minute_period, start_date, end_date, adjust)

        # 优先尝试 AKShare（东方财富接口）
        result = await self._get_hist_kline_akshare(stock_code, period, start_date, end_date, adjust)
        if result:
            return result

        # AKShare 失败时，用腾讯财经接口备用
        logger.info(f"AKShare 获取K线失败，切换到腾讯财经接口: {stock_code}")
        return await self._get_hist_kline_tencent(stock_code, period, start_date, end_date, adjust)

    async def _get_hist_kline_akshare(
        self, stock_code: str, period: str, start_date: str | None, end_date: str | None, adjust: str,
    ) -> list[dict]:
        """AKShare 方式获取 K 线（东方财富接口）"""
        ak_period = PERIOD_MAP.get(period, period)

        def _fetch():
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period=ak_period,
                start_date=start_date or "20200101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust,
            )
            return df

        try:
            df = await asyncio.to_thread(_fetch)
            df = self._normalize_hist_columns(df)
            return df.to_dict(orient="records")
        except Exception as e:
            logger.warning(f"AKShare 获取K线失败 {stock_code}: {e}")
            return []

    async def _get_hist_kline_tencent(
        self, stock_code: str, period: str, start_date: str | None, end_date: str | None, adjust: str,
    ) -> list[dict]:
        """腾讯财经备用接口获取 K 线数据（用 curl_cffi 模拟浏览器）"""
        # 确定市场前缀：0=深市，1=沪市
        market_prefix = "sz" if stock_code.startswith(("0", "3")) else "sh"
        tencent_period = TENCENT_PERIOD_MAP.get(period, "day")
        # qfq=前复权, hfq=后复权
        fq_type = "qfq" if adjust == "qfq" else ("hfq" if adjust == "hfq" else "")

        def _fetch():
            var_name = f"kline_{tencent_period}{fq_type}"
            url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {
                "_var": var_name,
                "param": f"{market_prefix}{stock_code},{tencent_period},,,320,{fq_type}",
            }
            r = curl_requests.get(url, params=params, impersonate="chrome110", timeout=15)
            if r.status_code != 200:
                return []

            text = r.text
            if "=" in text:
                json_str = text.split("=", 1)[1].strip()
            else:
                json_str = text

            import json as _json
            data = _json.loads(json_str)

            # 提取K线数据
            stock_data = data.get("data", {}).get(f"{market_prefix}{stock_code}", {})
            if isinstance(stock_data, dict):
                # day/qfqday/week/qfqweek 等
                key = tencent_period if not fq_type else f"{fq_type}{tencent_period}"
                klines_raw = stock_data.get(key, stock_data.get(tencent_period, []))
            else:
                klines_raw = []

            # 转换为标准格式
            # 腾讯格式: [date, open, close, high, low, volume]
            result = []
            for k in klines_raw:
                try:
                    result.append({
                        "date": k[0],
                        "open": float(k[1]),
                        "close": float(k[2]),
                        "high": float(k[3]),
                        "low": float(k[4]),
                        "volume": float(k[5]),
                        "amount": 0,
                    })
                except (IndexError, ValueError):
                    continue

            # 按日期范围过滤
            if start_date:
                result = [r for r in result if r["date"] >= start_date]
            if end_date:
                result = [r for r in result if r["date"] <= end_date]

            return result

        try:
            result = await asyncio.to_thread(_fetch)
            if result:
                logger.info(f"腾讯财经获取K线成功 {stock_code}: {len(result)}条")
            return result
        except Exception as e:
            logger.warning(f"腾讯财经获取K线失败 {stock_code}: {e}")
            return []

    async def get_realtime_quote(self, stock_code: str) -> dict | None:
        quotes = await self.get_realtime_quotes_batch([stock_code])
        return quotes[0] if quotes else None

    async def get_realtime_quotes_batch(self, stock_codes: list[str]) -> list[dict]:
        async with self._realtime_lock:
            now = time.monotonic()
            elapsed = now - self._last_realtime_call

            # 如果缓存仍在有效期内，直接使用缓存数据
            if self._spot_cache is not None and (now - self._spot_cache_time) < settings.akshare_refresh_interval:
                df = self._spot_cache
            else:
                # 限速：如果距离上次调用不足 refresh_interval，等待
                if elapsed < settings.akshare_refresh_interval and self._last_realtime_call > 0:
                    wait = settings.akshare_refresh_interval - elapsed
                    logger.debug(f"限速等待 {wait:.1f}s")
                    await asyncio.sleep(wait)

                def _fetch_spot():
                    return ak.stock_zh_a_spot_em()

                try:
                    df = await asyncio.to_thread(_fetch_spot)
                    self._spot_cache = df
                    self._spot_cache_time = time.monotonic()
                    self._last_realtime_call = time.monotonic()
                except Exception as e:
                    logger.warning(f"获取实时行情失败: {e}")
                    # 如果缓存还有数据，返回缓存
                    if self._spot_cache is not None:
                        df = self._spot_cache
                    else:
                        return []

        # 按股票代码筛选
        result = []
        for code in stock_codes:
            row = df[df["代码"] == code]
            if row.empty:
                continue
            row_data = row.iloc[0]
            result.append({
                "stock_code": code,
                "stock_name": str(row_data.get("名称", "")),
                "price": float(row_data.get("最新价", 0) or 0),
                "change_pct": float(row_data.get("涨跌幅", 0) or 0),
                "change_amt": float(row_data.get("涨跌额", 0) or 0),
                "volume": float(row_data.get("成交量", 0) or 0),
                "amount": float(row_data.get("成交额", 0) or 0),
                "amplitude": float(row_data.get("振幅", 0) or 0),
                "high": float(row_data.get("最高", 0) or 0),
                "low": float(row_data.get("最低", 0) or 0),
                "open": float(row_data.get("今开", 0) or 0),
                "prev_close": float(row_data.get("昨收", 0) or 0),
                "volume_ratio": float(row_data.get("量比", 0) or 0),
                "turnover_rate": float(row_data.get("换手率", 0) or 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        return result

    async def get_intraday_minutes(
        self,
        stock_code: str,
        period: str = "5",
        start_date: str | None = None,
        end_date: str | None = None,
        adjust: str = "qfq",
    ) -> list[dict]:
        def _fetch():
            df = ak.stock_zh_a_hist_min_em(
                symbol=stock_code,
                period=period,
                start_date=start_date or "2024-01-01 09:30:00",
                end_date=end_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                adjust=adjust,
            )
            return df

        try:
            df = await asyncio.to_thread(_fetch)
            df = self._normalize_hist_columns(df)
            return df.to_dict(orient="records")
        except Exception as e:
            logger.warning(f"获取分钟 K 线失败 {stock_code}: {e}")
            return []

    async def search_stock(self, keyword: str) -> list[dict]:
        """搜索股票 — 优先从本地 JSON 列表搜索，失败时再尝试 AKShare"""
        # 优先使用本地预加载的股票列表
        local_list = _load_stock_list()
        if local_list:
            keyword_lower = keyword.lower()
            results = []
            for stock in local_list:
                code = stock["stock_code"].lower()
                name = stock["stock_name"].lower()
                if keyword_lower in code or keyword_lower in name:
                    results.append(stock)
                    if len(results) >= 20:
                        break
            if results:
                return results

        # 本地列表无结果或加载失败，尝试 AKShare
        try:
            async with self._realtime_lock:
                if self._spot_cache is not None and (time.monotonic() - self._spot_cache_time) < 300:
                    df = self._spot_cache
                else:
                    def _fetch():
                        return ak.stock_zh_a_spot_em()
                    df = await asyncio.to_thread(_fetch)
                    self._spot_cache = df
                    self._spot_cache_time = time.monotonic()
                    self._last_realtime_call = time.monotonic()

            mask = df["代码"].str.contains(keyword, na=False) | df["名称"].str.contains(keyword, na=False)
            matches = df[mask].head(20)

            return [
                {
                    "stock_code": str(row["代码"]),
                    "stock_name": str(row["名称"]),
                    "market": "A",
                }
                for _, row in matches.iterrows()
            ]
        except Exception as e:
            logger.warning(f"搜索股票失败(AKShare): {e}")
            return []

    @staticmethod
    def _normalize_hist_columns(df: pd.DataFrame) -> pd.DataFrame:
        """将 AKShare 返回的中文列名映射为英文标准列名"""
        column_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "change_pct",
            "涨跌额": "change_amt",
            "换手率": "turnover",
        }
        # 只映射存在的列
        existing_map = {k: v for k, v in column_map.items() if k in df.columns}
        df = df.rename(columns=existing_map)
        return df