"""WebSocket 连接管理器"""
import logging
from fastapi import WebSocket, WebSocketDisconnect
from uuid import uuid4

from app.ws.protocol import (
    MSG_SUBSCRIBE, MSG_UNSUBSCRIBE, MSG_REQUEST_HIST, MSG_PING,
    MSG_PONG, make_message, make_error,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """管理所有 WebSocket 连接及其订阅关系"""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}   # connection_id -> WebSocket
        self._subscriptions: dict[str, set[str]] = {}   # connection_id -> set of stock_codes

    async def connect(self, websocket: WebSocket) -> str:
        """接受新连接，返回 connection_id"""
        await websocket.accept()
        connection_id = str(uuid4())
        self._connections[connection_id] = websocket
        self._subscriptions[connection_id] = set()
        logger.info(f"WebSocket 连接: {connection_id}")
        return connection_id

    def disconnect(self, connection_id: str):
        """断开连接"""
        self._connections.pop(connection_id, None)
        self._subscriptions.pop(connection_id, None)
        logger.info(f"WebSocket 断开: {connection_id}")

    def subscribe(self, connection_id: str, stock_codes: list[str]):
        """订阅股票"""
        if connection_id in self._subscriptions:
            self._subscriptions[connection_id].update(stock_codes)
            # 延迟导入避免循环依赖
            from app.services.realtime_push import push_service
            push_service.update_subscriptions(self.get_all_subscribed_codes())

    def unsubscribe(self, connection_id: str, stock_codes: list[str]):
        """取消订阅"""
        if connection_id in self._subscriptions:
            for code in stock_codes:
                self._subscriptions[connection_id].discard(code)
            from app.services.realtime_push import push_service
            push_service.update_subscriptions(self.get_all_subscribed_codes())

    def get_subscribed_codes(self, connection_id: str) -> set[str]:
        """获取某个连接订阅的股票代码"""
        return self._subscriptions.get(connection_id, set())

    def get_all_subscribed_codes(self) -> set[str]:
        """获取所有连接订阅的股票代码（合并）"""
        all_codes = set()
        for codes in self._subscriptions.values():
            all_codes.update(codes)
        return all_codes

    async def send_to(self, connection_id: str, message: dict):
        """向指定连接发送消息"""
        ws = self._connections.get(connection_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(connection_id)

    async def broadcast(self, message: dict, stock_codes: set[str] | None = None):
        """广播消息，可选只发给订阅了指定股票的连接"""
        for connection_id, ws in list(self._connections.items()):
            try:
                if stock_codes:
                    # 只发给订阅了这些股票的连接
                    subscribed = self._subscriptions.get(connection_id, set())
                    if not subscribed.intersection(stock_codes):
                        continue
                await ws.send_json(message)
            except Exception:
                self.disconnect(connection_id)


# 全局连接管理器实例
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 入口端点"""
    connection_id = await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == MSG_SUBSCRIBE:
                payload = data.get("payload", {})
                stock_codes = payload.get("stock_codes", [])
                manager.subscribe(connection_id, stock_codes)
                await manager.send_to(connection_id, make_message("subscribed", {
                    "stock_codes": stock_codes,
                }))

            elif msg_type == MSG_UNSUBSCRIBE:
                payload = data.get("payload", {})
                stock_codes = payload.get("stock_codes", [])
                manager.unsubscribe(connection_id, stock_codes)
                await manager.send_to(connection_id, make_message("unsubscribed", {
                    "stock_codes": stock_codes,
                }))

            elif msg_type == MSG_REQUEST_HIST:
                # 请求历史数据
                payload = data.get("payload", {})
                stock_code = payload.get("stock_code", "")
                period = payload.get("period", "daily")
                start_date = payload.get("start_date")
                end_date = payload.get("end_date")

                from app.services.akshare_source import AKShareSource
                from app.services.indicator_calc import IndicatorCalculator
                import pandas as pd

                ds = AKShareSource()
                raw = await ds.get_hist_kline(stock_code, period, start_date, end_date)
                if raw:
                    df = pd.DataFrame(raw)
                    df = df.sort_values("date").reset_index(drop=True)
                    indicators = IndicatorCalculator.calculate_all(df)
                    quote = await ds.get_realtime_quote(stock_code)
                    stock_name = quote.get("stock_name", stock_code) if quote else stock_code

                    from app.ws.protocol import make_hist_data
                    msg = make_hist_data(stock_code, stock_name, period, raw, indicators)
                    await manager.send_to(connection_id, msg)
                else:
                    await manager.send_to(connection_id, make_error("NO_DATA", f"无法获取 {stock_code} 的数据"))

            elif msg_type == MSG_PING:
                await manager.send_to(connection_id, make_message(MSG_PONG))

    except WebSocketDisconnect:
        manager.disconnect(connection_id)