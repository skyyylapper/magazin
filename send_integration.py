# send_integration.py
import aiohttp
import asyncio
from datetime import datetime, timedelta
from config import SEND_API_KEY
from database import async_session_maker, get_user, get_partner_by_id
from models import TopupInvoice, PartnerEarning
from sqlalchemy import select
from loguru import logger

# !!! ВАЖНО: URL для Crypto Pay API от @CryptoBot !!!
CRYPTO_PAY_API_URL = "https://pay.crypt.bot/api"

async def create_send_invoice(user_id: int, amount: float, description: str = "Пополнение баланса"):
    async with aiohttp.ClientSession() as session:
        payload = {
            "amount": str(amount),
            "asset": "USDT",
            "description": description,
            "paid_usd_rate": True,
            "expires_in": 3600,
        }
        # !!! ВАЖНО: Правильный заголовок для авторизации в Crypto Pay API !!!
        headers = {"Crypto-Pay-API-Token": SEND_API_KEY}
        async with session.post(f"{CRYPTO_PAY_API_URL}/createInvoice", json=payload, headers=headers) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get('ok'):
                invoice = data['result']
                invoice_id = invoice['invoice_id']
                # Используем поле bot_invoice_url для ссылки на оплату
                pay_url = invoice.get('bot_invoice_url')
                async with async_session_maker() as db:
                    new_invoice = TopupInvoice(
                        user_id=user_id,
                        amount=amount,
                        send_invoice_id=str(invoice_id),
                        status='pending',
                        expires_at=datetime.utcnow() + timedelta(hours=1)
                    )
                    db.add(new_invoice)
                    await db.commit()
                return invoice_id, pay_url
            else:
                logger.error(f"Send invoice error: {data}")
                return None, None

async def check_invoice_status(invoice_id: str) -> str:
    async with aiohttp.ClientSession() as session:
        headers = {"Crypto-Pay-API-Token": SEND_API_KEY}
        payload = {"invoice_id": invoice_id}
        async with session.get(f"{CRYPTO_PAY_API_URL}/getInvoices", params=payload, headers=headers) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get('ok') and data['result']['items']:
                invoice = data['result']['items'][0]
                status = invoice.get('status')
                if status == 'paid':
                    return 'paid'
                elif status == 'expired':
                    return 'expired'
                else:
                    return 'pending'
            return 'unknown'

async def process_paid_invoice(invoice_id: str):
    async with async_session_maker() as db:
        inv = await db.execute(select(TopupInvoice).where(TopupInvoice.send_invoice_id == invoice_id))
        inv = inv.scalar_one_or_none()
        if not inv or inv.status == 'paid':
            return
        inv.status = 'paid'
        user_id = inv.user_id
        amount = inv.amount
        user = await get_user(user_id)
        if user:
            user.balance += amount
            if user.partner_id:
                partner = await get_partner_by_id(user.partner_id)
                if partner:
                    bonus = amount * 0.5
                    partner.balance += bonus
                    db.add(PartnerEarning(
                        partner_id=partner.id,
                        user_id=user_id,
                        amount=bonus,
                        topup_amount=amount
                    ))
            elif user.referrer_id:
                referrer = await get_user(user.referrer_id)
                if referrer:
                    referrer.balance += amount * 0.5
            await db.commit()

async def start_invoice_checker():
    """Фоновая задача: каждые 10 секунд проверяет статусы pending инвойсов"""
    while True:
        async with async_session_maker() as session:
            pending = await session.execute(select(TopupInvoice).where(TopupInvoice.status == 'pending'))
            for inv in pending.scalars():
                status = await check_invoice_status(inv.send_invoice_id)
                if status == 'paid':
                    await process_paid_invoice(inv.send_invoice_id)
        await asyncio.sleep(10)
