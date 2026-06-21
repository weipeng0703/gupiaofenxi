"""SQLAlchemy ORM 模型"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String, unique=True, nullable=False)
    stock_name = Column(String, nullable=False)
    market = Column(String, nullable=False, default="A")
    added_at = Column(String, nullable=False, default="now")
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, default="")
    is_special_watch = Column(Integer, nullable=False, default=0)


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, default="")
    config_yaml = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(String, nullable=False, default="now")
    updated_at = Column(String, nullable=False, default="now")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String, nullable=False)
    strategy_id = Column(Integer, nullable=False)
    signal_type = Column(String, nullable=False)        # "BUY" or "SELL"
    confidence = Column(Float, default=0.0)
    indicator_values = Column(Text, nullable=False, default="{}")
    price = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)
    created_at = Column(String, nullable=False, default="now")
    is_read = Column(Boolean, nullable=False, default=False)


class KlineCache(Base):
    __tablename__ = "kline_cache"

    stock_code = Column(String, nullable=False, primary_key=True)
    period = Column(String, nullable=False, primary_key=True)
    date = Column(String, nullable=False, primary_key=True)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    turnover = Column(Float)


class StockGroup(Base):
    __tablename__ = "stock_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=False, default="#5470c6")
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default="now")
    updated_at = Column(String, nullable=False, default="now")


class StockGroupMember(Base):
    __tablename__ = "stock_group_members"

    group_id = Column(Integer, primary_key=True, nullable=False)
    stock_code = Column(String, primary_key=True, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    added_at = Column(String, nullable=False, default="now")