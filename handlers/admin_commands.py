from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import get_partner_by_telegram_id
from config import ADMIN_IDS
from keyboards.admin_menu import admin_main_keyboard, partner_main_keyboard

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("start"))
async def admin_start(message: Message):
    user_id = message.from_user.id
    if is_admin(user_id):
        await message.answer("👑 Добро пожаловать в админ-панель!", reply_markup=admin_main_keyboard('ru'))
    else:
        partner = await get_partner_by_telegram_id(user_id)
        if partner:
            await message.answer(f"🤝 Здравствуйте, {partner.name}! Вы вошли как партнёр.", reply_markup=partner_main_keyboard('ru'))
        else:
            await message.answer("У вас нет доступа к этому боту.")

@router.message(Command("help"))
async def admin_help(message: Message):
    user_id = message.from_user.id
    if is_admin(user_id):
        text = "Доступные команды:\n/start - главное меню\n/products - управление товарами\n/users - список пользователей\n/partners - управление партнёрами\n/manual_topups - ручные пополнения\n/withdraw_requests - заявки на вывод"
    else:
        partner = await get_partner_by_telegram_id(user_id)
        if partner:
            text = "Ваши возможности:\n/balance - партнёрский баланс\n/referral_link - ваша ссылка\n/stats - статистика\n/withdraw - запрос вывода"
        else:
            text = "Доступ запрещён."
    await message.answer(text)
