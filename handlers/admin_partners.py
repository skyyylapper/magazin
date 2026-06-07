from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import async_session_maker, Partner, WithdrawRequest, ManualTopup, User
from sqlalchemy import select, update
from config import ADMIN_IDS

router = Router()

def is_admin(user_id): return user_id in ADMIN_IDS

@router.message(Command("partners"))
async def list_partners(message: Message):
    if not is_admin(message.from_user.id): return
    async with async_session_maker() as session:
        partners = await session.execute(select(Partner))
        partners = partners.scalars().all()
        if not partners:
            await message.answer("Нет партнёров.")
            return
        text = "🤝 Список партнёров:\n"
        for p in partners:
            text += f"ID: {p.id} | {p.name} | Баланс: {p.balance} USDT\n"
        await message.answer(text)

@router.message(Command("add_partner"))
async def add_partner(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /add_partner <telegram_id> <имя>")
        return
    _, tele_id_str, name = parts
    tele_id = int(tele_id_str)
    async with async_session_maker() as session:
        partner = Partner(telegram_id=tele_id, name=name, referral_link=f"partner_{tele_id}")
        session.add(partner)
        await session.commit()
    await message.answer(f"Партнёр {name} добавлен. Его ссылка: partner_{tele_id}")

@router.message(Command("manual_topups"))
async def list_manual_topups(message: Message):
    if not is_admin(message.from_user.id): return
    async with async_session_maker() as session:
        topups = await session.execute(select(ManualTopup).where(ManualTopup.status == 'pending'))
        topups = topups.scalars().all()
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
async def confirm_manual(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    manual_id = int(callback.data.split("_")[2])
    async with async_session_maker() as session:
        manual = await session.get(ManualTopup, manual_id)
        if manual and manual.status == 'pending':
            manual.status = 'confirmed'
            # начисляем баланс пользователю и бонус партнёру/рефералу
            user = await session.execute(select(User).where(User.user_id == manual.user_id))
            user = user.scalar_one()
            user.balance += manual.amount
            # бонусы (аналогично send_integration)
            if user.partner_id:
                partner = await session.get(Partner, user.partner_id)
                if partner:
                    bonus = manual.amount * 0.5
                    partner.balance += bonus
            elif user.referrer_id:
                referrer = await session.execute(select(User).where(User.user_id == user.referrer_id))
                referrer = referrer.scalar_one()
                referrer.balance += manual.amount * 0.5
            await session.commit()
            await callback.message.edit_text(f"Пополнение {manual.amount} USDT для {manual.user_id} подтверждено.")
    await callback.answer()

@router.message(Command("withdraw_requests"))
async def list_withdraw_requests(message: Message):
    if not is_admin(message.from_user.id): return
    async with async_session_maker() as session:
        reqs = await session.execute(select(WithdrawRequest).where(WithdrawRequest.status == 'pending'))
        reqs = reqs.scalars().all()
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
async def approve_withdraw(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    req_id = int(callback.data.split("_")[2])
    async with async_session_maker() as session:
        req = await session.get(WithdrawRequest, req_id)
        if req and req.status == 'pending':
            req.status = 'approved'
            # списываем баланс у партнёра
            partner = await session.get(Partner, req.partner_id)
            if partner:
                partner.balance -= req.amount
            await session.commit()
            await callback.message.edit_text(f"Заявка №{req_id} одобрена. Деньги переведены вручную.")
    await callback.answer()
