import asyncpg
from core.config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global _pool
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не задан. Добавьте переменную на Railway.")
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     BIGINT PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                warnings    INT DEFAULT 0,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS chats (
                chat_id     BIGINT PRIMARY KEY,
                title       TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT,
                chat_id     BIGINT,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS violations (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT,
                chat_id     BIGINT,
                reason      TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS premium (
                chat_id     BIGINT PRIMARY KEY,
                until_date  TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_admins (
                chat_id     BIGINT NOT NULL,
                user_id     BIGINT NOT NULL,
                added_by    BIGINT,
                created_at  TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (chat_id, user_id)
            );
        """)


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("БД не инициализирована.")
    return _pool


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
