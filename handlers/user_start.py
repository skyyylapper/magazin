from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import get_user, create_user
from models import Partner
from sqlalchemy import select
from database import async_session_maker
from keyboards.main_menu import main_menu_keyboard
from translations import get_text
import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, lang: str = 'ru'):
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None
    user_id = message.from_user.id

    user = await get_user(user_id)
    if not user:
        partner_id = None
        referrer_id = None
        if ref_code:
            if ref_code.startswith('partner_'):
                try:
                    partner_telegram_id = int(ref_code.split('_')[1])
                    async with async_session_maker() as session:
                        partner = await session.execute(select(Partner).where(Partner.telegram_id == partner_telegram_id))
                        partner = partner.scalar_one_or_none()
                        if partner:
                            partner_id = partner.id
                except:
                    pass
            else:
                try:
                    referrer_id = int(ref_code)
                except:
                    pass
        user = await create_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language=lang,
            referrer_id=referrer_id,
            partner_id=partner_id
        )
    else:
        if user.language != lang:
            async with async_session_maker() as session:
                user.language = lang
                await session.commit()

    await message.answer(
        get_text('welcome', lang),
        reply_markup=main_menu_keyboard(lang)
    )
