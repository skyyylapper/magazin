import aiohttp
import asyncio
from datetime import datetime
from database import async_session_maker
from models import CurrencyRate
from sqlalchemy import select, update
from loguru import logger
import config

async def fetch_usdt_to_rub():
    """Получает курс USDT/RUB через Binance или другой API"""
    try:
        async with aiohttp.ClientSession() as session:
            # Пример Binance: цена USDT/RUB
            url = "https://api.binance.com/api/v3/ticker/price?symbol=USDTRUB"
            async with session.get(url) as resp:
                data = await resp.json()
                return float(data['price'])
    except Exception as e:
        logger.error(f"Failed to fetch USDT/RUB: {e}")
        return None

async def fetch_usdt_to_usd():
    """USDT/USD всегда 1, но можно запросить для единообразия"""
    return 1.0

async def update_currency_rates():
    """Обновляет курсы в БД"""
    rub_rate = await fetch_usdt_to_rub()
    if rub_rate:
        async with async_session_maker() as session:
            # Обновляем или вставляем
            await session.execute(
                update(CurrencyRate).where(CurrencyRate.currency == 'RUB').values(rate=rub_rate, updated_at=datetime.utcnow())
            )
            if (await session.execute(select(CurrencyRate).where(CurrencyRate.currency == 'RUB'))).first() is None:
                session.add(CurrencyRate(currency='RUB', rate=rub_rate))
            await session.commit()
    # USD
    usd_rate = 1.0
    async with async_session_maker() as session:
        await session.execute(
            update(CurrencyRate).where(CurrencyRate.currency == 'USD').values(rate=usd_rate, updated_at=datetime.utcnow())
        )
        if (await session.execute(select(CurrencyRate).where(CurrencyRate.currency == 'USD'))).first() is None:
            session.add(CurrencyRate(currency='USD', rate=usd_rate))
        await session.commit()

async def start_currency_updater():
    while True:
        await update_currency_rates()
        await asyncio.sleep(config.CURRENCY_UPDATE_INTERVAL)

async def get_rate(currency: str = "RUB") -> float:
    async with async_session_maker() as session:
        result = await session.execute(select(CurrencyRate).where(CurrencyRate.currency == currency.upper()))
        row = result.scalar_one_or_none()
        if row:
            return row.rate
        return None
