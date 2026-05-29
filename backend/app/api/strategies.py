"""策略配置 CRUD API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas import StrategyCreate, StrategyItem, StrategyUpdate
from app.models import Strategy

router = APIRouter()


@router.get("/", response_model=list[StrategyItem])
async def list_strategies(db: AsyncSession = Depends(get_db)):
    """获取所有策略配置"""
    stmt = select(Strategy).order_by(Strategy.created_at.desc())
    result = await db.execute(stmt)
    strategies = result.scalars().all()
    return [StrategyItem(
        id=s.id, name=s.name, description=s.description,
        config_yaml=s.config_yaml, is_active=s.is_active,
        created_at=s.created_at, updated_at=s.updated_at,
    ) for s in strategies]


@router.get("/{id}", response_model=StrategyItem)
async def get_strategy(id: int, db: AsyncSession = Depends(get_db)):
    """获取单个策略详情"""
    stmt = select(Strategy).where(Strategy.id == id)
    result = await db.execute(stmt)
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="策略不存在")
    return StrategyItem(
        id=s.id, name=s.name, description=s.description,
        config_yaml=s.config_yaml, is_active=s.is_active,
        created_at=s.created_at, updated_at=s.updated_at,
    )


@router.post("/", response_model=StrategyItem)
async def create_strategy(item: StrategyCreate, db: AsyncSession = Depends(get_db)):
    """创建新策略"""
    # 检查名称唯一性
    stmt = select(Strategy).where(Strategy.name == item.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"策略名称 '{item.name}' 已存在")

    new_strategy = Strategy(
        name=item.name,
        description=item.description,
        config_yaml=item.config_yaml,
    )
    db.add(new_strategy)
    await db.commit()
    await db.refresh(new_strategy)
    return StrategyItem(
        id=new_strategy.id, name=new_strategy.name, description=new_strategy.description,
        config_yaml=new_strategy.config_yaml, is_active=new_strategy.is_active,
        created_at=new_strategy.created_at, updated_at=new_strategy.updated_at,
    )


@router.patch("/{id}", response_model=StrategyItem)
async def update_strategy(id: int, update: StrategyUpdate, db: AsyncSession = Depends(get_db)):
    """更新策略配置"""
    stmt = select(Strategy).where(Strategy.id == id)
    result = await db.execute(stmt)
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="策略不存在")

    if update.description is not None:
        s.description = update.description
    if update.config_yaml is not None:
        s.config_yaml = update.config_yaml
    if update.is_active is not None:
        s.is_active = update.is_active
    await db.commit()
    await db.refresh(s)
    return StrategyItem(
        id=s.id, name=s.name, description=s.description,
        config_yaml=s.config_yaml, is_active=s.is_active,
        created_at=s.created_at, updated_at=s.updated_at,
    )


@router.delete("/{id}")
async def delete_strategy(id: int, db: AsyncSession = Depends(get_db)):
    """删除策略"""
    stmt = select(Strategy).where(Strategy.id == id)
    result = await db.execute(stmt)
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="策略不存在")

    await db.delete(s)
    await db.commit()
    return {"message": "策略已删除"}