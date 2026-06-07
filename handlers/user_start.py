from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import async_session_maker, User, Partner
from models import User, Partner
from sqlalchemy import select
from keyboards.main_menu import main_menu_keyboard
from translations import get_text
import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, lang: str = 'ru'):
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None

    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(select(User).where(User.user_id == user_id))
        user = user.scalar_one_or_none()
        if not user:
            # Регистрация
            partner_id = None
            referrer_id = None
            if ref_code:
                # проверяем, является ли ref_code партнёрской ссылкой (например, partner_123)
                if ref_code.startswith('partner_'):
                    partner_telegram_id = int(ref_code.split('_')[1])
                    partner = await session.execute(select(Partner).where(Partner.telegram_id == partner_telegram_id))
                    partner = partner.scalar_one_or_none()
                    if partner:
                        partner_id = partner.id
                else:
                    # обычная реферальная ссылка - user_id пригласившего
                    try:
                        referrer_id = int(ref_code)
                    except:
                        pass
            new_user = User(
                user_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language=lang,
                partner_id=partner_id,
                referrer_id=referrer_id
            )
            session.add(new_user)
            await session.commit()
        else:
            # Если пользователь уже есть, обновляем язык при необходимости
            if user.language != lang:
                user.language = lang
                await session.commit()
    await message.answer(
        get_text('welcome', lang),
        reply_markup=main_menu_keyboard(lang)
    )
