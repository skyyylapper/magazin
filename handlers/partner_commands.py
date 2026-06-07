from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import async_session_maker, Partner, WithdrawRequest, PartnerEarning
from sqlalchemy import select
from translations import get_text

router = Router()

async def get_partner_by_telegram_id(telegram_id: int):
    async with async_session_maker() as session:
        result = await session.execute(select(Partner).where(Partner.telegram_id == telegram_id))
        return result.scalar_one_or_none()

@router.message(Command("balance"))
async def partner_balance(message: Message):
    partner = await get_partner_by_telegram_id(message.from_user.id)
    if not partner:
        await message.answer("Доступ запрещён.")
        return
    await message.answer(f"💰 Ваш партнёрский баланс: {partner.balance:.2f} USDT")

@router.message(Command("referral_link"))
async def partner_link(message: Message):
    partner = await get_partner_by_telegram_id(message.from_user.id)
    if not partner:
        return
    await message.answer(f"🔗 Ваша партнёрская ссылка: `https://t.me/MAIN_BOT_USERNAME?start={partner.referral_link}`", parse_mode="Markdown")

@router.message(Command("stats"))
async def partner_stats(message: Message):
    partner = await get_partner_by_telegram_id(message.from_user.id)
    if not partner:
        return
    async with async_session_maker() as session:
        earnings = await session.execute(select(PartnerEarning).where(PartnerEarning.partner_id == partner.id))
        earnings = earnings.scalars().all()
        total_earned = sum(e.amount for e in earnings)
        count = len(earnings)
        text = f"📊 Ваша статистика:\nВсего начислено: {total_earned} USDT\nКоличество пополнений: {count}\n"
        # последние 5 начислений
        if earnings:
            text += "\nПоследние начисления:\n"
            for e in earnings[-5:]:
                text += f"{e.created_at.strftime('%Y-%m-%d')}: +{e.amount} USDT (пополнение на {e.topup_amount} USDT)\n"
        await message.answer(text)

@router.message(Command("withdraw"))
async def partner_withdraw(message: Message):
    partner = await get_partner_by_telegram_id(message.from_user.id)
    if not partner:
        return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /withdraw <сумма> <адрес_кошелька>")
        return
    _, amount_str, wallet = args
    try:
        amount = float(amount_str)
        if amount <= 0 or amount > partner.balance:
            await message.answer("Некорректная сумма или превышает баланс.")
            return
        async with async_session_maker() as session:
            req = WithdrawRequest(
                partner_id=partner.id,
                amount=amount,
                wallet_address=wallet,
                status='pending'
            )
            session.add(req)
            await session.commit()
        await message.answer(f"✅ Заявка на вывод {amount} USDT создана. Ожидайте подтверждения администратора.")
    except:
        await message.answer("Ошибка. Используйте: /withdraw 100 USDT TRC20 адрес")
