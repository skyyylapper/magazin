from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import async_session_maker, get_partner_by_telegram_id, create_withdraw_request
from models import PartnerEarning
from sqlalchemy import select, func
from config import MAIN_BOT_USERNAME
import config

router = Router()

async def get_partner(telegram_id: int):
    return await get_partner_by_telegram_id(telegram_id)

@router.callback_query(F.data == "partner_balance")
async def partner_balance_callback(callback: CallbackQuery):
    partner = await get_partner(callback.from_user.id)
    if not partner:
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text(f"💰 Ваш партнёрский баланс: {partner.balance:.2f} USDT")
    await callback.answer()

@router.callback_query(F.data == "partner_link")
async def partner_link_callback(callback: CallbackQuery):
    partner = await get_partner(callback.from_user.id)
    if not partner:
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    link = f"https://t.me/{MAIN_BOT_USERNAME}?start={partner.referral_link}"
    await callback.message.edit_text(f"🔗 Ваша партнёрская ссылка:\n`{link}`", parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "partner_stats")
async def partner_stats_callback(callback: CallbackQuery):
    partner = await get_partner(callback.from_user.id)
    if not partner:
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    async with async_session_maker() as session:
        earnings = await session.execute(select(PartnerEarning).where(PartnerEarning.partner_id == partner.id))
        earnings = earnings.scalars().all()
        total_earned = sum(e.amount for e in earnings)
        count = len(earnings)
        text = f"📊 Ваша статистика:\nВсего начислено: {total_earned:.2f} USDT\nКоличество пополнений: {count}\n"
        if earnings:
            text += "\nПоследние 5 начислений:\n"
            for e in earnings[-5:]:
                text += f"{e.created_at.strftime('%Y-%m-%d')}: +{e.amount:.2f} USDT (пополнение на {e.topup_amount:.2f} USDT)\n"
        await callback.message.edit_text(text)
    await callback.answer()

@router.callback_query(F.data == "partner_withdraw")
async def partner_withdraw_callback(callback: CallbackQuery):
    partner = await get_partner(callback.from_user.id)
    if not partner:
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text(
        "💸 Для вывода средств отправьте команду:\n`/withdraw <сумма> <адрес_кошелька>`\n\nПример:\n`/withdraw 100 TXxxx...`",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(Command("withdraw"))
async def partner_withdraw_command(message: Message):
    partner = await get_partner(message.from_user.id)
    if not partner:
        await message.answer("Доступ запрещён")
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
        await create_withdraw_request(partner.id, amount, wallet)
        await message.answer(f"✅ Заявка на вывод {amount} USDT создана. Ожидайте подтверждения администратора.")
    except ValueError:
        await message.answer("Сумма должна быть числом.")
