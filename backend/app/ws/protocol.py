"""WebSocket 消息协议定义"""
from datetime import datetime

# ─── 消息类型常量 ───
MSG_SUBSCRIBE = "subscribe"
MSG_UNSUBSCRIBE = "unsubscribe"
MSG_REQUEST_HIST = "request_hist"
MSG_PING = "ping"

MSG_QUOTE_UPDATE = "quote_update"
MSG_SIGNAL_ALERT = "signal_alert"
MSG_HIST_DATA = "hist_data"
MSG_PONG = "pong"
MSG_ERROR = "error"


def make_message(msg_type: str, payload: dict = None) -> dict:
    """构造标准 WebSocket 消息"""
    return {
        "type": msg_type,
        "payload": payload or {},
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    }


def make_quote_update(quotes: list[dict]) -> dict:
    """构造行情更新消息"""
    return make_message(MSG_QUOTE_UPDATE, {"quotes": quotes})


def make_signal_alert(signal: dict) -> dict:
    """构造信号通知消息"""
    return make_message(MSG_SIGNAL_ALERT, {"signal": signal})


def make_hist_data(stock_code: str, stock_name: str, period: str,
                   kline: list, indicators: dict) -> dict:
    """构造历史数据消息"""
    return make_message(MSG_HIST_DATA, {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "period": period,
        "kline": kline,
        "indicators": indicators,
    })


def make_error(code: str, message: str) -> dict:
    """构造错误消息"""
    return make_message(MSG_ERROR, {"code": code, "message": message})