from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.inline import main_menu
from core.config import ADMIN_IDS
from database.models import is_premium

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or await is_premium(message.chat.id)
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        "Я бот-модератор. Выберите функцию:",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(
        f"🆔 <b>Ваш ID:</b> <code>{message.from_user.id}</code>",
        reply_markup=main_menu(
            is_admin=message.from_user.id in ADMIN_IDS,
            premium=message.from_user.id in ADMIN_IDS or await is_premium(message.chat.id),
        ),
    )
