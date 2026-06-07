import aiohttp
import asyncio
from datetime import datetime, timedelta
from config import SEND_API_KEY
from database import async_session_maker, get_user, get_partner_by_id, update_user_balance, update_partner_balance
from models import TopupInvoice, PartnerEarning
from sqlalchemy import select
from loguru import logger

SEND_API_URL = "https://api.send.tg/v1"

async def create_send_invoice(user_id: int, amount: float, description: str = "Пополнение баланса"):
    async with aiohttp.ClientSession() as session:
        payload = {
            "amount": amount,
            "currency": "USDT",
            "description": description,
            "user_id": user_id,
            "expires_in": 3600,
        }
        headers = {"X-API-Key": SEND_API_KEY}
        async with session.post(f"{SEND_API_URL}/invoice", json=payload, headers=headers) as resp:
            data = await resp.json()
            if resp.status == 200:
                invoice_id = data['invoice_id']
                pay_url = data['pay_url']
                async with async_session_maker() as db:
                    new_invoice = TopupInvoice(
                        user_id=user_id,
                        amount=amount,
                        send_invoice_id=invoice_id,
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
        headers = {"X-API-Key": SEND_API_KEY}
        async with session.get(f"{SEND_API_URL}/invoice/{invoice_id}", headers=headers) as resp:
            data = await resp.json()
            return data.get('status', 'unknown')

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
