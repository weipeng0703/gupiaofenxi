"""自选股 CRUD API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.schemas import WatchlistAdd, WatchlistItem, WatchlistUpdate
from app.models import Watchlist

router = APIRouter()


@router.get("/", response_model=list[WatchlistItem])
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    """获取所有自选股"""
    stmt = select(Watchlist).where(Watchlist.is_active == True).order_by(Watchlist.added_at.desc())
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [WatchlistItem(
        id=i.id, stock_code=i.stock_code, stock_name=i.stock_name,
        market=i.market, added_at=i.added_at, is_active=i.is_active, notes=i.notes,
        is_special_watch=bool(i.is_special_watch),
    ) for i in items]


@router.post("/", response_model=WatchlistItem)
async def add_to_watchlist(item: WatchlistAdd, db: AsyncSession = Depends(get_db)):
    """添加股票到自选股列表"""
    # 检查是否已存在
    stmt = select(Watchlist).where(Watchlist.stock_code == item.stock_code)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        if not existing.is_active:
            # 重新激活
            existing.is_active = True
            existing.notes = item.notes or existing.notes
            await db.commit()
            await db.refresh(existing)
        else:
            raise HTTPException(status_code=409, detail=f"股票 {item.stock_code} 已在自选股列表中")
        return WatchlistItem(
            id=existing.id, stock_code=existing.stock_code, stock_name=existing.stock_name,
            market=existing.market, added_at=existing.added_at, is_active=existing.is_active, notes=existing.notes,
            is_special_watch=bool(existing.is_special_watch),
        )

    new_item = Watchlist(
        stock_code=item.stock_code,
        stock_name=item.stock_name,
        market=item.market,
        notes=item.notes,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return WatchlistItem(
        id=new_item.id, stock_code=new_item.stock_code, stock_name=new_item.stock_name,
        market=new_item.market, added_at=new_item.added_at, is_active=new_item.is_active, notes=new_item.notes,
        is_special_watch=bool(new_item.is_special_watch),
    )


@router.delete("/{id}")
async def remove_from_watchlist(id: int, db: AsyncSession = Depends(get_db)):
    """从自选股列表移除（软删除）"""
    stmt = select(Watchlist).where(Watchlist.id == id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="自选股条目不存在")

    item.is_active = False
    await db.commit()
    return {"message": "已从自选股列表移除"}


@router.patch("/{id}", response_model=WatchlistItem)
async def update_watchlist(id: int, update: WatchlistUpdate, db: AsyncSession = Depends(get_db)):
    """更新自选股条目（备注或激活状态）"""
    stmt = select(Watchlist).where(Watchlist.id == id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="自选股条目不存在")

    if update.notes is not None:
        item.notes = update.notes
    if update.is_active is not None:
        item.is_active = update.is_active
    if update.is_special_watch is not None:
        item.is_special_watch = int(update.is_special_watch)
    await db.commit()
    await db.refresh(item)
    return WatchlistItem(
        id=item.id, stock_code=item.stock_code, stock_name=item.stock_name,
        market=item.market, added_at=item.added_at, is_active=item.is_active, notes=item.notes,
        is_special_watch=bool(item.is_special_watch),
    )