from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated

router = Router()


@router.message(F.new_chat_members)
async def on_new_member(message: Message):
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        await message.answer(f"👋 Добро пожаловать, {member.full_name}!")


@router.chat_member()
async def on_member_update(event: ChatMemberUpdated):
    """Telegram ненадёжно присылает сервисное сообщение left_chat_member,
    поэтому уход участника ловим через обновление его статуса."""
    old, new = event.old_chat_member, event.new_chat_member
    if new.user.is_bot:
        return
    if new.status in ("left", "kicked") and old.status not in ("left", "kicked"):
        await event.bot.send_message(event.chat.id, f"👋 {new.user.full_name} покинул чат.")
