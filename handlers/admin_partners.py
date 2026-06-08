from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import async_session_maker, get_pending_manual_topups, get_pending_withdraw_requests, confirm_manual_topup, approve_withdraw_request
from models import Partner
from sqlalchemy import select
from config import ADMIN_IDS

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("add_partner"))
async def add_partner(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /add_partner <telegram_id> <имя>")
        return
    _, tele_id_str, name = parts
    try:
        tele_id = int(tele_id_str)
    except:
        await message.answer("Ошибка: telegram_id должно быть числом.")
        return
    async with async_session_maker() as session:
        existing = await session.execute(select(Partner).where(Partner.telegram_id == tele_id))
        if existing.scalar_one_or_none():
            await message.answer("Партнёр с таким Telegram ID уже существует.")
            return
        partner = Partner(telegram_id=tele_id, name=name, referral_link=f"partner_{tele_id}")
        session.add(partner)
        await session.commit()
    await message.answer(f"✅ Партнёр {name} добавлен. Его ссылка: partner_{tele_id}")

@router.message(Command("partners"))
async def list_partners(message: Message):
    if not is_admin(message.from_user.id):
        return
    async with async_session_maker() as session:
        partners = await session.execute(select(Partner))
        partners = partners.scalars().all()
        if not partners:
            await message.answer("Нет партнёров.")
            return
        text = "🤝 Список партнёров:\n"
        for p in partners:
            text += f"ID: {p.id} | {p.name} | Баланс: {p.balance} USDT | Телеграм ID: {p.telegram_id}\n"
        await message.answer(text)

@router.message(Command("manual_topups"))
async def list_manual_topups(message: Message):
    if not is_admin(message.from_user.id):
        return
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
            f"💰 Заявка #{t.id}\nПользователь: {t.user_id}\nСумма: {t.amount} USDT\nTXID: {t.transaction_hash}",
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("confirm_manual_"))
async def confirm_manual_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    manual_id = int(callback.data.split("_")[2])
    await confirm_manual_topup(manual_id)
    await callback.message.edit_text("✅ Пополнение подтверждено, баланс пользователя увеличен.")
    await callback.answer()

@router.message(Command("withdraw_requests"))
async def list_withdraw_requests(message: Message):
    if not is_admin(message.from_user.id):
        return
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
            f"📤 Заявка #{r.id}\nПартнёр ID: {r.partner_id}\nСумма: {r.amount} USDT\nАдрес: {r.wallet_address}",
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("approve_withdraw_"))
async def approve_withdraw_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    req_id = int(callback.data.split("_")[2])
    await approve_withdraw_request(req_id)
    await callback.message.edit_text("✅ Заявка на вывод одобрена.")
    await callback.answer()
