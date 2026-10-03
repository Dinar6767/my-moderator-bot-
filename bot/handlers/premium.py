from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.inline import premium_inline_menu
from core.config import ADMIN_IDS
from database.models import is_premium, get_premium_until, activate_premium

router = Router()


@router.callback_query(F.data == "premium")
async def cb_premium(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    until = await get_premium_until(chat_id)
    premium = await is_premium(chat_id)
    is_admin = callback.from_user.id in ADMIN_IDS

    text = "⭐ <b>Премиум-подписка</b>\n\n"
    text += "Что входит:\n"
    text += "• 📈 Расширенная статистика\n"
    text += "• 🔧 Кастомные фильтры\n"
    text += "• 🎯 Приоритетная поддержка\n\n"
    text += "<b>Стоимость:</b> 250 ⭐ в месяц\n\n"

    if premium and until:
        text += f"✅ <b>Активна до:</b> {until.strftime('%d.%m.%Y')}"
    elif is_admin:
        text += "✅ Администратор — премиум бесплатно."
    else:
        text += "❌ Подписка не активна."

    await callback.message.edit_text(text, reply_markup=premium_inline_menu(is_admin=is_admin))
    await callback.answer()


@router.callback_query(F.data == "premium_pay")
async def cb_premium_pay(callback: CallbackQuery):
    if callback.from_user.id in ADMIN_IDS:
        chat_id = callback.message.chat.id
        await activate_premium(chat_id, days=30)
        await callback.answer("✅ Премиум активирован на 30 дней.", show_alert=True)
        await cb_premium(callback)
        return
    await callback.answer(
        "Оплата через Telegram Stars скоро будет доступна. "
        "Пока напишите в поддержку.",
        show_alert=True,
    )


@router.callback_query(F.data == "premium_activate_test")
async def cb_premium_activate_test(callback: CallbackQuery):
    """Активировать премиум вручную — только для администраторов бота."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Недостаточно прав.", show_alert=True)
        return
    chat_id = callback.message.chat.id
    await activate_premium(chat_id, days=30)
    await callback.answer("✅ Премиум активирован на 30 дней.", show_alert=True)
    await cb_premium(callback)
