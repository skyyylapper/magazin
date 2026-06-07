from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import async_session_maker, get_partner_by_id, create_partner, get_pending_manual_topups, confirm_manual_topup, get_pending_withdraw_requests, approve_withdraw_request
from models import Partner
from sqlalchemy import select
from config import ADMIN_IDS

router = Router()

def is_admin(user_id): return user_id in ADMIN_IDS

async def list_partners(message: Message):
    async with async_session_maker() as session:
        partners = await session.execute(select(Partner))
        partners = partners.scalars().all()
        if not partners:
            await message.answer("Нет партнёров. Добавьте командой /add_partner")
            return
        text = "🤝 Список партнёров:\n"
        for p in partners:
            text += f"ID: {p.id} | {p.name} | Баланс: {p.balance} USDT\n"
        await message.answer(text)

@router.message(Command("partners"))
async def partners_command(message: Message):
    if not is_admin(message.from_user.id): return
    await list_partners(message)

@router.message(Command("add_partner"))
async def add_partner(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /add_partner <telegram_id> <имя>")
        return
    _, tele_id_str, name = parts
    tele_id = int(tele_id_str)
    await create_partner(tele_id, name)
    await message.answer(f"Партнёр {name} добавлен. Его ссылка: partner_{tele_id}")

async def list_manual_topups(message: Message):
    topups = await get_pending_manual_topups()
    if not topups:
        await message.answer("Нет ручных пополнений на проверке.")
        return
    for t in topups:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_manual_{t.id}"),
             InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_manual_{t.id}")]
        ])
        await message.answer(
            f"Пользователь: {t.user_id}\nСумма: {t.amount} USDT\nTXID: {t.transaction_hash}",
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("confirm_manual_"))
async def confirm_manual_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    manual_id = int(callback.data.split("_")[2])
    await confirm_manual_topup(manual_id)
    await callback.message.edit_text("Пополнение подтверждено.")
    await callback.answer()

@router.callback_query(F.data.startswith("reject_manual_"))
async def reject_manual_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    # можно просто удалить заявку или пометить rejected
    await callback.message.edit_text("Заявка отклонена.")
    await callback.answer()

async def list_withdraw_requests(message: Message):
    reqs = await get_pending_withdraw_requests()
    if not reqs:
        await message.answer("Нет заявок на вывод.")
        return
    for r in reqs:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_withdraw_{r.id}"),
             InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_withdraw_{r.id}")]
        ])
        await message.answer(
            f"Партнёр ID: {r.partner_id}\nСумма: {r.amount} USDT\nАдрес: {r.wallet_address}",
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("approve_withdraw_"))
async def approve_withdraw_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    req_id = int(callback.data.split("_")[2])
    await approve_withdraw_request(req_id)
    await callback.message.edit_text("Заявка одобрена. Средства списаны с баланса партнёра.")
    await callback.answer()

@router.callback_query(F.data.startswith("reject_withdraw_"))
async def reject_withdraw_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("Заявка отклонена.")
    await callback.answer()
