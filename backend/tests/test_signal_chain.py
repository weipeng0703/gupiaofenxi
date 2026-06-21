"""信号推送链路测试 — 验证策略评估→信号生成→微信推送的完整链路

覆盖三个已修复的 Bug:
  1. IndicatorCalculator.calculate_all → compute_all (方法名修复)
  2. wechat_notify 去重逻辑永不过期 → 10分钟过期
  3. realtime_push 策略评估异常日志 DEBUG → WARNING
"""
import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pandas as pd
import pytest

# 确保 backend 目录在搜索路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── 辅助：构造模拟数据 ───

def make_kline_df(n=60, close_base=10.0, rsi_force=None):
    """构造模拟 K 线 DataFrame，用于指标计算测试"""
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    closes = [close_base + i * 0.01 for i in range(n)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    volumes = [10000 + i * 100 for i in range(n)]

    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": closes,
        "close": closes,
        "high": highs,
        "low": lows,
        "volume": volumes,
        "amount": [v * c for v, c in zip(volumes, closes)],
    })
    return df


def make_kline_list(n=60, close_base=10.0):
    """构造模拟 K 线列表（dict格式），供策略引擎使用"""
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    result = []
    for i in range(n):
        close = close_base + i * 0.01
        result.append({
            "date": dates[i].strftime("%Y-%m-%d"),
            "open": close,
            "close": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "volume": 10000 + i * 100,
            "amount": (10000 + i * 100) * close,
        })
    return result


def make_rsi_extreme_indicators(rsi_value=15.0):
    """构造指标字典，强制 RSI 为指定值（模拟超卖）"""
    n = 60
    return {
        "ma": {
            "MA5": [10.0] * n,
            "MA10": [10.0] * n,
            "MA20": [10.0] * n,
            "MA60": [10.0] * n,
        },
        "rsi": {
            "RSI6": [50.0] * n,
            "RSI12": [50.0] * n,
            "RSI14": [rsi_value] * n,  # 强制 RSI14 为指定值
            "RSI24": [50.0] * n,
        },
        "kdj": {
            "K": [50.0] * n,
            "D": [50.0] * n,
            "J": [50.0] * n,
        },
    }


def make_kdj_cross_indicators(direction="up"):
    """构造指标字典，模拟 KDJ 金叉或死叉"""
    n = 60
    # 构造交叉数据：最后几根K从下方穿越D（金叉），或从上方穿越D（死叉）
    k_list = [50.0] * (n - 3)
    d_list = [50.0] * (n - 3)
    j_list = [50.0] * (n - 3)

    if direction == "up":
        # 金叉：前一根 K<D，当前 K>D
        k_list.extend([48.0, 49.0, 52.0])
        d_list.extend([50.0, 50.5, 50.0])
        j_list.extend([10.0, 20.0, 30.0])  # J > 0
    else:
        # 死叉：前一根 K>D，当前 K<D
        k_list.extend([52.0, 51.0, 48.0])
        d_list.extend([50.0, 49.5, 50.0])
        j_list.extend([80.0, 70.0, 40.0])  # J < 100

    return {
        "ma": {
            "MA5": [10.0] * n,
            "MA10": [10.0] * n,
            "MA20": [10.0] * n,
            "MA60": [10.0] * n,
        },
        "rsi": {
            "RSI6": [50.0] * n,
            "RSI12": [50.0] * n,
            "RSI14": [50.0] * n,
            "RSI24": [50.0] * n,
        },
        "kdj": {
            "K": k_list,
            "D": d_list,
            "J": j_list,
        },
    }


def make_rsi_cross_indicators(direction="up"):
    """构造指标字典，模拟 RSI6 与 RSI12/24 的交叉"""
    n = 60
    rsi6 = [50.0] * (n - 3)
    rsi12 = [50.0] * (n - 3)
    rsi14 = [50.0] * n
    rsi24 = [50.0] * (n - 3)

    if direction == "up":
        rsi6.extend([45.0, 47.0, 52.0])
        rsi12.extend([50.0, 49.0, 48.0])
        rsi24.extend([50.0, 49.5, 48.0])
    else:
        rsi6.extend([55.0, 53.0, 48.0])
        rsi12.extend([50.0, 51.0, 52.0])
        rsi24.extend([50.0, 50.5, 52.0])

    return {
        "ma": {
            "MA5": [10.0] * n,
            "MA10": [10.0] * n,
            "MA20": [10.0] * n,
            "MA60": [10.0] * n,
        },
        "rsi": {
            "RSI6": rsi6,
            "RSI12": rsi12,
            "RSI14": rsi14,
            "RSI24": rsi24,
        },
        "kdj": {
            "K": [50.0] * n,
            "D": [50.0] * n,
            "J": [50.0] * n,
        },
    }


# ─── 测试1：Bug1 修复验证 — IndicatorCalculator.compute_all 可正常调用 ───

class TestBug1IndicatorCalculatorMethod:
    """验证 Bug 1 修复：方法名从 calculate_all 改为 compute_all"""

    def test_compute_all_exists_and_works(self):
        """compute_all 方法存在且能正常计算"""
        df = make_kline_df()
        result = IndicatorCalculator.compute_all(df)
        assert "ma" in result
        assert "rsi" in result
        assert "kdj" in result

    def test_calculate_all_does_not_exist(self):
        """calculate_all 方法已不存在（确认旧方法名被移除）"""
        df = make_kline_df()
        with pytest.raises(AttributeError, match="calculate_all"):
            IndicatorCalculator.calculate_all(df)

    def test_compute_all_output_structure(self):
        """compute_all 输出结构正确"""
        df = make_kline_df()
        result = IndicatorCalculator.compute_all(df)
        # MA 应包含 MA5/MA10/MA20/MA60
        for period in [5, 10, 20, 60]:
            assert f"MA{period}" in result["ma"]
            assert len(result["ma"][f"MA{period}"]) == 60
        # RSI 应包含 RSI6/12/14/24
        for period in [6, 12, 14, 24]:
            assert f"RSI{period}" in result["rsi"]
            assert len(result["rsi"][f"RSI{period}"]) == 60
        # KDJ 应包含 K/D/J
        assert "K" in result["kdj"]
        assert "D" in result["kdj"]
        assert "J" in result["kdj"]


# ─── 测试2：Bug2 修复验证 — 微信推送去重逻辑有10分钟过期 ───

class TestBug2WechatDedupExpiry:
    """验证 Bug 2 修复：微信推送去重逻辑从永久抑制改为10分钟过期"""

    def setup_method(self):
        """每个测试前清空去重缓存"""
        import app.services.wechat_notify as wn
        wn._recent_signals.clear()

    @pytest.mark.asyncio
    async def test_dedup_blocks_within_10_minutes(self):
        """同一信号在10分钟内应被去重跳过"""
        import app.services.wechat_notify as wn

        signal = {
            "stock_code": "000001",
            "strategy_name": "RSI超卖低吸",
            "signal_type": "BUY",
            "confidence": 0.8,
            "price": 10.0,
            "timestamp": "2025-01-01",
            "indicator_values": {"rsi": 15.0},
        }

        # 模拟首次推送成功，记录时间
        wn._recent_signals["000001:RSI超卖低吸"] = datetime.now()

        with patch("app.services.wechat_notify.settings") as mock_settings:
            mock_settings.wechat_webhook_url = "https://example.com/webhook"
            result = await wn.send_wechat_signal(signal)
            assert result is False  # 10分钟内应被跳过

    @pytest.mark.asyncio
    async def test_dedup_allows_after_10_minutes(self):
        """同一信号超过10分钟后应允许再次推送"""
        import app.services.wechat_notify as wn

        signal = {
            "stock_code": "000001",
            "strategy_name": "RSI超卖低吸",
            "signal_type": "BUY",
            "confidence": 0.8,
            "price": 10.0,
            "timestamp": "2025-01-01",
            "indicator_values": {"rsi": 15.0},
        }

        # 记录时间超过10分钟
        wn._recent_signals["000001:RSI超卖低吸"] = datetime.now() - timedelta(seconds=700)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}

        with patch("app.services.wechat_notify.settings") as mock_settings, \
             patch("app.services.wechat_notify.curl_requests") as mock_curl:
            mock_settings.wechat_webhook_url = "https://example.com/webhook"
            mock_curl.post.return_value = mock_resp
            result = await wn.send_wechat_signal(signal)
            assert result is True  # 超过10分钟应允许推送

    @pytest.mark.asyncio
    async def test_dedup_different_signals_not_blocked(self):
        """不同股票代码的策略信号不应互相去重"""
        import app.services.wechat_notify as wn

        signal1 = {
            "stock_code": "000001",
            "strategy_name": "RSI超卖低吸",
            "signal_type": "BUY",
            "confidence": 0.8,
            "price": 10.0,
            "timestamp": "2025-01-01",
            "indicator_values": {"rsi": 15.0},
        }
        signal2 = {
            "stock_code": "600000",  # 不同的股票代码
            "strategy_name": "RSI超卖低吸",
            "signal_type": "BUY",
            "confidence": 0.8,
            "price": 20.0,
            "timestamp": "2025-01-01",
            "indicator_values": {"rsi": 15.0},
        }

        # 记录 signal1 的时间
        wn._recent_signals["000001:RSI超卖低吸"] = datetime.now()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}

        with patch("app.services.wechat_notify.settings") as mock_settings, \
             patch("app.services.wechat_notify.curl_requests") as mock_curl:
            mock_settings.wechat_webhook_url = "https://example.com/webhook"
            mock_curl.post.return_value = mock_resp
            # signal2 的 dedup_key 是 "600000:RSI超卖低吸"，不应被 signal1 去重
            result = await wn.send_wechat_signal(signal2)
            assert result is True


# ─── 测试3：策略引擎评估测试 ───

class TestStrategyEngineEvaluate:
    """验证策略引擎在不同条件下能正确触发信号"""

    def setup_method(self):
        """初始化策略引擎"""
        from app.services.strategy_engine import StrategyEngine, StrategyConfig
        self.engine = StrategyEngine()

    def test_rsi_oversold_triggers_buy(self):
        """RSI低于20应触发超卖低吸买入信号"""
        indicators = make_rsi_extreme_indicators(rsi_value=15.0)  # RSI14 = 15 < 20
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        # 应包含 RSI超卖低吸 信号
        buy_signals = [s for s in signals if s["strategy_name"] == "RSI超卖低吸"]
        assert len(buy_signals) > 0
        assert buy_signals[0]["signal_type"] == "BUY"

    def test_rsi_overbought_triggers_sell(self):
        """RSI高于80应触发超买高抛卖出信号"""
        indicators = make_rsi_extreme_indicators(rsi_value=85.0)  # RSI14 = 85 > 80
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        sell_signals = [s for s in signals if s["strategy_name"] == "RSI超买高抛"]
        assert len(sell_signals) > 0
        assert sell_signals[0]["signal_type"] == "SELL"

    def test_rsi_normal_no_signal(self):
        """RSI在正常区间(30-70)不应触发RSI反转信号"""
        indicators = make_rsi_extreme_indicators(rsi_value=50.0)
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        rsi_signals = [s for s in signals if s["strategy_name"] in ("RSI超卖低吸", "RSI超买高抛")]
        assert len(rsi_signals) == 0

    def test_kdj_golden_cross_triggers_buy(self):
        """KDJ金叉应触发买入信号"""
        indicators = make_kdj_cross_indicators(direction="up")
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        kdj_buy = [s for s in signals if s["strategy_name"] == "KDJ金叉买入"]
        assert len(kdj_buy) > 0
        assert kdj_buy[0]["signal_type"] == "BUY"

    def test_kdj_dead_cross_triggers_sell(self):
        """KDJ死叉应触发卖出信号"""
        indicators = make_kdj_cross_indicators(direction="down")
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        kdj_sell = [s for s in signals if s["strategy_name"] == "KDJ死叉卖出"]
        assert len(kdj_sell) > 0
        assert kdj_sell[0]["signal_type"] == "SELL"

    def test_rsi_cross_golden_triggers_buy(self):
        """RSI6上穿RSI12和RSI24应触发金叉低吸信号"""
        indicators = make_rsi_cross_indicators(direction="up")
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        rsi_buy = [s for s in signals if s["strategy_name"] == "RSI金叉低吸"]
        assert len(rsi_buy) > 0

    def test_rsi_cross_dead_triggers_sell(self):
        """RSI6下穿RSI12和RSI24应触发死叉高抛信号"""
        indicators = make_rsi_cross_indicators(direction="down")
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        rsi_sell = [s for s in signals if s["strategy_name"] == "RSI死叉高抛"]
        assert len(rsi_sell) > 0

    def test_signal_contains_required_fields(self):
        """信号应包含所有必要字段"""
        indicators = make_rsi_extreme_indicators(rsi_value=15.0)
        kline = make_kline_list()

        signals = self.engine.evaluate("000001", indicators, kline)
        assert len(signals) > 0
        signal = signals[0]
        assert "stock_code" in signal
        assert "strategy_name" in signal
        assert "signal_type" in signal
        assert "confidence" in signal
        assert "price" in signal
        assert "indicator_values" in signal


# ─── 测试4：完整链路集成测试 ───

class TestFullSignalChain:
    """验证从指标计算到策略评估再到微信推送的完整链路"""

    def setup_method(self):
        """清空微信推送去重缓存"""
        import app.services.wechat_notify as wn
        wn._recent_signals.clear()

    def test_indicator_to_strategy_to_signal(self):
        """从 DataFrame → compute_all → 策略评估 → 信号生成"""
        # 构造一个 RSI 超卖的数据集
        n = 60
        # 构造连续下跌的收盘价，使 RSI 进入超卖区
        closes = [20.0 - i * 0.3 for i in range(n)]
        df = make_kline_df()
        df["close"] = closes
        df["high"] = [c + 0.1 for c in closes]
        df["low"] = [c - 0.1 for c in closes]

        # 第一步：计算指标
        indicators = IndicatorCalculator.compute_all(df)
        assert "rsi" in indicators
        assert "RSI14" in indicators["rsi"]

        # 第二步：构造 kline 列表
        kline = []
        for i in range(n):
            kline.append({
                "date": df.iloc[i]["date"],
                "open": df.iloc[i]["open"],
                "close": closes[i],
                "high": df.iloc[i]["high"],
                "low": df.iloc[i]["low"],
                "volume": df.iloc[i]["volume"],
                "amount": df.iloc[i]["amount"],
            })

        # 第三步：策略评估
        from app.services.strategy_engine import StrategyEngine
        engine = StrategyEngine()
        signals = engine.evaluate("000001", indicators, kline)

        # 连续下跌的数据应该触发某些买入信号（RSI超卖）
        # 注意：实际 RSI 值取决于算法，可能不是严格 <20，
        # 但我们验证链路能正常走通
        assert isinstance(signals, list)
        # 验证所有信号都有正确的结构
        for signal in signals:
            assert signal["stock_code"] == "000001"
            assert signal["signal_type"] in ("BUY", "SELL")
            assert isinstance(signal["confidence"], float)

    @pytest.mark.asyncio
    async def test_wechat_push_called_with_signal(self):
        """模拟完整链路：策略评估出信号后微信推送被调用"""
        # 构造一个触发信号的场景
        indicators = make_rsi_extreme_indicators(rsi_value=15.0)
        kline = make_kline_list()

        from app.services.strategy_engine import StrategyEngine
        engine = StrategyEngine()
        signals = engine.evaluate("000001", indicators, kline)

        assert len(signals) > 0, "应至少触发一个信号"

        # 模拟微信推送
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}

        with patch("app.services.wechat_notify.settings") as mock_settings, \
             patch("app.services.wechat_notify.curl_requests") as mock_curl:
            mock_settings.wechat_webhook_url = "https://example.com/webhook"
            mock_curl.post.return_value = mock_resp

            from app.services.wechat_notify import send_wechat_signal
            for signal in signals:
                result = await send_wechat_signal(signal)
                assert result is True  # 首次推送应成功


# ─── 测试5：Bug3 修复验证 — 日志级别 ───

class TestBug3LogLevel:
    """验证 Bug 3 修复：策略评估异常日志级别从 DEBUG 提升到 WARNING"""

    def test_strategy_exception_logged_at_warning(self):
        """验证 realtime_push.py 中策略评估异常使用 WARNING 级别"""
        import app.services.realtime_push as rp
        # 检查源代码中异常日志的级别
        import inspect
        source = inspect.getsource(rp.RealtimePushService._fetch_and_push)
        assert "logger.warning" in source, "策略评估异常应使用 logger.warning"
        assert "logger.debug" not in source, "策略评估异常不应使用 logger.debug"


# ─── 导入必要的类 ───

from app.services.indicator_calc import IndicatorCalculator
