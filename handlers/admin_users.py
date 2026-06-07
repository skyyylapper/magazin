from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import async_session_maker, get_user, update_user_balance
from models import User
from sqlalchemy import select
from config import ADMIN_IDS

router = Router()

def is_admin(user_id): return user_id in ADMIN_IDS

@router.message(Command("users"))
async def list_users(message: Message):
    if not is_admin(message.from_user.id): return
    async with async_session_maker() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
        if not users:
            await message.answer("Нет пользователей.")
            return
        text = "👥 Список пользователей:\n"
        for u in users[:20]:
            text += f"ID: {u.user_id} | {u.first_name} | Баланс: {u.balance} USDT\n"
        await message.answer(text)

@router.message(Command("edit_balance"))
async def edit_balance_start(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /edit_balance <user_id> <сумма>")
        return
    _, user_id_str, amount_str = parts
    try:
        user_id = int(user_id_str)
        amount = float(amount_str)
        await update_user_balance(user_id, amount)
        await message.answer(f"Баланс пользователя {user_id} изменён на {amount} USDT")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def list_users(message: Message):
    from database import async_session_maker
    from models import User
    from sqlalchemy import select
    async with async_session_maker() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
        if not users:
            await message.answer("Нет пользователей.")
            return
        text = "👥 Список пользователей:\n"
        for u in users[:20]:
            text += f"ID: {u.user_id} | {u.first_name} | Баланс: {u.balance} USDT\n"
        await message.answer(text)
