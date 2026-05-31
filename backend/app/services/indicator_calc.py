"""技术指标计算 — 纯 Python 实现，不依赖 pandas-ta"""
import pandas as pd
from app.config import settings


class IndicatorCalculator:
    """技术指标计算器"""

    @staticmethod
    def calc_ma(close: pd.Series, window: int) -> pd.Series:
        """简单移动平均"""
        return close.rolling(window=window).mean()

    @staticmethod
    def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Wilder's RSI"""
        delta = close.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)

        # Wilder's smoothing (EMA with alpha = 1/period)
        avg_gain = up.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = down.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    @staticmethod
    def calc_kdj(high: pd.Series, low: pd.Series, close: pd.Series,
                 n: int = 9) -> dict:
        """计算 KDJ 指标"""
        low_n = low.rolling(n, min_periods=1).min()
        high_n = high.rolling(n, min_periods=1).max()
        rsv = (close - low_n) / (high_n - low_n) * 100

        K, D = 50.0, 50.0
        K_list, D_list, J_list = [], [], []
        for r in rsv:
            K = 2/3 * K + r / 3
            D = 2/3 * D + K / 3
            K_list.append(K)
            D_list.append(D)
            J = 3 * K - 2 * D
            J_list.append(J)

        return {"K": K_list, "D": D_list, "J": J_list}

    @classmethod
    def compute_all(cls, df: pd.DataFrame) -> dict:
        """计算所有指标"""
        close = df["close"]

        # MA
        ma = {}
        for period in settings.ma_periods:
            series = cls.calc_ma(close, period)
            ma[f"MA{period}"] = series.tolist()

        # RSI — 多周期
        rsi = {}
        for period in settings.rsi_periods:
            series = cls.calc_rsi(close, period)
            rsi[f"RSI{period}"] = series.tolist()

        # KDJ
        kdj = cls.calc_kdj(df["high"], df["low"], close, n=9)

        return {"ma": ma, "rsi": rsi, "kdj": kdj}