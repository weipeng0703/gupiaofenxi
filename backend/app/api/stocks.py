"""股票数据 REST API"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import StockFullResponse, RealtimeQuote, StockSearchResult, KlinePoint, IndicatorData
from app.services.akshare_source import AKShareSource
from app.services.indicator_calc import IndicatorCalculator
from app.models import Watchlist, Signal, Strategy

import pandas as pd

router = APIRouter()

# 全局数据源实例（会在 main.py 中注入）
data_source: AKShareSource = AKShareSource()


@router.get("/search", response_model=list[StockSearchResult])
async def search_stock(keyword: str = Query(..., min_length=1)):
    """按代码或名称搜索股票"""
    results = await data_source.search_stock(keyword)
    return [StockSearchResult(**r) for r in results]


@router.get("/{stock_code}/hist", response_model=list[KlinePoint])
async def get_hist_kline(
    stock_code: str,
    period: str = Query("daily"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    adjust: str = Query("qfq"),
):
    """获取历史 K 线数据"""
    raw = await data_source.get_hist_kline(stock_code, period, start_date, end_date, adjust)
    return [KlinePoint(**r) for r in raw]


@router.get("/{stock_code}/full", response_model=StockFullResponse)
async def get_stock_full(
    stock_code: str,
    period: str = Query("daily"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    adjust: str = Query("qfq"),
    db: AsyncSession = Depends(get_db),
):
    """获取股票完整数据：K 线 + 指标 + 信号（前端图表主数据源）"""
    # 1. 获取 K 线数据
    raw_kline = await data_source.get_hist_kline(stock_code, period, start_date, end_date, adjust)

    if not raw_kline:
        return StockFullResponse(
            stock_code=stock_code, stock_name="", period=period,
            kline=[], indicators=IndicatorData(ma={}, rsi={}, kdj={"K": [], "D": [], "J": []}),
            signals=[],
        )

    # 2. 获取股票名称
    stock_name = raw_kline[0].get("stock_name", stock_code)
    # 尝试从实时行情获取更准确的名称
    quote = await data_source.get_realtime_quote(stock_code)
    if quote:
        stock_name = quote.get("stock_name", stock_name)

    # 3. 构建 DataFrame 计算指标
    df = pd.DataFrame(raw_kline)
    if "date" in df.columns:
        # 确保按日期排序
        df = df.sort_values("date").reset_index(drop=True)

    indicators = IndicatorCalculator.compute_all(df)
    kline_points = [KlinePoint(**r) for r in raw_kline]

    # 4. 获取该股票的最近信号
    from sqlalchemy import select
    stmt = (
        select(Signal)
        .where(Signal.stock_code == stock_code)
        .order_by(Signal.timestamp.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    signals_db = result.scalars().all()

    signal_items = []
    for s in signals_db:
        # 获取策略名称
        stmt2 = select(Strategy).where(Strategy.id == s.strategy_id)
        result2 = await db.execute(stmt2)
        strategy = result2.scalar_one_or_none()
        strategy_name = strategy.name if strategy else "Unknown"

        signal_items.append({
            "id": s.id,
            "stock_code": s.stock_code,
            "strategy_name": strategy_name,
            "signal_type": s.signal_type,
            "confidence": s.confidence,
            "indicator_values": eval(s.indicator_values) if isinstance(s.indicator_values, str) else s.indicator_values,
            "price": s.price,
            "timestamp": s.timestamp,
            "is_read": s.is_read,
        })

    return StockFullResponse(
        stock_code=stock_code,
        stock_name=stock_name,
        period=period,
        kline=kline_points,
        indicators=IndicatorData(**indicators),
        signals=signal_items,
    )


@router.get("/{stock_code}/quote", response_model=RealtimeQuote | None)
async def get_realtime_quote(stock_code: str):
    """获取单只股票实时行情"""
    result = await data_source.get_realtime_quote(stock_code)
    if result:
        return RealtimeQuote(**result)
    return None


@router.get("/{stock_code}/intraday", response_model=list[KlinePoint])
async def get_intraday_minutes(
    stock_code: str,
    period: str = Query("5"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    adjust: str = Query("qfq"),
):
    """获取分时/分钟级 K 线数据"""
    raw = await data_source.get_intraday_minutes(stock_code, period, start_date, end_date, adjust)
    return [KlinePoint(**r) for r in raw]