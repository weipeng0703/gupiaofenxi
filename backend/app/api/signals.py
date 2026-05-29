"""信号查询 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas import SignalItem, SignalFilter
from app.models import Signal, Strategy

router = APIRouter()


@router.get("/", response_model=list[SignalItem])
async def list_signals(
    stock_code: str | None = None,
    signal_type: str | None = None,
    strategy_id: int | None = None,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """查询信号列表"""
    stmt = select(Signal).order_by(Signal.timestamp.desc())

    if stock_code:
        stmt = stmt.where(Signal.stock_code == stock_code)
    if signal_type:
        stmt = stmt.where(Signal.signal_type == signal_type)
    if strategy_id:
        stmt = stmt.where(Signal.strategy_id == strategy_id)
    if unread_only:
        stmt = stmt.where(Signal.is_read == False)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    signals = result.scalars().all()

    items = []
    for s in signals:
        # 获取策略名称
        stmt2 = select(Strategy).where(Strategy.id == s.strategy_id)
        result2 = await db.execute(stmt2)
        strategy = result2.scalar_one_or_none()
        strategy_name = strategy.name if strategy else "Unknown"

        items.append(SignalItem(
            id=s.id, stock_code=s.stock_code, strategy_name=strategy_name,
            signal_type=s.signal_type, confidence=s.confidence,
            indicator_values=eval(s.indicator_values) if isinstance(s.indicator_values, str) else s.indicator_values,
            price=s.price, timestamp=s.timestamp, is_read=s.is_read,
        ))

    return items


@router.get("/{id}", response_model=SignalItem)
async def get_signal(id: int, db: AsyncSession = Depends(get_db)):
    """获取单个信号详情"""
    stmt = select(Signal).where(Signal.id == id)
    result = await db.execute(stmt)
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="信号不存在")

    stmt2 = select(Strategy).where(Strategy.id == s.strategy_id)
    result2 = await db.execute(stmt2)
    strategy = result2.scalar_one_or_none()
    strategy_name = strategy.name if strategy else "Unknown"

    return SignalItem(
        id=s.id, stock_code=s.stock_code, strategy_name=strategy_name,
        signal_type=s.signal_type, confidence=s.confidence,
        indicator_values=eval(s.indicator_values) if isinstance(s.indicator_values, str) else s.indicator_values,
        price=s.price, timestamp=s.timestamp, is_read=s.is_read,
    )


@router.patch("/{id}/read")
async def mark_signal_read(id: int, db: AsyncSession = Depends(get_db)):
    """标记信号为已读"""
    stmt = select(Signal).where(Signal.id == id)
    result = await db.execute(stmt)
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="信号不存在")

    s.is_read = True
    await db.commit()
    return {"message": "已标记为已读"}