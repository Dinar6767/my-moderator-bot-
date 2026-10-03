from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from core.config import ADMIN_IDS


class IsOwnerFilter(BaseFilter):
    """Пропускает только владельца бота (из ADMIN_IDS)."""

    async def __call__(self, event) -> bool:
        if isinstance(event, Message):
            return event.from_user.id in ADMIN_IDS
        if isinstance(event, CallbackQuery):
            return event.from_user.id in ADMIN_IDS
        return False