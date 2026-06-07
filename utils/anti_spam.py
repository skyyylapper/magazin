from datetime import datetime, timedelta
from database import async_session_maker
from models import AntiSpamRecord
from sqlalchemy import select, update
import config

async def check_antispam(user_id: int) -> bool:
    """
    Возвращает True, если пользователь может создавать новый счёт/заявку.
    False - заблокирован.
    """
    now = datetime.utcnow()
    async with async_session_maker() as session:
        record = await session.execute(select(AntiSpamRecord).where(AntiSpamRecord.user_id == user_id))
        record = record.scalar_one_or_none()
        if record and record.blocked_until and record.blocked_until > now:
            return False
        if record:
            # проверяем окно времени
            if record.first_invoice_time and (now - record.first_invoice_time).total_seconds() < config.ANTISPAM_TIMEFRAME:
                if record.invoice_count >= config.ANTISPAM_MAX_INVOICES:
                    # блокируем
                    record.blocked_until = now + timedelta(seconds=config.ANTISPAM_BLOCK_DURATION)
                    await session.commit()
                    return False
            else:
                # сброс счётчика
                record.invoice_count = 1
                record.first_invoice_time = now
                record.blocked_until = None
                await session.commit()
        else:
            # новый
            new_record = AntiSpamRecord(
                user_id=user_id,
                invoice_count=1,
                first_invoice_time=now
            )
            session.add(new_record)
            await session.commit()
        return True

async def increment_invoice_count(user_id: int):
    """Увеличивает счётчик после создания счёта"""
    async with async_session_maker() as session:
        record = await session.execute(select(AntiSpamRecord).where(AntiSpamRecord.user_id == user_id))
        record = record.scalar_one_or_none()
        if record:
            record.invoice_count += 1
            await session.commit()
