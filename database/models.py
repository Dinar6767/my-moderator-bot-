from datetime import datetime, timedelta
from database.session import get_pool


# ---------- Пользователи ----------

async def get_or_create_user(user_id: int, username: str, full_name: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if row:
            return dict(row)
        await conn.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES ($1, $2, $3)",
            user_id, username, full_name,
        )
        return {"user_id": user_id, "warnings": 0}


async def add_warning(user_id: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE users SET warnings = warnings + 1 WHERE user_id = $1 RETURNING warnings",
            user_id,
        )
        return row["warnings"] if row else 0


# ---------- Сообщения (для статистики) ----------

async def log_message(user_id: int, chat_id: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (user_id, chat_id) VALUES ($1, $2)",
            user_id, chat_id,
        )


async def get_top_users(chat_id: int, limit: int = 10) -> list[dict]:
    """Топ активных участников за всё время."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.full_name, u.username, COUNT(m.id) AS cnt
            FROM messages m
            JOIN users u ON u.user_id = m.user_id
            WHERE m.chat_id = $1
            GROUP BY u.user_id, u.full_name, u.username
            ORDER BY cnt DESC
            LIMIT $2
        """, chat_id, limit)
        return [dict(r) for r in rows]


async def get_activity_week(chat_id: int) -> list[dict]:
    """Активность за последние 7 дней по дням."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DATE(created_at) AS day, COUNT(*) AS cnt
            FROM messages
            WHERE chat_id = $1 AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY day
            ORDER BY day
        """, chat_id)
        return [dict(r) for r in rows]


async def get_total_messages(chat_id: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) AS cnt FROM messages WHERE chat_id = $1",
            chat_id,
        )
        return row["cnt"] if row else 0


async def get_top_violators(chat_id: int, limit: int = 10) -> list[dict]:
    """Топ нарушителей по количеству warn."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT full_name, username, warnings
            FROM users
            WHERE warnings > 0
            ORDER BY warnings DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


# ---------- Премиум ----------

async def is_premium(chat_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT until_date FROM premium WHERE chat_id = $1",
            chat_id,
        )
        if not row:
            return False
        return row["until_date"] > datetime.now()


async def activate_premium(chat_id: int, days: int = 30) -> None:
    pool = await get_pool()
    until = datetime.now() + timedelta(days=days)
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO premium (chat_id, until_date)
            VALUES ($1, $2)
            ON CONFLICT (chat_id) DO UPDATE
            SET until_date = $2
        """, chat_id, until)


async def get_premium_until(chat_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT until_date FROM premium WHERE chat_id = $1",
            chat_id,
        )
        return row["until_date"] if row else None
async def get_user(user_id: int) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None


async def reset_warnings(user_id: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET warnings = 0 WHERE user_id = $1", user_id
        )

async def add_admin(chat_id: int, user_id: int, added_by: int) -> None:
    """chat_id = 0 означает модератора всех групп."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO chat_admins (chat_id, user_id, added_by)
               VALUES ($1, $2, $3)
               ON CONFLICT (chat_id, user_id) DO NOTHING""",
            chat_id, user_id, added_by,
        )


async def remove_admin(chat_id: int, user_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM chat_admins WHERE chat_id = $1 AND user_id = $2",
            chat_id, user_id,
        )
        return result == "DELETE 1"


async def is_chat_admin(chat_id: int, user_id: int) -> bool:
    """Глобальный модератор (chat_id=0) действует везде."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT 1 FROM chat_admins
               WHERE user_id = $1 AND (chat_id = $2 OR chat_id = 0)""",
            user_id, chat_id,
        )
        return row is not None


async def list_admins() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM chat_admins ORDER BY created_at")


async def count_user_messages(user_id: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM messages WHERE user_id = $1", user_id
        ) or 0
