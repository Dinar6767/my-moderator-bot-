from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📜 Правила")],
        [KeyboardButton(text="⭐ Премиум"), KeyboardButton(text="🎯 Поддержка")],
    ]
    if is_admin:
        rows.insert(1, [KeyboardButton(text="🛠️ Модерация")])
    rows.append([KeyboardButton(text="📈 Расширенная статистика")])
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


def support_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Написать в поддержку")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )
