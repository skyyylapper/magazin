from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import get_user
from translations import get_text
from keyboards.main_menu import main_menu_keyboard

router = Router()

# Обработчик кнопки "Баланс"
@router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery, lang: str = 'ru'):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    text = f"💰 {get_text('balance', lang)}: {user.balance:.2f} USDT"
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(lang))
    await callback.answer()

# Обработчик кнопки "Профиль" (покупки и всё остальное)
@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, lang: str = 'ru'):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    from database import async_session_maker
    from models import Order
    from sqlalchemy import select, func
    async with async_session_maker() as session:
        orders_count = await session.execute(select(func.count(Order.id)).where(Order.user_id == user_id, Order.status == 'paid'))
        orders_count = orders_count.scalar()
    text = f"<b>{get_text('profile_title', lang)}</b>\n\n"
    text += f"{get_text('balance', lang)}: {user.balance:.2f} USDT\n"
    text += f"{get_text('purchases', lang)}: {orders_count}\n"
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(lang))
    await callback.answer()
