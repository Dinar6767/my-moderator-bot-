from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.inline import main_menu
from core.config import ADMIN_IDS

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        "Я бот-модератор. Выберите функцию:",
        reply_markup=main_menu(is_admin=is_admin),
    )