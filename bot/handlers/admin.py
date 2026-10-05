from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards.inline import (
    main_menu,
    moderation_menu,
    premium_menu,
    premium_inline_menu,
    donate_inline_menu,
    support_menu,
)
from core.config import ADMIN_IDS
from database.models import (
    is_premium,
    get_premium_until,
    get_total_messages,
    get_top_users,
    get_top_violators,
    get_activity_week,
)

router = Router()
private = F.chat.type == "private"


async def has_premium_access(message: Message) -> bool:
    """Админу — всё бесплатно, остальным — только при активном премиуме."""
    if message.from_user.id in ADMIN_IDS:
        return True
    return await is_premium(message.chat.id)


@router.message(F.text == "🏠 Старт", private)
async def btn_start_menu(message: Message):
    """Возврат в главное меню."""
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or await is_premium(message.chat.id)
    await message.answer(
        f"🏠 <b>Главное меню</b>\n\nПривет, {message.from_user.full_name}! Выбирай раздел:",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )


@router.message(F.text == "📊 Статистика", private)
async def btn_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Только для администраторов")
        return
    chat_id = message.chat.id
    total = await get_total_messages(chat_id)
    top = await get_top_users(chat_id, limit=5)

    lines = [f"📊 <b>Статистика чата</b>\n\nВсего сообщений: <b>{total}</b>"]
    if top:
        lines.append("\n<b>Топ-5 участников:</b>")
        for i, u in enumerate(top, 1):
            lines.append(f"{i}. {u['full_name']} — {u['cnt']}")
    else:
        lines.append("\nПока нет данных — добавьте бота в группу.")
    await message.answer(
        "\n".join(lines),
        reply_markup=main_menu(is_admin=True, premium=True),
    )


@router.message(F.text == "📜 Правила", private)
async def btn_rules(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or await is_premium(message.chat.id)
    await message.answer(
        "📜 <b>Правила чата</b>\n\n"
        "1. Будьте вежливы.\n"
        "2. Без спама и рекламы.\n"
        "3. Без флуда.\n"
        "4. Общайтесь по теме.",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )


@router.message(F.text == "🛠️ Модерация", private)
async def btn_moderation(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Только для администраторов")
        return
    await message.answer(
        "🛠️ <b>Модерация</b>\n\n"
        "Команды в группе (ответом на сообщение):\n"
        "/warn [причина] — предупреждение\n"
        "/warnings — предупреждения пользователя\n"
        "/unwarn — сбросить предупреждения\n"
        "/mute [минуты] — мут (по умолч. 60)\n"
        "/unmute — снять мут\n"
        "/ban [причина] — бан\n"
        "/unban ID — разбан\n"
        "/report — жалоба на сообщение",
        reply_markup=moderation_menu(),
    )


@router.message(F.text == "⭐ Премиум", private)
async def btn_premium(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or await is_premium(message.chat.id)
    until = await get_premium_until(message.chat.id)

    text = "⭐ <b>Премиум-подписка</b>\n\n"
    text += "Что входит:\n"
    text += "• 📈 Расширенная статистика\n"
    text += "• 🔧 Кастомные фильтры\n"
    text += "• 🎯 Приоритетная поддержка\n\n"
    text += "<b>Стоимость:</b> 250 ⭐ в месяц\n\n"

    if premium and until:
        text += f"✅ <b>Активна до:</b> {until.strftime('%d.%m.%Y')}"
    elif premium:
        text += "✅ <b>Премиум активен</b> (администратор — бесплатно)."
    else:
        text += "❌ Подписка не активна."

    await message.answer(
        text,
        reply_markup=premium_inline_menu(is_admin=is_admin),
    )


@router.message(F.text == "💳 Оплатить 250 ⭐", private)
async def btn_premium_pay(message: Message):
    await message.answer("Оплата временно недоступна. Свяжитесь с поддержкой.")


@router.message(F.text == "📈 Расширенная статистика", private)
async def btn_adv_stats(message: Message):
    if not await has_premium_access(message):
        await message.answer(
            "🔒 <b>Расширенная статистика</b> доступна только с Премиум-подпиской.\n\n"
            "Нажмите «⭐ Премиум», чтобы оформить подписку."
        )
        return

    chat_id = message.chat.id
    total = await get_total_messages(chat_id)
    top = await get_top_users(chat_id, limit=10)
    week = await get_activity_week(chat_id)
    violators = await get_top_violators(chat_id, limit=5)

    lines = [
        "📈 <b>Расширенная статистика</b>\n",
        f"Всего сообщений: <b>{total}</b>",
    ]
    if week:
        lines.append("\n<b>Активность за неделю:</b>")
        for row in week:
            lines.append(f"• {row['day']}: {row['cnt']} сообщ.")
    if top:
        lines.append("\n<b>Топ-10 участников:</b>")
        for i, u in enumerate(top, 1):
            lines.append(f"{i}. {u['full_name']} — {u['cnt']}")
    if violators:
        lines.append("\n<b>Топ нарушителей:</b>")
        for u in violators:
            lines.append(f"• {u['full_name']} — {u['warnings']} предупр.")
    await message.answer(
        "\n".join(lines),
        reply_markup=main_menu(),
    )


@router.message(F.text == "🎯 Поддержка", private)
async def btn_support(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or await is_premium(message.chat.id)
    await message.answer(
        "🎯 <b>Приоритетная поддержка</b>\n\n"
        "Мы отвечаем в течение 1 часа.\n"
        "Нажмите кнопку ниже, чтобы написать нам.",
        reply_markup=support_menu(),
    )


@router.message(F.text == "💰 Донат", private)
async def btn_donate(message: Message):
    await message.answer(
        "💰 <b>Поддержать бота</b>\n\n"
        "Бот бесплатный, но любой донат помогает его развивать. "
        "Выберите сумму — оплата в Telegram Stars:",
        reply_markup=donate_inline_menu(),
    )


@router.message(F.text == "⬅️ Назад", private)
async def btn_back(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or await is_premium(message.chat.id)
    await message.answer(
        "Выберите функцию:",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )
