from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards.inline import main_menu, moderation_menu, premium_menu, support_menu
from core.config import ADMIN_IDS

router = Router()
private = F.chat.type == "private"


@router.message(F.text == "📊 Статистика", private)
async def btn_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Только для администраторов")
        return
    await message.answer(
        "📊 <b>Статистика</b>\n\n"
        "Здесь будет отчёт по вашему чату.\n"
        "Пока функция в разработке.",
        reply_markup=main_menu(),
    )


@router.message(F.text == "📜 Правила", private)
async def btn_rules(message: Message):
    await message.answer(
        "📜 <b>Правила чата</b>\n\n"
        "1. Будьте вежливы.\n"
        "2. Без спама и рекламы.\n"
        "3. Без флуда.\n"
        "4. Общайтесь по теме.",
        reply_markup=main_menu(),
    )


@router.message(F.text == "🛠️ Модерация", private)
async def btn_moderation(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Только для администраторов")
        return
    await message.answer(
        "🛠️ <b>Модерация</b>\n\nВыберите действие:",
        reply_markup=moderation_menu(),
    )


@router.message(F.text == "⭐ Премиум", private)
async def btn_premium(message: Message):
    await message.answer(
        "⭐ <b>Премиум-подписка</b>\n\n"
        "Что входит:\n"
        "• Расширенная статистика\n"
        "• Кастомные фильтры\n"
        "• Приоритетная поддержка\n\n"
        "Стоимость: 250 ⭐ в месяц",
        reply_markup=premium_menu(),
    )


@router.message(F.text == "💳 Оплатить 250 ⭐", private)
async def btn_premium_pay(message: Message):
    await message.answer("Оплата временно недоступна. Свяжитесь с поддержкой.")


@router.message(F.text == "📈 Расширенная статистика", private)
async def btn_adv_stats(message: Message):
    await message.answer(
        "📈 <b>Расширенная статистика</b>\n\n"
        "• Топ-10 активных участников\n"
        "• График активности за неделю\n"
        "• Топ нарушителей\n\n"
        "Функция доступна в Премиум-подписке.",
        reply_markup=main_menu(),
    )


@router.message(F.text == "🎯 Поддержка", private)
async def btn_support(message: Message):
    await message.answer(
        "🎯 <b>Приоритетная поддержка</b>\n\n"
        "Мы отвечаем в течение 1 часа.\n"
        "Нажмите кнопку ниже, чтобы написать нам.",
        reply_markup=support_menu(),
    )


@router.message(F.text == "⬅️ Назад", private)
async def btn_back(message: Message):
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer("Выберите функцию:", reply_markup=main_menu(is_admin=is_admin))
