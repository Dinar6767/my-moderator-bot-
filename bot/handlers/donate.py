from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.keyboards.inline import donate_inline_menu
from core.config import ADMIN_IDS

router = Router()

DONATE_LABELS = {
    50: "☕ Угостить кофе",
    100: "⭐ Поддержка бота",
    250: "🚀 Большой вклад",
}


@router.callback_query(F.data.startswith("donate_"))
async def cb_donate(callback: CallbackQuery):
    """Отправляет инвойс Telegram Stars на выбранную сумму."""
    try:
        amount = int(callback.data.split("_", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверная сумма.", show_alert=True)
        return

    await callback.message.answer_invoice(
        title=DONATE_LABELS.get(amount, "💰 Донат боту"),
        description="Добровольная поддержка развития бота. Спасибо!",
        payload=f"donate_{amount}",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=DONATE_LABELS.get(amount, "Донат"), amount=amount)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    """Telegram требует подтвердить заказ перед оплатой."""
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def payment_success(message: Message, bot: Bot):
    """Оплата прошла — благодарим и уведомляем владельца бота."""
    payment = message.successful_payment
    amount = payment.total_amount
    currency = payment.currency

    await message.answer(
        "❤️ <b>Спасибо за поддержку!</b>\n\n"
        "Ваш донат получен — это очень помогает развитию бота.",
        reply_markup=donate_inline_menu(),
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
