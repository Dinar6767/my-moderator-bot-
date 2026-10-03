from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def main_menu(is_admin: bool = False, premium: bool = False) -> ReplyKeyboardMarkup:
    """Обычное меню у всех; премиум добавляет функции; админ — полный доступ."""
    rows = []
    if is_admin:
        rows.append([KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📜 Правила")])
    else:
        rows.append([KeyboardButton(text="📜 Правила")])
    rows.append([KeyboardButton(text="⭐ Премиум"), KeyboardButton(text="🎯 Поддержка")])
    if is_admin or premium:
        rows.append([KeyboardButton(text="📈 Расширенная статистика")])
        rows.append([KeyboardButton(text="🧾 Моя статистика")])
    rows.append([KeyboardButton(text="💰 Донат"), KeyboardButton(text="🏠 Старт")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def moderation_menu() -> ReplyKeyboardMarkup:
    """Панель модерации — видит только владелец (ADMIN_IDS)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить модератора"), KeyboardButton(text="➖ Удалить модератора")],
            [KeyboardButton(text="📋 Список модераторов"), KeyboardButton(text="📖 Команды модерации")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def premium_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Оплатить 250 ⭐")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def premium_inline_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="💳 Купить 250 ⭐", callback_data="premium_pay")]]
    if is_admin:
        rows.append([
            InlineKeyboardButton(
                text="🧪 Активировать 30 дней (админ)",
                callback_data="premium_activate_test",
            )
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def donate_inline_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ 50 ⭐ — угостить кофе", callback_data="donate_50")],
        [InlineKeyboardButton(text="⭐ 100 ⭐ — поддержать", callback_data="donate_100")],
        [InlineKeyboardButton(text="🚀 250 ⭐ — большой вклад", callback_data="donate_250")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu_back")],
    ])


def support_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Написать в поддержку")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )
