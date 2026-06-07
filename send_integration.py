import aiohttp
import asyncio
from datetime import datetime, timedelta
from config import SEND_API_KEY
from database import async_session_maker, TopupInvoice, User, Partner, PartnerEarning
from models import User, Partner, PartnerEarning
from sqlalchemy import select
from loguru import logger

SEND_API_URL = "https://api.send.tg/v1"  # уточнить у документации @send

async def create_send_invoice(user_id: int, amount: float, description: str = "Пополнение баланса") -> str:
    """Создаёт счёт в @send, возвращает ID счёта и ссылку для оплаты"""
    async with aiohttp.ClientSession() as session:
        # Документация @send: POST /invoice
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
                # Сохраняем в БД
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
    """Проверяет статус счёта в @send (pending/paid/expired)"""
    async with aiohttp.ClientSession() as session:
        headers = {"X-API-Key": SEND_API_KEY}
        async with session.get(f"{SEND_API_URL}/invoice/{invoice_id}", headers=headers) as resp:
            data = await resp.json()
            return data.get('status', 'unknown')

async def process_paid_invoice(invoice_id: str):
    """При подтверждении оплаты начисляет баланс пользователю и партнёру/рефералу"""
    async with async_session_maker() as db:
        # Находим инвойс
        inv = await db.execute(select(TopupInvoice).where(TopupInvoice.send_invoice_id == invoice_id))
        inv = inv.scalar_one_or_none()
        if not inv or inv.status == 'paid':
            return
        inv.status = 'paid'
        user_id = inv.user_id
        amount = inv.amount
        # Начисляем пользователю
        user = await db.execute(select(User).where(User.user_id == user_id))
        user = user.scalar_one()
        user.balance += amount
        # Начисляем бонус партнёру или рефералу
        if user.partner_id:
            partner = await db.execute(select(Partner).where(Partner.id == user.partner_id))
            partner = partner.scalar_one()
            bonus = amount * 0.5
            partner.balance += bonus
            db.add(PartnerEarning(
                partner_id=partner.id,
                user_id=user_id,
                amount=bonus,
                topup_amount=amount
            ))
        elif user.referrer_id:
            referrer = await db.execute(select(User).where(User.user_id == user.referrer_id))
            referrer = referrer.scalar_one()
            bonus = amount * 0.5
            referrer.balance += bonus
            # Для рефералов можно отдельную таблицу, но пока просто увеличиваем баланс
        await db.commit()
