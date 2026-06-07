import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import MAIN_BOT_TOKEN, ADMIN_BOT_TOKEN
from database import init_db
from handlers import user_start, user_catalog, user_cart, user_profile, user_referral, user_topup
from handlers import admin_commands, admin_products, admin_users, admin_partners, admin_manual_topups, admin_withdrawals, partner_commands
from middlewares import LanguageMiddleware
from currency import start_currency_updater

logging.basicConfig(level=logging.INFO)

async def main_bot():
    bot = Bot(token=MAIN_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())
    # Регистрация роутеров пользовательского бота
    dp.include_router(user_start.router)
    dp.include_router(user_catalog.router)
    dp.include_router(user_cart.router)
    dp.include_router(user_profile.router)
    dp.include_router(user_referral.router)
    dp.include_router(user_topup.router)
    await dp.start_polling(bot)

async def admin_bot():
    bot = Bot(token=ADMIN_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    # Роутеры админ-бота
    dp.include_router(admin_commands.router)
    dp.include_router(admin_products.router)
    dp.include_router(admin_users.router)
    dp.include_router(admin_partners.router)
    dp.include_router(admin_manual_topups.router)
    dp.include_router(admin_withdrawals.router)
    dp.include_router(partner_commands.router)
    await dp.start_polling(bot)

async def main():
    await init_db()
    asyncio.create_task(start_currency_updater())  # фоновая задача обновления курсов
    await asyncio.gather(main_bot(), admin_bot())

if __name__ == "__main__":
    asyncio.run(main())
