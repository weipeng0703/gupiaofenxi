"""测试 push_service 独立于 WebSocket 运行策略评估

验证核心修复：即使没有 WebSocket 连接，push_service 也能
从数据库加载自选股列表，独立运行策略评估，触发微信通知。
"""
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestPushServiceWatchlistLoading:
    """验证 push_service 独立于 WS 连接加载自选股"""

    def test_get_all_monitor_codes_merges_ws_and_watchlist(self):
        """get_all_monitor_codes 应合并 WS 订阅和自选股列表"""
        from app.services.realtime_push import RealtimePushService
        svc = RealtimePushService()
        svc._subscribed_codes = {"000001", "600000"}
        svc._watchlist_codes = {"600000", "000002"}

        codes = svc.get_all_monitor_codes()
        assert codes == {"000001", "600000", "000002"}

    def test_watchlist_codes_used_without_ws(self):
        """没有 WS 连接时，仅用自选股列表也能工作"""
        from app.services.realtime_push import RealtimePushService
        svc = RealtimePushService()
        svc._subscribed_codes = set()
        svc._watchlist_codes = {"000001", "000002"}

        codes = svc.get_all_monitor_codes()
        assert codes == {"000001", "000002"}

    @pytest.mark.asyncio
    async def test_load_watchlist_from_db(self):
        """_load_watchlist_from_db 应正确从数据库查询活跃自选股"""
        from app.services.realtime_push import RealtimePushService
        svc = RealtimePushService()

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("000001",), ("600036",), ("300750",)]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.database.async_session", return_value=mock_session):
            await svc._load_watchlist_from_db()

        assert svc._watchlist_codes == {"000001", "600036", "300750"}


class TestPushServiceFetchAndPush:
    """验证 _fetch_and_push 正确处理所有监控代码"""

    @pytest.mark.asyncio
    async def test_fetch_and_push_evaluates_all_codes(self):
        """_fetch_and_push 应对所有传入的代码评估策略"""
        from app.services.realtime_push import RealtimePushService
        svc = RealtimePushService()

        mock_quotes = [
            {"stock_code": "000001", "price": 10.0},
            {"stock_code": "600036", "price": 35.0},
        ]

        evaluated_codes = []

        async def mock_get_quotes(codes):
            return mock_quotes

        async def mock_get_hist(code, **kwargs):
            evaluated_codes.append(code)
            return None  # 返回 None 跳过后续处理

        svc._data_source.get_realtime_quotes_batch = mock_get_quotes
        svc._data_source.get_hist_kline = mock_get_hist

        await svc._fetch_and_push({"000001", "600036"})

        assert "000001" in evaluated_codes
        assert "600036" in evaluated_codes

    @pytest.mark.asyncio
    async def test_wechat_push_called_when_signal_generated(self):
        """策略触发信号后应调用微信推送（无需 WS 连接）"""
        from app.services.realtime_push import RealtimePushService
        import app.services.wechat_notify as wn
        wn._recent_signals.clear()

        svc = RealtimePushService()
        svc._subscribed_codes = set()  # 无 WS 连接

        mock_quotes = [{"stock_code": "000001", "price": 10.0}]

        # 构造会触发 RSI 超卖信号的 K 线数据
        kline_data = []
        for i in range(60):
            kline_data.append({
                "date": f"2025-01-{i+1:02d}" if i < 28 else f"2025-02-{i-27:02d}",
                "open": 10.0, "close": 10.0,
                "high": 10.5, "low": 9.5,
                "volume": 10000, "amount": 100000,
            })

        async def mock_get_quotes(codes):
            return mock_quotes

        async def mock_get_hist(code, **kwargs):
            return kline_data

        svc._data_source.get_realtime_quotes_batch = mock_get_quotes
        svc._data_source.get_hist_kline = mock_get_hist

        # Mock 策略引擎直接返回信号
        mock_signal = {
            "stock_code": "000001",
            "strategy_name": "RSI超卖低吸",
            "signal_type": "BUY",
            "confidence": 0.8,
            "price": 10.0,
            "timestamp": "2025-02-01",
            "indicator_values": {"rsi": 15.0},
        }
        svc._strategy_engine.evaluate = MagicMock(return_value=[mock_signal])

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}

        with patch("app.services.wechat_notify.settings") as mock_settings, \
             patch("app.services.wechat_notify.curl_requests") as mock_curl:
            mock_settings.wechat_webhook_url = "https://qyapi.weixin.qq.com/test"
            mock_curl.post.return_value = mock_resp

            await svc._fetch_and_push({"000001"})

            # 验证微信推送被调用了
            assert mock_curl.post.called, "微信推送应被调用"
            call_kwargs = mock_curl.post.call_args
            payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
            assert "RSI超卖低吸" in str(payload)


class TestStrategyThresholdUpdate:
    """验证 RSI 阈值已从 20/80 调整为 30/70"""

    def test_rsi_value_25_triggers_buy(self):
        """RSI=25 应触发买入（旧阈值 20 不会触发，新阈值 30 会触发）"""
        from app.services.strategy_engine import StrategyEngine
        engine = StrategyEngine()

        n = 60
        indicators = {
            "ma": {"MA5": [10.0]*n, "MA10": [10.0]*n, "MA20": [10.0]*n, "MA60": [10.0]*n},
            "rsi": {"RSI6": [50.0]*n, "RSI12": [50.0]*n, "RSI14": [25.0]*n, "RSI24": [50.0]*n},
            "kdj": {"K": [50.0]*n, "D": [50.0]*n, "J": [50.0]*n},
        }
        kline = [{"date": "2025-01-01", "close": 10.0, "high": 10.5, "low": 9.5,
                  "open": 10.0, "volume": 10000, "amount": 100000}] * n

        signals = engine.evaluate("000001", indicators, kline)
        buy_signals = [s for s in signals if s["strategy_name"] == "RSI超卖低吸"]
        assert len(buy_signals) > 0, "RSI=25 应触发超卖低吸（阈值 30）"

    def test_rsi_value_75_triggers_sell(self):
        """RSI=75 应触发卖出（旧阈值 80 不会触发，新阈值 70 会触发）"""
        from app.services.strategy_engine import StrategyEngine
        engine = StrategyEngine()

        n = 60
        indicators = {
            "ma": {"MA5": [10.0]*n, "MA10": [10.0]*n, "MA20": [10.0]*n, "MA60": [10.0]*n},
            "rsi": {"RSI6": [50.0]*n, "RSI12": [50.0]*n, "RSI14": [75.0]*n, "RSI24": [50.0]*n},
            "kdj": {"K": [50.0]*n, "D": [50.0]*n, "J": [50.0]*n},
        }
        kline = [{"date": "2025-01-01", "close": 10.0, "high": 10.5, "low": 9.5,
                  "open": 10.0, "volume": 10000, "amount": 100000}] * n

        signals = engine.evaluate("000001", indicators, kline)
        sell_signals = [s for s in signals if s["strategy_name"] == "RSI超买高抛"]
        assert len(sell_signals) > 0, "RSI=75 应触发超买高抛（阈值 70）"

    def test_rsi_value_35_no_trigger(self):
        """RSI=35 不应触发买入（在 30-70 正常区间内）"""
        from app.services.strategy_engine import StrategyEngine
        engine = StrategyEngine()

        n = 60
        indicators = {
            "ma": {"MA5": [10.0]*n, "MA10": [10.0]*n, "MA20": [10.0]*n, "MA60": [10.0]*n},
            "rsi": {"RSI6": [50.0]*n, "RSI12": [50.0]*n, "RSI14": [35.0]*n, "RSI24": [50.0]*n},
            "kdj": {"K": [50.0]*n, "D": [50.0]*n, "J": [50.0]*n},
        }
        kline = [{"date": "2025-01-01", "close": 10.0, "high": 10.5, "low": 9.5,
                  "open": 10.0, "volume": 10000, "amount": 100000}] * n

        signals = engine.evaluate("000001", indicators, kline)
        rsi_signals = [s for s in signals if s["strategy_name"] in ("RSI超卖低吸", "RSI超买高抛")]
        assert len(rsi_signals) == 0, "RSI=35 不应触发任何RSI信号"
