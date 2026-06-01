"""FastAPI 入口 — 组装所有模块"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import stocks, watchlist, signals, strategies, stock_groups, wechat_notify
from app.ws.handler import websocket_endpoint
from app.services.realtime_push import push_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动：初始化数据库 + 启动推送服务
    logger.info("初始化数据库...")
    await init_db()

    logger.info("启动实时推送服务...")
    push_service.start()

    yield

    # 关闭：停止推送服务
    logger.info("停止推送服务...")
    push_service.stop()


app = FastAPI(title="gupiaofenxi", description="股票分析助手 API", lifespan=lifespan)

# CORS — 允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API 路由
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(stock_groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(wechat_notify.router, prefix="/api/wechat", tags=["wechat"])

# WebSocket 端点
app.websocket("/ws")(websocket_endpoint)


@app.get("/")
async def root():
    return {"message": "gupiaofenxi API 正在运行", "version": "1.0"}