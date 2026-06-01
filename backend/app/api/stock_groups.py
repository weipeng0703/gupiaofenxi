"""股票分组 CRUD API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.database import get_db
from app.schemas import (
    StockGroupCreate, StockGroupItem, StockGroupUpdate,
    StockGroupMemberAdd, StockGroupMemberItem, StockGroupMemberMove,
)
from app.models import StockGroup, StockGroupMember, Watchlist

router = APIRouter()


# ── 分组 CRUD ──

@router.get("/", response_model=list[StockGroupItem])
async def list_groups(db: AsyncSession = Depends(get_db)):
    """列出所有分组（含成员数量）"""
    stmt = select(StockGroup).order_by(StockGroup.sort_order, StockGroup.id)
    result = await db.execute(stmt)
    groups = result.scalars().all()

    items = []
    for g in groups:
        # 统计成员数
        count_stmt = select(func.count()).select_from(StockGroupMember).where(
            StockGroupMember.group_id == g.id
        )
        count_result = await db.execute(count_stmt)
        member_count = count_result.scalar() or 0

        items.append(StockGroupItem(
            id=g.id, name=g.name, color=g.color,
            sort_order=g.sort_order, created_at=g.created_at,
            member_count=member_count,
        ))
    return items


@router.post("/", response_model=StockGroupItem)
async def create_group(data: StockGroupCreate, db: AsyncSession = Depends(get_db)):
    """创建新分组"""
    # 获取最大 sort_order
    stmt = select(func.max(StockGroup.sort_order))
    result = await db.execute(stmt)
    max_order = result.scalar() or 0

    group = StockGroup(
        name=data.name,
        color=data.color,
        sort_order=max_order + 1,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    return StockGroupItem(
        id=group.id, name=group.name, color=group.color,
        sort_order=group.sort_order, created_at=group.created_at,
        member_count=0,
    )


@router.patch("/{group_id}", response_model=StockGroupItem)
async def update_group(group_id: int, data: StockGroupUpdate, db: AsyncSession = Depends(get_db)):
    """更新分组名称或颜色"""
    stmt = select(StockGroup).where(StockGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    if data.name is not None:
        group.name = data.name
    if data.color is not None:
        group.color = data.color

    await db.commit()
    await db.refresh(group)

    # 统计成员数
    count_stmt = select(func.count()).select_from(StockGroupMember).where(
        StockGroupMember.group_id == group.id
    )
    count_result = await db.execute(count_stmt)
    member_count = count_result.scalar() or 0

    return StockGroupItem(
        id=group.id, name=group.name, color=group.color,
        sort_order=group.sort_order, created_at=group.created_at,
        member_count=member_count,
    )


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """删除分组（级联删除成员）"""
    stmt = select(StockGroup).where(StockGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 删除成员
    await db.execute(
        delete(StockGroupMember).where(StockGroupMember.group_id == group_id)
    )
    # 删除分组
    await db.delete(group)
    await db.commit()
    return {"message": f"分组 '{group.name}' 已删除"}


# ── 分组成员管理 ──

@router.get("/{group_id}/members", response_model=list[StockGroupMemberItem])
async def list_members(group_id: int, db: AsyncSession = Depends(get_db)):
    """列出分组内标的"""
    # 验证分组存在
    stmt = select(StockGroup).where(StockGroup.id == group_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="分组不存在")

    # 查询成员，关联 watchlist 获取 stock_name 和 market
    stmt = (
        select(StockGroupMember, Watchlist.stock_name, Watchlist.market)
        .join(Watchlist, StockGroupMember.stock_code == Watchlist.stock_code)
        .where(StockGroupMember.group_id == group_id)
        .order_by(StockGroupMember.sort_order, StockGroupMember.added_at)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        StockGroupMemberItem(
            stock_code=row[0].stock_code,
            stock_name=row[1] or row[0].stock_code,
            market=row[2] or "A",
            sort_order=row[0].sort_order,
            added_at=row[0].added_at,
        )
        for row in rows
    ]


@router.post("/{group_id}/members", response_model=StockGroupMemberItem)
async def add_member(group_id: int, data: StockGroupMemberAdd, db: AsyncSession = Depends(get_db)):
    """添加标的到分组（必须先在自选股中）"""
    # 验证分组存在
    stmt = select(StockGroup).where(StockGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 验证标的在自选股中
    stmt = select(Watchlist).where(
        Watchlist.stock_code == data.stock_code,
        Watchlist.is_active == True,
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"股票 {data.stock_code} 不在自选股中，请先添加到自选股",
        )

    # 检查是否已在分组中
    stmt = select(StockGroupMember).where(
        StockGroupMember.group_id == group_id,
        StockGroupMember.stock_code == data.stock_code,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"股票 {data.stock_code} 已在该分组中")

    # 获取最大 sort_order
    stmt = select(func.max(StockGroupMember.sort_order)).where(
        StockGroupMember.group_id == group_id
    )
    result = await db.execute(stmt)
    max_order = result.scalar() or 0

    member = StockGroupMember(
        group_id=group_id,
        stock_code=data.stock_code,
        sort_order=max_order + 1,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return StockGroupMemberItem(
        stock_code=data.stock_code,
        stock_name=data.stock_name,
        market=data.market,
        sort_order=member.sort_order,
        added_at=member.added_at,
    )


@router.delete("/{group_id}/members/{stock_code}")
async def remove_member(group_id: int, stock_code: str, db: AsyncSession = Depends(get_db)):
    """从分组中移除标的"""
    stmt = select(StockGroupMember).where(
        StockGroupMember.group_id == group_id,
        StockGroupMember.stock_code == stock_code,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="该标的不在此分组中")

    await db.delete(member)
    await db.commit()
    return {"message": f"已从分组移除 {stock_code}"}


@router.patch("/{group_id}/members/{stock_code}/move")
async def move_member(group_id: int, stock_code: str, data: StockGroupMemberMove,
                      db: AsyncSession = Depends(get_db)):
    """上下移动标的排序"""
    # 查询所有成员（按 sort_order 排序）
    stmt = (
        select(StockGroupMember)
        .where(StockGroupMember.group_id == group_id)
        .order_by(StockGroupMember.sort_order, StockGroupMember.added_at)
    )
    result = await db.execute(stmt)
    members = list(result.scalars().all())

    # 找到当前标的的索引
    current_idx = None
    for i, m in enumerate(members):
        if m.stock_code == stock_code:
            current_idx = i
            break

    if current_idx is None:
        raise HTTPException(status_code=404, detail="该标的不在此分组中")

    # 计算目标索引
    if data.direction == "up" and current_idx > 0:
        target_idx = current_idx - 1
    elif data.direction == "down" and current_idx < len(members) - 1:
        target_idx = current_idx + 1
    else:
        return {"message": "无法移动"}

    # 交换 sort_order
    members[current_idx].sort_order, members[target_idx].sort_order = (
        members[target_idx].sort_order, members[current_idx].sort_order
    )
    await db.commit()
    return {"message": f"已移动 {stock_code}"}