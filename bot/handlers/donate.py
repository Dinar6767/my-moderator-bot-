from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.keyboards.inline import donate_inline_menu, main_menu
from core.config import ADMIN_IDS
from database.models import activate_premium, get_premium_until

router = Router()

DONATE_LABELS = {
    50: "☕ Угостить кофе",
    100: "⭐ Поддержка бота",
    250: "🚀 Большой вклад",
}


@router.callback_query(F.data.startswith("donate_"))
async def cb_donate(callback: CallbackQuery):
    """Инвойс Telegram Stars на выбранную сумму."""
    try:
        amount = int(callback.data.split("_", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверная сумма.", show_alert=True)
        return

    await callback.message.answer_invoice(
        title=DONATE_LABELS.get(amount, "💰 Донат боту"),
        description="Добровольная поддержка развития бота. Спасибо!",
        payload=f"donate_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label=DONATE_LABELS.get(amount, "Донат"), amount=amount)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    """Telegram требует подтвердить заказ перед оплатой."""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def payment_success(message: Message, bot: Bot):
    """Оплата прошла: активируем премиум или регистрируем донат."""
    payment = message.successful_payment
    amount = payment.total_amount
    currency = payment.currency
    payload = payment.invoice_payload or ""
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or payload.startswith("premium")

    if payload.startswith("premium"):
        # --- покупка премиума ---
        parts = payload.split("_")
        days = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 30
        chat_id = message.chat.id
        await activate_premium(chat_id, days)
        until = await get_premium_until(chat_id)

        await message.answer(
            "⭐ <b>Премиум активирован!</b>\n\n"
            "Теперь вам доступен весь премиум-функционал.\n"
            f"Действует до: <b>{until.strftime('%d.%m.%Y')}</b>",
            reply_markup=main_menu(is_admin=is_admin, premium=True),
        )

        notify = (
            "💎 <b>Покупка премиума!</b>\n\n"
            f"<b>От:</b> {message.from_user.full_name}\n"
            f"<b>Username:</b> @{message.from_user.username or '—'}\n"
            f"<b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"<b>Сумма:</b> {amount} {currency}\n"
            f"<b>Чат:</b> <code>{chat_id}</code>"
        )
    else:
        # --- обычный донат ---
        await message.answer(
            "❤️ <b>Спасибо за поддержку!</b>\n\n"
            "Ваш донат получен — это очень помогает развитию бота.",
            reply_markup=main_menu(is_admin=is_admin, premium=premium),
        )
        notify = (
            "💰 <b>Новый донат!</b>\n\n"
            f"<b>От:</b> {message.from_user.full_name}\n"
            f"<b>Username:</b> @{message.from_user.username or '—'}\n"
            f"<b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"<b>Сумма:</b> {amount} {currency}"
        )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, notify)
        except Exception:
            pass
