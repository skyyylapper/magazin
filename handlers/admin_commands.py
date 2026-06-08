from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
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
        await message.answer("👑 Добро пожаловать в админ-панель!", reply_markup=admin_main_keyboard('ru'), parse_mode=None)
    else:
        partner = await get_partner_by_telegram_id(user_id)
        if partner:
            await message.answer(f"🤝 Здравствуйте, {partner.name}! Вы вошли как партнёр.", reply_markup=partner_main_keyboard('ru'), parse_mode=None)
        else:
            await message.answer("У вас нет доступа к этому боту.", parse_mode=None)

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
    await message.answer(text, parse_mode=None)

# Обработчики callback-кнопок (без parse_mode)
@router.callback_query(F.data == "admin_products")
async def admin_products_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    from handlers.admin_products import list_products_for_admin
    await list_products_for_admin(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    from handlers.admin_users import list_users
    await list_users(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_partners")
async def admin_partners_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    from handlers.admin_partners import list_partners
    await list_partners(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_manual_topups")
async def admin_manual_topups_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    from handlers.admin_partners import list_manual_topups
    await list_manual_topups(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_withdraw_requests")
async def admin_withdraw_requests_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    from handlers.admin_partners import list_withdraw_requests
    await list_withdraw_requests(callback.message)
    await callback.answer()
