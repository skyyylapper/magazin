from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from models import Base, User, Product, Order, Partner, ManualTopup, WithdrawRequest, AntiSpamRecord, CurrencyRate
from config import DATABASE_URL
from datetime import datetime
from typing import Optional, List, Any

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---- User CRUD ----
async def get_user(user_id: int) -> Optional[User]:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

async def create_user(user_id: int, username: str, first_name: str, last_name: str,
                      language: str = 'ru', referrer_id: int = None, partner_id: int = None) -> User:
    async with async_session_maker() as session:
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            referrer_id=referrer_id,
            partner_id=partner_id
        )
        session.add(user)
        await session.commit()
        return user

async def update_user_balance(user_id: int, new_balance: float):
    async with async_session_maker() as session:
        user = await get_user(user_id)
        if user:
            user.balance = new_balance
            await session.commit()

# ---- Product CRUD ----
async def get_product(product_id: int) -> Optional[Product]:
    async with async_session_maker() as session:
        return await session.get(Product, product_id)

async def get_all_products(only_available: bool = True) -> List[Product]:
    async with async_session_maker() as session:
        query = select(Product)
        if only_available:
            query = query.where(Product.is_available == True)
        result = await session.execute(query)
        return result.scalars().all()

async def create_product(name: str, description: str, price: float, photo_file_id: str = None, is_available: bool = True) -> Product:
    async with async_session_maker() as session:
        product = Product(
            name=name,
            description=description,
            price=price,
            photo_file_id=photo_file_id,
            is_available=is_available
        )
        session.add(product)
        await session.commit()
        return product

async def update_product(product_id: int, **kwargs):
    async with async_session_maker() as session:
        product = await get_product(product_id)
        if product:
            for key, value in kwargs.items():
                setattr(product, key, value)
            await session.commit()

async def delete_product(product_id: int):
    async with async_session_maker() as session:
        await session.execute(delete(Product).where(Product.id == product_id))
        await session.commit()

# ---- Partner CRUD ----
async def get_partner_by_telegram_id(telegram_id: int) -> Optional[Partner]:
    async with async_session_maker() as session:
        result = await session.execute(select(Partner).where(Partner.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def get_partner_by_id(partner_id: int) -> Optional[Partner]:
    async with async_session_maker() as session:
        return await session.get(Partner, partner_id)

async def create_partner(telegram_id: int, name: str) -> Partner:
    async with async_session_maker() as session:
        partner = Partner(
            telegram_id=telegram_id,
            name=name,
            referral_link=f"partner_{telegram_id}"
        )
        session.add(partner)
        await session.commit()
        return partner

async def update_partner_balance(partner_id: int, new_balance: float):
    async with async_session_maker() as session:
        partner = await get_partner_by_id(partner_id)
        if partner:
            partner.balance = new_balance
            await session.commit()

# ---- Order CRUD ----
async def create_order(user_id: int, product_id: int, amount: float) -> Order:
    async with async_session_maker() as session:
        order = Order(user_id=user_id, product_id=product_id, amount=amount, status='paid')
        session.add(order)
        await session.commit()
        return order

# ---- ManualTopup CRUD ----
async def create_manual_topup(user_id: int, amount: float, wallet_address: str, transaction_hash: str) -> ManualTopup:
    async with async_session_maker() as session:
        manual = ManualTopup(
            user_id=user_id,
            amount=amount,
            wallet_address=wallet_address,
            transaction_hash=transaction_hash,
            status='pending'
        )
        session.add(manual)
        await session.commit()
        return manual

async def get_pending_manual_topups() -> List[ManualTopup]:
    async with async_session_maker() as session:
        result = await session.execute(select(ManualTopup).where(ManualTopup.status == 'pending'))
        return result.scalars().all()

async def confirm_manual_topup(manual_id: int):
    from models import User, Partner, PartnerEarning
    from datetime import datetime
    import logging
    async with async_session_maker() as session:
        async with session.begin():
            manual = await session.get(ManualTopup, manual_id)
            if not manual:
                logging.error(f"ManualTopup {manual_id} not found")
                return
            if manual.status != 'pending':
                logging.warning(f"ManualTopup {manual_id} already {manual.status}")
                return
            manual.status = 'confirmed'
            manual.confirmed_at = datetime.utcnow()
            
            user = await session.get(User, manual.user_id)
            if user:
                user.balance += manual.amount
                if user.partner_id:
                    partner = await session.get(Partner, user.partner_id)
                    if partner:
                        bonus = manual.amount * 0.5
                        partner.balance += bonus
                        earning = PartnerEarning(
                            partner_id=partner.id,
                            user_id=user.user_id,
                            amount=bonus,
                            topup_amount=manual.amount
                        )
                        session.add(earning)
                logging.info(f"User {user.user_id} balance increased by {manual.amount}")
            await session.commit()
# ---- WithdrawRequest CRUD ----
async def create_withdraw_request(partner_id: int, amount: float, wallet_address: str) -> WithdrawRequest:
    async with async_session_maker() as session:
        req = WithdrawRequest(
            partner_id=partner_id,
            amount=amount,
            wallet_address=wallet_address,
            status='pending'
        )
        session.add(req)
        await session.commit()
        return req

async def get_pending_withdraw_requests() -> List[WithdrawRequest]:
    async with async_session_maker() as session:
        result = await session.execute(select(WithdrawRequest).where(WithdrawRequest.status == 'pending'))
        return result.scalars().all()

async def approve_withdraw_request(request_id: int):
    async with async_session_maker() as session:
        req = await session.get(WithdrawRequest, request_id)
        if req and req.status == 'pending':
            req.status = 'approved'
            partner = await get_partner_by_id(req.partner_id)
            if partner and partner.balance >= req.amount:
                partner.balance -= req.amount
            await session.commit()

# ---- AntiSpam CRUD ----
async def get_antispam_record(user_id: int) -> Optional[AntiSpamRecord]:
    async with async_session_maker() as session:
        result = await session.execute(select(AntiSpamRecord).where(AntiSpamRecord.user_id == user_id))
        return result.scalar_one_or_none()

async def update_antispam_record(user_id: int, **kwargs):
    async with async_session_maker() as session:
        record = await get_antispam_record(user_id)
        if record:
            for key, value in kwargs.items():
                setattr(record, key, value)
        else:
            record = AntiSpamRecord(user_id=user_id, **kwargs)
            session.add(record)
        await session.commit()

# ---- CurrencyRate CRUD ----
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
