from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import async_session_maker, Product
from sqlalchemy import select
from currency import get_rate
from translations import get_text
from utils.pagination import paginate_keyboard
import config

router = Router()

@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery, lang: str = 'ru'):
    async with async_session_maker() as session:
        products = await session.execute(select(Product).where(Product.is_available == True))
        products = products.scalars().all()
        if not products:
            await callback.message.edit_text(get_text('no_products', lang))
            return
        # Пагинация
        kb = paginate_keyboard(products, page=0, callback_prefix="product_", items_per_page=5)
        await callback.message.edit_text(get_text('catalog_title', lang), reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery, lang: str = 'ru'):
    product_id = int(callback.data.split("_")[1])
    async with async_session_maker() as session:
        product = await session.get(Product, product_id)
        if not product:
            await callback.answer(get_text('product_not_found', lang), show_alert=True)
            return
        # Конвертируем цену в валюту пользователя
        user_currency = 'RUB'  # по умолчанию, но можно брать из user.language? можно добавить поле currency в User
        rate = await get_rate(user_currency)
        price_in_currency = product.price * rate if rate else product.price
        text = f"<b>{product.name}</b>\n\n{product.description}\n\nЦена: {price_in_currency:.2f} {user_currency}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text('add_to_cart', lang), callback_data=f"addcart_{product.id}")],
            [InlineKeyboardButton(text=get_text('back_to_catalog', lang), callback_data="catalog")]
        ])
        if product.photo_file_id:
            await callback.message.delete()
            await callback.message.answer_photo(product.photo_file_id, caption=text, reply_markup=kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
