from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    language = Column(String, default='ru')
    registered_at = Column(DateTime, default=datetime.utcnow)
    referrer_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)  # обычный реферал
    partner_id = Column(Integer, ForeignKey('partners.id'), nullable=True)        # партнёр, если пришёл по партнёрской ссылке

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    photo_file_id = Column(String, nullable=True)   # одно фото
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    amount = Column(Float)
    status = Column(String, default='pending')  # pending, paid, delivered
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

class TopupInvoice(Base):
    __tablename__ = 'topup_invoices'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    amount = Column(Float)
    send_invoice_id = Column(String, unique=True)
    status = Column(String, default='pending')  # pending, paid, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class Partner(Base):
    __tablename__ = 'partners'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    referral_link = Column(String, unique=True)   # уникальная партнёрская ссылка
    created_at = Column(DateTime, default=datetime.utcnow)

class PartnerEarning(Base):
    __tablename__ = 'partner_earnings'
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey('partners.id'))
    user_id = Column(BigInteger)
    amount = Column(Float)
    topup_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class WithdrawRequest(Base):
    __tablename__ = 'withdraw_requests'
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey('partners.id'), nullable=False)
    amount = Column(Float, nullable=False)
    wallet_address = Column(String, nullable=False)
    status = Column(String, default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    admin_comment = Column(String, nullable=True)

class ManualTopup(Base):
    __tablename__ = 'manual_topups'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    amount = Column(Float, nullable=False)
    wallet_address = Column(String)
    transaction_hash = Column(String, nullable=True)
    status = Column(String, default='pending')  # pending, confirmed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

class AntiSpamRecord(Base):
    __tablename__ = 'antispam'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True)
    invoice_count = Column(Integer, default=0)
    first_invoice_time = Column(DateTime)
    blocked_until = Column(DateTime, nullable=True)

class CurrencyRate(Base):
    __tablename__ = 'currency_rates'
    id = Column(Integer, primary_key=True)
    currency = Column(String, unique=True)  # RUB, USD
    rate = Column(Float)   # сколько USDT стоит 1 единица валюты? (например, 0.011 за RUB)
    updated_at = Column(DateTime, default=datetime.utcnow)
