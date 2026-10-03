from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from core.config import ADMIN_IDS
from database.models import is_premium


class IsPremiumFilter(BaseFilter):
    """Пропускает владельца бота или активного премиум-пользователя."""

    async def __call__(self, event) -> bool:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if not user_id:
            return False

        if user_id in ADMIN_IDS:
            return True

        return await is_premium(user_id)