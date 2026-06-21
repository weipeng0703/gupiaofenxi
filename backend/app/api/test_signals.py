"""测试信号 API — 生成模拟交易信号并通过 WebSocket 实时推送"""
import asyncio
import json
import random
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import text

from app.database import async_session
from app.ws.handler import manager
from app.ws.protocol import make_signal_alert

logger = logging.getLogger(__name__)

router = APIRouter()

# 模拟策略信号模板
TEST_SIGNALS_TEMPLATES = [
    {
        "strategy_name": "RSI超卖反弹",
        "signal_type": "BUY",
        "confidence_range": (0.72, 0.92),
        "indicator_gen": lambda price: {
            "RSI6": round(random.uniform(18, 28), 2),
            "RSI12": round(random.uniform(25, 35), 2),
            "RSI24": round(random.uniform(30, 40), 2),
        },
        "description": "RSI多周期超卖，短期反弹概率大",
    },
    {
        "strategy_name": "KDJ金叉买入",
        "signal_type": "BUY",
        "confidence_range": (0.65, 0.85),
        "indicator_gen": lambda price: {
            "K": round(random.uniform(20, 35), 2),
            "D": round(random.uniform(18, 30), 2),
            "J": round(random.uniform(-5, 15), 2),
        },
        "description": "KDJ低位金叉，趋势反转信号",
    },
    {
        "strategy_name": "MA20突破",
        "signal_type": "BUY",
        "confidence_range": (0.68, 0.88),
        "indicator_gen": lambda price: {
            "MA5": round(price * random.uniform(1.01, 1.03), 2),
            "MA10": round(price * random.uniform(0.99, 1.01), 2),
            "MA20": round(price * random.uniform(0.96, 0.99), 2),
            "volume_ratio": round(random.uniform(1.5, 2.8), 2),
        },
        "description": "放量突破MA20均线，多头趋势确认",
    },
    {
        "strategy_name": "多指标共振",
        "signal_type": "BUY",
        "confidence_range": (0.82, 0.96),
        "indicator_gen": lambda price: {
            "RSI6": round(random.uniform(25, 35), 2),
            "K": round(random.uniform(25, 40), 2),
            "D": round(random.uniform(20, 35), 2),
            "MA20": round(price * random.uniform(0.95, 0.99), 2),
        },
        "description": "RSI+KDJ+均线三重共振，强烈看多",
    },
    {
        "strategy_name": "RSI超买预警",
        "signal_type": "SELL",
        "confidence_range": (0.70, 0.90),
        "indicator_gen": lambda price: {
            "RSI6": round(random.uniform(75, 90), 2),
            "RSI12": round(random.uniform(68, 80), 2),
            "RSI24": round(random.uniform(62, 75), 2),
        },
        "description": "RSI多周期超买，注意回调风险",
    },
    {
        "strategy_name": "KDJ死叉卖出",
        "signal_type": "SELL",
        "confidence_range": (0.65, 0.82),
        "indicator_gen": lambda price: {
            "K": round(random.uniform(70, 85), 2),
            "D": round(random.uniform(72, 88), 2),
            "J": round(random.uniform(90, 110), 2),
        },
        "description": "KDJ高位死叉，下行趋势信号",
    },
    {
        "strategy_name": "量价背离",
        "signal_type": "SELL",
        "confidence_range": (0.60, 0.78),
        "indicator_gen": lambda price: {
            "volume_ratio": round(random.uniform(0.4, 0.7), 2),
            "MA5": round(price * random.uniform(0.99, 1.01), 2),
            "MA10": round(price * random.uniform(1.01, 1.03), 2),
        },
        "description": "价升量缩，上涨动力不足",
    },
    {
        "strategy_name": "均线空头排列",
        "signal_type": "SELL",
        "confidence_range": (0.72, 0.88),
        "indicator_gen": lambda price: {
            "MA5": round(price * random.uniform(0.97, 0.99), 2),
            "MA10": round(price * random.uniform(0.99, 1.01), 2),
            "MA20": round(price * random.uniform(1.02, 1.05), 2),
            "MA60": round(price * random.uniform(1.05, 1.10), 2),
        },
        "description": "均线空头排列，趋势偏空",
    },
]


async def _generate_and_push_signals(stock_code: str, stock_name: str, price: float, count: int):
    """后台任务：逐条生成信号并推送，模拟实时异动"""
    templates = random.sample(TEST_SIGNALS_TEMPLATES, min(count, len(TEST_SIGNALS_TEMPLATES)))

    for i, tpl in enumerate(templates):
        confidence = round(random.uniform(*tpl["confidence_range"]), 2)
        indicator_values = tpl["indicator_gen"](price)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        signal_data = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "strategy_name": tpl["strategy_name"],
            "signal_type": tpl["signal_type"],
            "confidence": confidence,
            "indicator_values": indicator_values,
            "price": round(price * random.uniform(0.98, 1.02), 2),
            "timestamp": now,
            "is_read": False,
        }

        # 存入数据库
        try:
            async with async_session() as session:
                # 使用 strategy_id=0 表示测试信号
                await session.execute(
                    text("""INSERT INTO signals (stock_code, strategy_id, signal_type, confidence, indicator_values, price, timestamp, created_at, is_read)
                            VALUES (:code, :sid, :stype, :conf, :indv, :price, :ts, :ts, 0)"""),
                    {
                        "code": stock_code,
                        "sid": 0,
                        "stype": tpl["signal_type"],
                        "conf": confidence,
                        "indv": json.dumps(indicator_values),
                        "price": signal_data["price"],
                        "ts": now,
                    },
                )
                # 获取插入的 ID
                result = await session.execute(text("SELECT last_insert_rowid()"))
                signal_id = result.scalar()
                await session.commit()

                signal_data["id"] = signal_id
        except Exception as e:
            logger.warning(f"测试信号入库失败: {e}")
            signal_data["id"] = 90000 + i

        # 通过 WebSocket 推送
        signal_msg = make_signal_alert(signal_data)
        await manager.broadcast(signal_msg)
        logger.info(f"测试信号推送: {stock_code} {tpl['strategy_name']} {tpl['signal_type']}")

        # 同步推送微信
        from app.services.wechat_notify import send_wechat_signal
        await send_wechat_signal(signal_data)

        # 间隔 1-3 秒，模拟实时到达
        if i < len(templates) - 1:
            await asyncio.sleep(random.uniform(1.0, 3.0))


@router.post("/special-watch")
async def generate_special_watch_test_signals(background_tasks: BackgroundTasks):
    """为所有特别关注的股票生成测试信号并逐条推送

    自动查询 is_special_watch=1 的股票，每只生成 2-3 条信号。
    """
    from app.database import async_session
    from sqlalchemy import text as sql_text

    # 查询所有特别关注的股票
    async with async_session() as session:
        result = await session.execute(
            sql_text("SELECT stock_code, stock_name FROM watchlist WHERE is_active = 1 AND is_special_watch = 1")
        )
        special_stocks = [(row[0], row[1]) for row in result.fetchall()]

    if not special_stocks:
        return {"message": "没有特别关注的股票", "count": 0}

    total_count = 0
    for stock_code, stock_name in special_stocks:
        count = random.randint(2, 3)
        price = round(random.uniform(8, 80), 2)
        background_tasks.add_task(_generate_and_push_signals, stock_code, stock_name, price, count)
        total_count += count

    return {
        "message": f"正在为 {len(special_stocks)} 只特别关注股票生成共 {total_count} 条测试信号",
        "stocks": [{"stock_code": c, "stock_name": n} for c, n in special_stocks],
        "total_count": total_count,
    }


@router.post("/{stock_code}")
async def generate_test_signals(
    stock_code: str,
    background_tasks: BackgroundTasks,
    count: int = 5,
    price: float | None = None,
    stock_name: str | None = None,
):
    """为指定股票生成测试信号并实时推送到前端

    - stock_code: 股票代码
    - count: 生成信号数量（1-8），默认5
    - price: 模拟价格，不传则尝试获取实时价格
    - stock_name: 股票名称，不传则自动获取
    """
    count = max(1, min(count, len(TEST_SIGNALS_TEMPLATES)))

    # 获取股票真实价格和名称
    actual_price = price
    actual_name = stock_name or stock_code

    if not actual_price or not stock_name:
        try:
            from app.services.akshare_source import AKShareSource
            ds = AKShareSource()
            quote = await ds.get_realtime_quote(stock_code)
            if quote:
                if not actual_price:
                    actual_price = quote.get("price", 10.0)
                if not stock_name:
                    actual_name = quote.get("stock_name", stock_code)
        except Exception:
            pass

    if not actual_price:
        actual_price = round(random.uniform(5, 50), 2)

    # 启动后台任务逐条推送
    background_tasks.add_task(_generate_and_push_signals, stock_code, actual_name, actual_price, count)

    return {
        "message": f"正在生成 {count} 条测试信号并推送",
        "stock_code": stock_code,
        "stock_name": actual_name,
        "price": actual_price,
        "count": count,
    }
