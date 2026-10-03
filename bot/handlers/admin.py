from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.keyboards.inline import (
    main_menu,
    moderation_menu,
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
    get_user,
    count_user_messages,
    add_admin,
    remove_admin,
    list_admins,
)

router = Router()
private = F.chat.type == "private"

HELP_TEXT = (
    "📖 <b>Команды модерации в группе</b> (ответом на сообщение):\n\n"
    "/warn [причина] — предупреждение (3 шт = бан)\n"
    "/warnings — предупреждения пользователя\n"
    "/unwarn — сбросить предупреждения\n"
    "/mute [минуты] — мут (по умолчанию 60)\n"
    "/unmute — снять мут\n"
    "/ban [причина] — бан\n"
    "/unban ID — разбан по ID\n"
    "/report — жалоба от участников\n"
    "/myid — узнать свой ID"
)


class AddModForm(StatesGroup):
    waiting_user_id = State()


class DelModForm(StatesGroup):
    waiting_user_id = State()


async def has_premium_access(message: Message) -> bool:
    if message.from_user.id in ADMIN_IDS:
        return True
    return await is_premium(message.chat.id)


async def user_flags(message: Message) -> tuple[bool, bool]:
    is_admin = message.from_user.id in ADMIN_IDS
    premium = is_admin or await is_premium(message.chat.id)
    return is_admin, premium


# ---------- Главное меню ----------

@router.message(F.text == "🏠 Старт", private)
async def btn_start_menu(message: Message):
    is_admin, premium = await user_flags(message)
    await message.answer(
        f"🏠 <b>Главное меню</b>\n\nПривет, {message.from_user.full_name}! Выбирай раздел:",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )


@router.callback_query(F.data == "menu_back")
async def cb_menu_back(callback):
    """Назад в меню из inline-кнопок (премиум, донат)."""
    is_admin, premium = await user_flags(callback.message)
    await callback.message.answer(
        "Выберите функцию:",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )
    await callback.answer()


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
    is_admin, premium = await user_flags(message)
    await message.answer(
        "📜 <b>Правила чата</b>\n\n"
        "1. Будьте вежливы.\n"
        "2. Без спама и рекламы.\n"
        "3. Без флуда.\n"
        "4. Общайтесь по теме.",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )


# ---------- Модерация (только владелец) ----------

@router.message(F.text == "🛠️ Модерация", private)
async def btn_moderation(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Только для владельца бота.")
        return
    await message.answer(
        "🛠️ <b>Панель модерации</b>\n\n"
        "Управляйте модераторами и смотрите команды. "
        "Модераторы смогут использовать /warn, /mute, /ban в группах.",
        reply_markup=moderation_menu(),
    )


@router.message(F.text == "📖 Команды модерации", private)
async def btn_mod_help(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(HELP_TEXT, reply_markup=moderation_menu())


@router.message(F.text == "➕ Добавить модератора", private)
async def btn_mod_add(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AddModForm.waiting_user_id)
    await message.answer(
        "➕ Отправьте <b>ID</b> пользователя, которого назначить модератором.\n\n"
        "Узнать ID можно командой /myid. Отмена — /cancel"
    )


@router.message(AddModForm.waiting_user_id, F.text.regexp(r"^\d+$"))
async def process_mod_add(message: Message, state: FSMContext):
    user_id = int(message.text.strip())
    if user_id in ADMIN_IDS:
        await message.answer("⚠️ Этот пользователь уже владелец.")
        await state.clear()
        return
    await add_admin(0, user_id, message.from_user.id)
    await state.clear()
    await message.answer(
        f"✅ Пользователь <code>{user_id}</code> назначен модератором всех групп.",
        reply_markup=moderation_menu(),
    )


@router.message(AddModForm.waiting_user_id)
async def process_mod_add_wrong(message: Message):
    await message.answer("⚠️ Нужен числовой ID (например, 123456789) или /cancel.")


@router.message(F.text == "➖ Удалить модератора", private)
async def btn_mod_del(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(DelModForm.waiting_user_id)
    await message.answer(
        "➖ Отправьте <b>ID</b> модератора, которого нужно удалить.\n\nОтмена — /cancel"
    )


@router.message(DelModForm.waiting_user_id, F.text.regexp(r"^\d+$"))
async def process_mod_del(message: Message, state: FSMContext):
    user_id = int(message.text.strip())
    removed = await remove_admin(0, user_id)
    await state.clear()
    if removed:
        await message.answer(
            f"✅ Модератор <code>{user_id}</code> удалён.",
            reply_markup=moderation_menu(),
        )
    else:
        await message.answer(
            "⚠️ Такой модератор не найден.",
            reply_markup=moderation_menu(),
        )


@router.message(DelModForm.waiting_user_id)
async def process_mod_del_wrong(message: Message):
    await message.answer("⚠️ Нужен числовой ID или /cancel.")


@router.message(F.text == "📋 Список модераторов", private)
async def btn_mod_list(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    admins = await list_admins()
    lines = ["📋 <b>Модераторы:</b>", ""]
    for i, a in enumerate(admins, 1):
        scope = "все группы" if a["chat_id"] == 0 else f"чат {a['chat_id']}"
        lines.append(f"{i}. ID <code>{a['user_id']}</code> — {scope}")
    if len(lines) == 2:
        lines.append("Нет назначенных модераторов.")
    await message.answer(
        "\n".join(lines),
        reply_markup=moderation_menu(),
    )


# ---------- Премиум ----------

@router.message(F.text == "⭐ Премиум", private)
async def btn_premium(message: Message):
    is_admin, premium = await user_flags(message)
    until = await get_premium_until(message.chat.id)

    text = "⭐ <b>Премиум-подписка</b>\n\n"
    text += "Что входит:\n"
    text += "• 📈 Расширенная статистика\n"
    text += "• 🧾 Личная статистика\n"
    text += "• 🔧 Кастомные фильтры\n"
    text += "• 🎯 Приоритетная поддержка\n\n"
    text += "<b>Стоимость:</b> 250 ⭐ в месяц\n\n"

    if premium and until:
        text += f"✅ <b>Активна до:</b> {until.strftime('%d.%m.%Y')}"
    elif premium:
        text += "✅ <b>Премиум активен</b> (администратор — бесплатно)."
    else:
        text += "❌ Подписка не активна."

    await message.answer(text, reply_markup=premium_inline_menu(is_admin=is_admin))


@router.message(F.text == "💳 Оплатить 250 ⭐", private)
async def btn_premium_pay(message: Message):
    from bot.handlers.premium import PREMIUM_DAYS, PREMIUM_PRICE
    await message.answer(
        "💳 Оплата премиума — через кнопку «⭐ Премиум» → «Купить 250 ⭐» "
        "(настоящая оплата Telegram Stars)."
    )


# ---------- Статистика ----------

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

    lines = ["📈 <b>Расширенная статистика</b>\n", f"Всего сообщений: <b>{total}</b>"]
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
    await message.answer("\n".join(lines), reply_markup=main_menu())


@router.message(F.text == "🧾 Моя статистика", private)
async def btn_my_stats(message: Message):
    """Премиум-функция: личная статистика пользователя."""
    if not await has_premium_access(message):
        await message.answer(
            "🔒 <b>Личная статистика</b> доступна только с Премиум-подпиской.\n\n"
            "Нажмите «⭐ Премиум», чтобы оформить подписку."
        )
        return

    user = await get_user(message.from_user.id)
    warnings = user["warnings"] if user else 0
    msgs = await count_user_messages(message.from_user.id)
    until = await get_premium_until(message.chat.id)

    text = (
        f"🧾 <b>Твоя статистика</b>\n\n"
        f"<b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>Сообщений в группах:</b> {msgs}\n"
        f"<b>Предупреждений:</b> {warnings}\n"
    )
    if until:
        text += f"<b>Премиум до:</b> {until.strftime('%d.%m.%Y')}"
    await message.answer(text, reply_markup=main_menu())


# ---------- Остальное ----------

@router.message(F.text == "🎯 Поддержка", private)
async def btn_support(message: Message):
    is_admin, premium = await user_flags(message)
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
    is_admin, premium = await user_flags(message)
    await message.answer(
        "Выберите функцию:",
        reply_markup=main_menu(is_admin=is_admin, premium=premium),
    )
