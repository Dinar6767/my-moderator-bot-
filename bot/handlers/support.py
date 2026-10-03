from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.keyboards.inline import main_menu
from core.config import ADMIN_IDS

router = Router()


class SupportForm(StatesGroup):
    waiting_for_message = State()


@router.message(F.text == "✍️ Написать в поддержку")
async def btn_support_write(message: Message, state: FSMContext):
    await state.set_state(SupportForm.waiting_for_message)
    await message.answer("✍️ Напишите ваше сообщение — оно придёт в поддержку.\n\nДля отмены отправьте /cancel")


@router.message(SupportForm.waiting_for_message, Command("cancel"))
async def cmd_cancel_in_state(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


@router.message(SupportForm.waiting_for_message, F.text)
async def process_support_message(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    text = (
        f"🎯 <b>Новое обращение в поддержку</b>\n\n"
        f"<b>От:</b> {message.from_user.full_name}\n"
        f"<b>Username:</b> @{message.from_user.username or '—'}\n"
        f"<b>ID:</b> <code>{message.from_user.id}</code>\n\n"
        f"<b>Сообщение:</b>\n{message.text}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass

    await message.answer(
        "✅ Сообщение отправлено в поддержку. Ответим в течение 1 часа.",
        reply_markup=main_menu(),
    )


@router.message(SupportForm.waiting_for_message)
async def support_wrong_content(message: Message):
    await message.answer("Пожалуйста, отправьте текст или /cancel для отмены.")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())
