from aiogram import BaseMiddleware
from aiogram.types import Message

from database.models import get_or_create_user, log_message


class DbLoggerMiddleware(BaseMiddleware):
    """Автоматизация: пишет участников и сообщения группы в БД для статистики."""

    async def __call__(self, handler, event, data):
        if (
            isinstance(event, Message)
            and event.chat.type in ("group", "supergroup")
            and event.from_user
            and not event.from_user.is_bot
        ):
            try:
                await get_or_create_user(
                    event.from_user.id,
                    event.from_user.username or "",
                    event.from_user.full_name,
                )
                await log_message(event.from_user.id, event.chat.id)
            except Exception:
                pass  # статистика не должна ронять бота
        return await handler(event, data)
