from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from database import async_session_maker, User
from sqlalchemy import select

class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        if user_id:
            async with async_session_maker() as session:
                user = await session.execute(select(User).where(User.user_id == user_id))
                user = user.scalar_one_or_none()
                lang = user.language if user else 'ru'
            data['lang'] = lang
        else:
            data['lang'] = 'ru'
        return await handler(event, data)
