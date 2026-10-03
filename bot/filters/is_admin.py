from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from core.config import ADMIN_IDS


class IsAdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id

        if user_id in ADMIN_IDS:
            return True

        if isinstance(event, Message):
            chat = event.chat
        else:
            chat = event.message.chat

        if chat.type == "private":
            return False

        member = await chat.get_member(user_id)
        return member.status in ("administrator", "creator")