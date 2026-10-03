from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatPermissions

from database.models import get_or_create_user, add_warning

router = Router()
router.message.filter(F.chat.type.in_({"group", "supergroup"}))

MAX_WARNINGS = 3
MUTE_PERMISSIONS = ChatPermissions(can_send_messages=False)
UNMUTE_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


async def is_admin(message: Message) -> bool:
    member = await message.chat.get_member(message.from_user.id)
    return member.status in ("administrator", "creator")


async def get_target(message: Message):
    """Возвращает пользователя, на чьё сообщение ответили, либо None."""
    if not message.reply_to_message:
        return None
    target = message.reply_to_message.from_user
    if target is None or target.is_bot:
        return None
    return target


async def target_is_admin(message: Message, target_id: int) -> bool:
    member = await message.chat.get_member(target_id)
    return member.status in ("administrator", "creator")


# /warn — предупреждение
@router.message(Command("warn"))
async def cmd_warn(message: Message, command: CommandObject):
    if not await is_admin(message):
        return

    target = await get_target(message)
    if not target:
        await message.answer("⚠️ Ответьте на сообщение пользователя, которому хотите выдать предупреждение.")
        return
    if await target_is_admin(message, target.id):
        await message.answer("⚠️ Нельзя выдать предупреждение администратору.")
        return

    reason = command.args or "без причины"
    await get_or_create_user(target.id, target.username or "", target.full_name)
    count = await add_warning(target.id)

    if count >= MAX_WARNINGS:
        await message.bot.ban_chat_member(message.chat.id, target.id)
        await message.answer(
            f"🚫 {target.full_name} получил {count}/{MAX_WARNINGS} предупреждений и был забанен.\n"
            f"Причина: {reason}"
        )
    else:
        await message.answer(
            f"⚠️ {target.full_name} получил предупреждение {count}/{MAX_WARNINGS}.\n"
            f"Причина: {reason}"
        )


# /mute — мут на N минут (по умолчанию 60)
@router.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject):
    if not await is_admin(message):
        return

    target = await get_target(message)
    if not target:
        await message.answer("🔇 Ответьте на сообщение пользователя, которого нужно замутить.")
        return
    if await target_is_admin(message, target.id):
        await message.answer("⚠️ Нельзя замутить администратора.")
        return

    minutes = 60
    if command.args and command.args.split()[0].isdigit():
        minutes = max(1, int(command.args.split()[0]))

    until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    await message.bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=target.id,
        permissions=MUTE_PERMISSIONS,
        until_date=until,
    )
    await message.answer(f"🔇 {target.full_name} замучен на {minutes} мин.")


# /unmute — снять мут
@router.message(Command("unmute"))
async def cmd_unmute(message: Message):
    if not await is_admin(message):
        return

    target = await get_target(message)
    if not target:
        await message.answer("🔊 Ответьте на сообщение пользователя, которого нужно размутить.")
        return

    await message.bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=target.id,
        permissions=UNMUTE_PERMISSIONS,
    )
    await message.answer(f"🔊 {target.full_name} размучен.")


# /ban — бан
@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    if not await is_admin(message):
        return

    target = await get_target(message)
    if not target:
        await message.answer("🚫 Ответьте на сообщение пользователя, которого нужно забанить.")
        return
    if await target_is_admin(message, target.id):
        await message.answer("⚠️ Нельзя забанить администратора.")
        return

    reason = command.args or "без причины"
    await message.bot.ban_chat_member(
        chat_id=message.chat.id,
        user_id=target.id,
        revoke_messages=True,
    )
    await message.answer(f"🚫 {target.full_name} забанен.\nПричина: {reason}")


# /unban — разбан по ID
@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject):
    if not await is_admin(message):
        return

    if not command.args or not command.args.strip().isdigit():
        await message.answer("Использование: /unban 123456789")
        return

    user_id = int(command.args.strip())
    await message.bot.unban_chat_member(message.chat.id, user_id)
    await message.answer(f"✅ Пользователь {user_id} разбанен.")
