"""Pydantic 请求/响应模型"""
from pydantic import BaseModel


# ─── K 线数据 ───
class KlinePoint(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    amount: float | None = None
    turnover: float | None = None
    change_pct: float | None = None
    change_amt: float | None = None


class IndicatorData(BaseModel):
    ma: dict[str, list[float | None]]           # {"MA5": [...], "MA10": [...], ...}
    rsi: dict[str, list[float | None]]          # {"RSI6": [...], "RSI12": [...], "RSI24": [...]}
    kdj: dict[str, list[float | None]]          # {"K": [...], "D": [...], "J": [...]}


class StockFullResponse(BaseModel):
    """股票完整数据：K 线 + 指标 + 信号"""
    stock_code: str
    stock_name: str
    period: str
    kline: list[KlinePoint]
    indicators: IndicatorData
    signals: list[SignalItem]


# ─── 实时行情 ───
class RealtimeQuote(BaseModel):
    stock_code: str
    stock_name: str
    price: float
    change_pct: float
    change_amt: float = 0
    volume: float
    amount: float
    amplitude: float = 0
    high: float
    low: float
    open: float
    prev_close: float
    volume_ratio: float = 0
    turnover_rate: float = 0
    timestamp: str


# ─── 自选股 ───
class WatchlistAdd(BaseModel):
    stock_code: str
    stock_name: str
    market: str = "A"
    notes: str = ""


class WatchlistItem(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    market: str
    added_at: str
    is_active: bool
    notes: str


class WatchlistUpdate(BaseModel):
    notes: str | None = None
    is_active: bool | None = None


# ─── 信号 ───
class SignalItem(BaseModel):
    id: int
    stock_code: str
    strategy_name: str
    signal_type: str            # "BUY" / "SELL"
    confidence: float
    indicator_values: dict
    price: float
    timestamp: str
    is_read: bool = False


class SignalFilter(BaseModel):
    stock_code: str | None = None
    signal_type: str | None = None
    strategy_id: int | None = None
    unread_only: bool = False
    limit: int = 50
    offset: int = 0


# ─── 策略 ───
class StrategyCreate(BaseModel):
    name: str
    description: str = ""
    config_yaml: str


class StrategyItem(BaseModel):
    id: int
    name: str
    description: str
    config_yaml: str
    is_active: bool
    created_at: str
    updated_at: str


class StrategyUpdate(BaseModel):
    description: str | None = None
    config_yaml: str | None = None
    is_active: bool | None = None


# ─── 搜索 ───
class StockSearchResult(BaseModel):
    stock_code: str
    stock_name: str
    market: str = "A"


# ─── WebSocket 消息 ───
class WSMessage(BaseModel):
    type: str
    payload: dict = {}
    timestamp: str = ""


# ─── 股票分组 ───
class StockGroupCreate(BaseModel):
    name: str
    color: str = "#5470c6"


class StockGroupItem(BaseModel):
    id: int
    name: str
    color: str
    sort_order: int
    created_at: str
    member_count: int = 0


class StockGroupUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class StockGroupMemberItem(BaseModel):
    stock_code: str
    stock_name: str
    market: str
    sort_order: int
    added_at: str


class StockGroupMemberAdd(BaseModel):
    stock_code: str
    stock_name: str
    market: str = "A"


class StockGroupMemberMove(BaseModel):
    stock_code: str
    direction: str  # "up" or "down"