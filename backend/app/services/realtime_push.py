"""WebSocket 实时推送服务 — 后台定时拉取行情并推送"""
import asyncio
import logging
from datetime import datetime

import pandas as pd

from app.services.akshare_source import AKShareSource
from app.services.indicator_calc import IndicatorCalculator
from app.services.strategy_engine import StrategyEngine
from app.ws.protocol import make_quote_update, make_signal_alert
from app.config import settings

logger = logging.getLogger(__name__)


class RealtimePushService:
    """后台推送服务

    定时拉取自选股行情数据，计算指标，评估策略，
    通过 WebSocket 推送行情更新和买卖信号。
    """

    def __init__(self):
        self._data_source = AKShareSource()
        self._strategy_engine = StrategyEngine()
        self._refresh_task: asyncio.Task | None = None
        self._subscribed_codes: set[str] = set()

    def start(self):
        """启动后台推送循环"""
        if self._refresh_task is None:
            self._refresh_task = asyncio.create_task(self._periodic_refresh())

    def stop(self):
        """停止后台推送循环"""
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

    def update_subscriptions(self, codes: set[str]):
        """更新订阅的股票代码集合"""
        self._subscribed_codes = codes

    async def _periodic_refresh(self):
        """定时刷新循环"""
        logger.info("实时推送服务启动")
        while True:
            try:
                if self._subscribed_codes:
                    await self._fetch_and_push()
                else:
                    logger.debug("无订阅，跳过刷新")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"刷新异常: {e}")

            await asyncio.sleep(settings.akshare_refresh_interval)

    async def _fetch_and_push(self):
        """拉取数据并推送"""
        codes = list(self._subscribed_codes)

        # 1. 拉取实时行情
        quotes = await self._data_source.get_realtime_quotes_batch(codes)
        if not quotes:
            return

        # 2. 推送行情更新
        quote_msg = make_quote_update(quotes)
        from app.ws.handler import manager
        await manager.broadcast(quote_msg, stock_codes=set(codes))

        # 3. 对每只股票计算指标和评估策略
        for quote in quotes:
            stock_code = quote["stock_code"]
            try:
                # 获取最近历史数据用于指标计算
                raw_kline = await self._data_source.get_hist_kline(
                    stock_code, period="daily",
                    start_date=None, end_date=None,
                )
                if not raw_kline:
                    continue

                df = pd.DataFrame(raw_kline)
                df = df.sort_values("date").reset_index(drop=True)
                indicators = IndicatorCalculator.calculate_all(df)

                # 评估策略
                signals = self._strategy_engine.evaluate(
                    stock_code, indicators, raw_kline,
                )

                # 推送新信号
                for signal in signals:
                    signal_msg = make_signal_alert(signal)
                    from app.ws.handler import manager
                    await manager.broadcast(signal_msg)

                    # 微信推送
                    from app.services.wechat_notify import send_wechat_signal
                    await send_wechat_signal(signal)

            except Exception as e:
                logger.debug(f"策略评估异常 {stock_code}: {e}")


# 全局推送服务实例
push_service = RealtimePushService()