from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import async_session_maker, User, Order
from sqlalchemy import select, func
from translations import get_text
from keyboards.main_menu import main_menu_keyboard

router = Router()

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, lang: str = 'ru'):
    user_id = callback.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(select(User).where(User.user_id == user_id))
        user = user.scalar_one()
        orders_count = await session.execute(select(func.count(Order.id)).where(Order.user_id == user_id, Order.status == 'paid'))
        orders_count = orders_count.scalar()
        text = f"<b>{get_text('profile_title', lang)}</b>\n\n"
        text += f"{get_text('balance', lang)}: {user.balance:.2f} USDT\n"
        text += f"{get_text('purchases', lang)}: {orders_count}\n"
        # Реферальная ссылка удалена
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard(lang))
    await callback.answer()
