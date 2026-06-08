from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete, update
from models import Base, User, Product, Order, Partner, ManualTopup, WithdrawRequest, AntiSpamRecord, CurrencyRate, PartnerEarning
from config import DATABASE_URL
from datetime import datetime
from typing import Optional, List

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---- User ----
async def get_user(user_id: int) -> Optional[User]:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

async def create_user(user_id: int, username: str, first_name: str, last_name: str, language='ru', referrer_id=None, partner_id=None) -> User:
    async with async_session_maker() as session:
        user = User(user_id=user_id, username=username, first_name=first_name, last_name=last_name, language=language, referrer_id=referrer_id, partner_id=partner_id)
        session.add(user)
        await session.commit()
        return user

async def update_user_balance(user_id: int, new_balance: float):
    async with async_session_maker() as session:
        user = await get_user(user_id)
        if user:
            user.balance = new_balance
            await session.commit()

# ---- Product ----
async def get_product(product_id: int) -> Optional[Product]:
    async with async_session_maker() as session:
        return await session.get(Product, product_id)

async def get_all_products(only_available=True) -> List[Product]:
    async with async_session_maker() as session:
        q = select(Product)
        if only_available:
            q = q.where(Product.is_available == True)
        result = await session.execute(q)
        return result.scalars().all()

async def create_product(name, description, price, photo_file_id=None, is_available=True) -> Product:
    async with async_session_maker() as session:
        p = Product(name=name, description=description, price=price, photo_file_id=photo_file_id, is_available=is_available)
        session.add(p)
        await session.commit()
        return p

async def update_product(product_id: int, **kwargs):
    async with async_session_maker() as session:
        p = await get_product(product_id)
        if p:
            for k, v in kwargs.items():
                setattr(p, k, v)
            await session.commit()

async def delete_product(product_id: int):
    async with async_session_maker() as session:
        await session.execute(delete(Product).where(Product.id == product_id))
        await session.commit()

# ---- Partner ----
async def get_partner_by_telegram_id(telegram_id: int) -> Optional[Partner]:
    async with async_session_maker() as session:
        result = await session.execute(select(Partner).where(Partner.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def get_partner_by_id(partner_id: int) -> Optional[Partner]:
    async with async_session_maker() as session:
        return await session.get(Partner, partner_id)

async def create_partner(telegram_id: int, name: str) -> Partner:
    async with async_session_maker() as session:
        partner = Partner(telegram_id=telegram_id, name=name, referral_link=f"partner_{telegram_id}")
        session.add(partner)
        await session.commit()
        return partner

async def update_partner_balance(partner_id: int, new_balance: float):
    async with async_session_maker() as session:
        p = await get_partner_by_id(partner_id)
        if p:
            p.balance = new_balance
            await session.commit()

# ---- ManualTopup ----
async def create_manual_topup(user_id: int, amount: float, wallet_address: str, txid: str) -> ManualTopup:
    async with async_session_maker() as session:
        m = ManualTopup(user_id=user_id, amount=amount, wallet_address=wallet_address, transaction_hash=txid, status='pending')
        session.add(m)
        await session.commit()
        return m

async def get_pending_manual_topups() -> List[ManualTopup]:
    async with async_session_maker() as session:
        result = await session.execute(select(ManualTopup).where(ManualTopup.status == 'pending'))
        return result.scalars().all()

async def confirm_manual_topup(manual_id: int):
    """Подтверждает ручное пополнение, начисляет баланс пользователю и бонус партнёру"""
    async with async_session_maker() as session:
        # Получаем заявку
        manual = await session.get(ManualTopup, manual_id)
        if not manual or manual.status != 'pending':
            return
        manual.status = 'confirmed'
        manual.confirmed_at = datetime.utcnow()
        
        # Начисляем баланс пользователю
        user = await session.execute(select(User).where(User.user_id == manual.user_id))
        user = user.scalar_one_or_none()
        if user:
            user.balance += manual.amount
            
            # Начисляем бонус партнёру (если есть)
            if user.partner_id:
                partner = await session.get(Partner, user.partner_id)
                if partner:
                    bonus = manual.amount * 0.5
                    partner.balance += bonus
                    # Записываем историю начисления
                    earning = PartnerEarning(
                        partner_id=partner.id,
                        user_id=user.user_id,
                        amount=bonus,
                        topup_amount=manual.amount
                    )
                    session.add(earning)
            # Если есть обычный реферал (опционально)
            elif user.referrer_id:
                referrer = await session.get(User, user.referrer_id)
                if referrer:
                    referrer.balance += manual.amount * 0.5
            await session.commit()

# ---- WithdrawRequest ----
async def create_withdraw_request(partner_id: int, amount: float, wallet: str) -> WithdrawRequest:
    async with async_session_maker() as session:
        w = WithdrawRequest(partner_id=partner_id, amount=amount, wallet_address=wallet, status='pending')
        session.add(w)
        await session.commit()
        return w

async def get_pending_withdraw_requests() -> List[WithdrawRequest]:
    async with async_session_maker() as session:
        result = await session.execute(select(WithdrawRequest).where(WithdrawRequest.status == 'pending'))
        return result.scalars().all()

async def approve_withdraw_request(request_id: int):
    async with async_session_maker() as session:
        w = await session.get(WithdrawRequest, request_id)
        if w and w.status == 'pending':
            w.status = 'approved'
            partner = await session.get(Partner, w.partner_id)
            if partner and partner.balance >= w.amount:
                partner.balance -= w.amount
            await session.commit()

# ---- AntiSpam ----
async def get_antispam_record(user_id: int) -> Optional[AntiSpamRecord]:
    async with async_session_maker() as session:
        result = await session.execute(select(AntiSpamRecord).where(AntiSpamRecord.user_id == user_id))
        return result.scalar_one_or_none()

async def update_antispam_record(user_id: int, **kwargs):
    async with async_session_maker() as session:
        rec = await get_antispam_record(user_id)
        if rec:
            for k, v in kwargs.items():
                setattr(rec, k, v)
        else:
            rec = AntiSpamRecord(user_id=user_id, **kwargs)
            session.add(rec)
        await session.commit()

# ---- CurrencyRate ----
async def get_currency_rate(currency: str) -> Optional[float]:
    async with async_session_maker() as session:
        result = await session.execute(select(CurrencyRate).where(CurrencyRate.currency == currency.upper()))
        row = result.scalar_one_or_none()
        return row.rate if row else None

async def set_currency_rate(currency: str, rate: float):
    async with async_session_maker() as session:
        result = await session.execute(select(CurrencyRate).where(CurrencyRate.currency == currency.upper()))
        row = result.scalar_one_or_none()
        if row:
            row.rate = rate
            row.updated_at = datetime.utcnow()
        else:
            session.add(CurrencyRate(currency=currency.upper(), rate=rate))
        await session.commit()
