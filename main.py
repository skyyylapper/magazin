#!/usr/bin/env python3
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config import MAIN_BOT_TOKEN, ADMIN_BOT_TOKEN
from database import init_db
from handlers import user_start, user_catalog, user_cart, user_profile, user_topup
from handlers import admin_commands, admin_products, admin_users, admin_partners, partner_commands
from middlewares import LanguageMiddleware
from currency import start_currency_updater
from send_integration import start_invoice_checker
from loguru import logger

logger.add("logs/bot.log", rotation="1 day", retention="7 days")

async def main_bot():
    bot = Bot(token=MAIN_BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())

    dp.include_router(user_start.router)
    dp.include_router(user_catalog.router)
    dp.include_router(user_cart.router)
    dp.include_router(user_profile.router)
    dp.include_router(user_topup.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

async def admin_bot():
    bot = Bot(token=ADMIN_BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())

    dp.include_router(admin_commands.router)
    dp.include_router(admin_products.router)
    dp.include_router(admin_users.router)
    dp.include_router(admin_partners.router)
    dp.include_router(partner_commands.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

async def main():
    await init_db()
    asyncio.create_task(start_currency_updater())
    asyncio.create_task(start_invoice_checker())
    await asyncio.gather(main_bot(), admin_bot())

if __name__ == "__main__":
    asyncio.run(main())
