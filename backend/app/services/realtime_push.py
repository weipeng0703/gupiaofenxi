"""WebSocket 实时推送服务 — 后台定时拉取行情并推送"""
import asyncio
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import text

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
    即使无 WebSocket 连接，也会独立运行策略评估并推送微信通知。
    """

    def __init__(self):
        self._data_source = AKShareSource()
        self._strategy_engine = StrategyEngine()
        self._refresh_task: asyncio.Task | None = None
        self._subscribed_codes: set[str] = set()
        self._watchlist_codes: set[str] = set()
        self._watchlist_refresh_counter: int = 0

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
        """更新 WebSocket 订阅的股票代码集合"""
        self._subscribed_codes = codes

    def get_all_monitor_codes(self) -> set[str]:
        """获取所有需要监控的股票代码（WS 订阅 + 自选股列表）"""
        return self._subscribed_codes | self._watchlist_codes

    async def _load_watchlist_from_db(self):
        """从数据库加载活跃的自选股列表"""
        try:
            from app.database import async_session
            async with async_session() as session:
                result = await session.execute(
                    text("SELECT stock_code FROM watchlist WHERE is_active = 1")
                )
                codes = {row[0] for row in result.fetchall()}
                if codes != self._watchlist_codes:
                    logger.info(f"自选股列表更新: {len(codes)} 只 — {codes}")
                self._watchlist_codes = codes
        except Exception as e:
            logger.warning(f"加载自选股列表失败: {e}")

    async def _periodic_refresh(self):
        """定时刷新循环"""
        logger.info("实时推送服务启动")
        # 启动时立即加载自选股
        await self._load_watchlist_from_db()
        while True:
            try:
                # 每 20 个周期（约 5 分钟）刷新一次自选股列表
                self._watchlist_refresh_counter += 1
                if self._watchlist_refresh_counter >= 20:
                    self._watchlist_refresh_counter = 0
                    await self._load_watchlist_from_db()

                all_codes = self.get_all_monitor_codes()
                if all_codes:
                    await self._fetch_and_push(all_codes)
                else:
                    logger.debug("无监控股票，跳过刷新")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"刷新异常: {e}")

            await asyncio.sleep(settings.akshare_refresh_interval)

    async def _fetch_and_push(self, all_codes: set[str]):
        """拉取数据并推送"""
        codes = list(all_codes)

        # 1. 拉取实时行情
        quotes = await self._data_source.get_realtime_quotes_batch(codes)
        if not quotes:
            return

        # 2. 推送行情更新（只推送给有 WS 连接的）
        if self._subscribed_codes:
            quote_msg = make_quote_update(quotes)
            from app.ws.handler import manager
            await manager.broadcast(quote_msg, stock_codes=set(codes))

        # 3. 对每只股票计算指标和评估策略
        for quote in quotes:
            stock_code = quote["stock_code"]
            try:
                raw_kline = await self._data_source.get_hist_kline(
                    stock_code, period="daily",
                    start_date=None, end_date=None,
                )
                if not raw_kline:
                    continue

                df = pd.DataFrame(raw_kline)
                df = df.sort_values("date").reset_index(drop=True)
                indicators = IndicatorCalculator.compute_all(df)

                # 评估策略
                signals = self._strategy_engine.evaluate(
                    stock_code, indicators, raw_kline,
                )

                if signals:
                    logger.info(f"信号触发 {stock_code}: {[s['strategy_name'] for s in signals]}")

                # 推送新信号
                for signal in signals:
                    # WebSocket 推送
                    signal_msg = make_signal_alert(signal)
                    from app.ws.handler import manager
                    await manager.broadcast(signal_msg)

                    # 微信推送（独立于 WS 连接）
                    from app.services.wechat_notify import send_wechat_signal
                    await send_wechat_signal(signal)

            except Exception as e:
                logger.warning(f"策略评估异常 {stock_code}: {e}")


# 全局推送服务实例
push_service = RealtimePushService()