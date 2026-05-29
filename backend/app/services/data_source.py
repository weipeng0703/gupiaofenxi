"""抽象数据源接口 — 方便未来扩展港美股等其他市场"""
from abc import ABC, abstractmethod


class DataSourceInterface(ABC):
    """股票数据源抽象接口

    所有数据源（AKShare A股、港美股等）都必须实现此接口。
    这保证了上层代码（指标计算、策略引擎、API）不依赖具体数据源。
    """

    @abstractmethod
    async def get_hist_kline(
        self,
        stock_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
        adjust: str = "qfq",
    ) -> list[dict]:
        """获取历史 K 线数据

        Args:
            stock_code: 股票代码，如 "000001"
            period: 周期 — "daily"/"weekly"/"monthly"/"60min"/"30min"/"15min"/"5min"
            start_date: 开始日期 YYYYMMDD，None 为默认
            end_date: 结束日期 YYYYMMDD，None 为今天
            adjust: 复权方式 — "qfq"(前复权)/"hfq"(后复权)/""(不复权)

        Returns:
            list[dict]: 每条记录包含 date, open, close, high, low, volume, amount, turnover
        """
        pass

    @abstractmethod
    async def get_realtime_quote(self, stock_code: str) -> dict | None:
        """获取单只股票实时行情

        Returns:
            dict | None: 包含 price, change_pct, volume, amount 等；找不到时返回 None
        """
        pass

    @abstractmethod
    async def get_realtime_quotes_batch(self, stock_codes: list[str]) -> list[dict]:
        """批量获取多只股票实时行情（比逐只调用更高效）

        Returns:
            list[dict]: 每只股票的行情数据
        """
        pass

    @abstractmethod
    async def get_intraday_minutes(
        self,
        stock_code: str,
        period: str = "5",
        start_date: str | None = None,
        end_date: str | None = None,
        adjust: str = "qfq",
    ) -> list[dict]:
        """获取分时/分钟级 K 线数据

        Args:
            period: "1"/"5"/"15"/"30"/"60" 分钟

        Returns:
            list[dict]: 分钟级 K 线数据
        """
        pass

    @abstractmethod
    async def search_stock(self, keyword: str) -> list[dict]:
        """按股票代码或名称搜索

        Returns:
            list[dict]: 包含 stock_code, stock_name 的搜索结果
        """
        pass