from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from database import async_session_maker, User
from sqlalchemy import select, func
from translations import get_text
import config

router = Router()

@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery, lang: str = 'ru'):
    user_id = callback.from_user.id
    async with async_session_maker() as session:
        # кол-во приглашённых (у кого referrer_id = текущий user_id)
        invited_count = await session.execute(select(func.count(User.id)).where(User.referrer_id == user_id))
        invited_count = invited_count.scalar()
        # сумма заработанных бонусов? можно хранить отдельно, но для простоты считаем из баланса? нет, баланс общий
        # пока просто показываем ссылку и количество
        text = f"<b>{get_text('referral_title', lang)}</b>\n\n"
        text += f"{get_text('your_referral_link', lang)}:\n"
        text += f"https://t.me/{config.MAIN_BOT_USERNAME}?start={user_id}\n\n"
        text += f"{get_text('invited_count', lang)}: {invited_count}\n"
        text += f"{get_text('referral_bonus_text', lang)}: 50% от пополнения приглашённого"
        await callback.message.edit_text(text)
    await callback.answer()
