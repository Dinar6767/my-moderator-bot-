from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatPermissions

from core.config import ADMIN_IDS
from database.models import (
    get_or_create_user,
    add_warning,
    get_user,
    reset_warnings,
)

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


# /warnings — посмотреть предупреждения пользователя
@router.message(Command("warnings"))
async def cmd_warnings(message: Message):
    target = await get_target(message)
    if not target:
        await message.answer("ℹ️ Ответьте на сообщение пользователя, чтобы увидеть его предупреждения.")
        return

    user = await get_user(target.id)
    count = user["warnings"] if user else 0
    await message.answer(f"⚠️ У {target.full_name}: {count}/{MAX_WARNINGS} предупреждений.")


# /unwarn — сбросить предупреждения пользователя
@router.message(Command("unwarn"))
async def cmd_unwarn(message: Message):
    if not await is_admin(message):
        return

    target = await get_target(message)
    if not target:
        await message.answer("⚠️ Ответьте на сообщение пользователя, чьи предупреждения нужно сбросить.")
        return

    await reset_warnings(target.id)
    await message.answer(f"✅ Предупреждения {target.full_name} сброшены.")


# /report — жалоба на сообщение администраторам
@router.message(Command("report"))
async def cmd_report(message: Message):
    if not message.reply_to_message:
        await message.answer("🚩 Ответьте на сообщение, на которое хотите пожаловаться.")
        return

    reported = message.reply_to_message
    if not reported.from_user:
        await message.answer("🚩 На это сообщение пожаловаться нельзя.")
        return

    if reported.from_user.id == message.from_user.id:
        await message.answer("🚩 Нельзя жаловаться на самого себя.")
        return

    chat_title = message.chat.title or "чат"
    text = (
        f"🚩 <b>Жалоба</b>\n\n"
        f"<b>Чат:</b> {chat_title}\n"
        f"<b>От:</b> {message.from_user.full_name} (id <code>{message.from_user.id}</code>)\n"
        f"<b>На:</b> {reported.from_user.full_name} (id <code>{reported.from_user.id}</code>)\n\n"
        f"Оригинальное сообщение переслано ниже."
    )
    sent = 0
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, text)
            await message.bot.forward_message(admin_id, message.chat.id, reported.message_id)
            sent += 1
        except Exception:
            pass

    if sent:
        await message.answer("🚩 Жалоба отправлена администраторам.")
    else:
        await message.answer("⚠️ Не удалось доставить жалобу — администраторы не найдены.")
