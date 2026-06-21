"""数据库初始化与会话管理"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.config import settings

# 异步引擎 — SQLite + aiosqlite
engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.get_abs_db_path()}",
    echo=False,
)

# 异步会话工厂
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# 表创建 SQL
CREATE_TABLES_SQL = [
    """CREATE TABLE IF NOT EXISTS watchlist (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code  TEXT    NOT NULL UNIQUE,
        stock_name  TEXT    NOT NULL,
        market      TEXT    NOT NULL DEFAULT 'A',
        added_at    TEXT    NOT NULL DEFAULT (datetime('now')),
        is_active   INTEGER NOT NULL DEFAULT 1,
        notes       TEXT    DEFAULT '',
        is_special_watch INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS strategies (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL UNIQUE,
        description TEXT    DEFAULT '',
        config_yaml TEXT    NOT NULL,
        is_active   INTEGER NOT NULL DEFAULT 1,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS signals (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code  TEXT    NOT NULL,
        strategy_id INTEGER NOT NULL REFERENCES strategies(id),
        signal_type TEXT    NOT NULL,
        confidence  REAL    DEFAULT 0.0,
        indicator_values TEXT NOT NULL DEFAULT '{}',
        price       REAL    NOT NULL,
        timestamp   TEXT    NOT NULL,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
        is_read     INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE INDEX IF NOT EXISTS idx_signals_stock ON signals(stock_code)""",
    """CREATE INDEX IF NOT EXISTS idx_signals_time  ON signals(timestamp DESC)""",
    """CREATE INDEX IF NOT EXISTS idx_signals_type  ON signals(signal_type)""",
    """CREATE TABLE IF NOT EXISTS kline_cache (
        stock_code  TEXT    NOT NULL,
        period      TEXT    NOT NULL,
        date        TEXT    NOT NULL,
        open        REAL,
        close       REAL,
        high        REAL,
        low         REAL,
        volume      REAL,
        amount      REAL,
        turnover    REAL,
        PRIMARY KEY (stock_code, period, date)
    )""",
    """CREATE INDEX IF NOT EXISTS idx_kline_cache_lookup ON kline_cache(stock_code, period, date)""",
    """CREATE TABLE IF NOT EXISTS stock_groups (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        color       TEXT    NOT NULL DEFAULT '#5470c6',
        sort_order  INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS stock_group_members (
        group_id    INTEGER NOT NULL REFERENCES stock_groups(id) ON DELETE CASCADE,
        stock_code  TEXT    NOT NULL,
        sort_order  INTEGER NOT NULL DEFAULT 0,
        added_at    TEXT    NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (group_id, stock_code)
    )""",
    """CREATE INDEX IF NOT EXISTS idx_group_members_group ON stock_group_members(group_id)""",
]


async def init_db():
    """创建所有表和索引（如果不存在）"""
    import os
    db_path = settings.get_abs_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async with engine.begin() as conn:
        # 开启 WAL 模式以改善并发读写性能
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        for sql in CREATE_TABLES_SQL:
            await conn.execute(text(sql))

        # Migration: add is_special_watch column for existing databases
        try:
            await conn.execute(text(
                "ALTER TABLE watchlist ADD COLUMN is_special_watch INTEGER NOT NULL DEFAULT 0"
            ))
        except Exception:
            pass  # column already exists


async def get_db() -> AsyncSession:
    """依赖注入：获取异步数据库会话"""
    async with async_session() as session:
        yield session