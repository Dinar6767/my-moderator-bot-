from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def main_menu(is_admin: bool = False, premium: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню. Админ видит всё, премиум — расширенную статистику."""
    rows = []
    if is_admin:
        rows.append([KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📜 Правила")])
    else:
        rows.append([KeyboardButton(text="📜 Правила")])
    rows.append([KeyboardButton(text="⭐ Премиум"), KeyboardButton(text="🎯 Поддержка")])
    if is_admin or premium:
        rows.append([KeyboardButton(text="📈 Расширенная статистика")])
    rows.append([KeyboardButton(text="🏠 Старт")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def moderation_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚠️ Warn"), KeyboardButton(text="🔇 Mute")],
            [KeyboardButton(text="🚫 Ban"), KeyboardButton(text="⬅️ Назад")],
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
    """Inline-кнопки под сообщением о премиуме."""
    rows = [[InlineKeyboardButton(text="💳 Купить 250 ⭐", callback_data="premium_pay")]]
    if is_admin:
        rows.append([
            InlineKeyboardButton(
                text="🧪 Активировать 30 дней (админ)",
                callback_data="premium_activate_test",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Написать в поддержку")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )
