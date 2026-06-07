from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import async_session_maker, Product, Order, User
from sqlalchemy import select
from translations import get_text
import config

router = Router()
# Для простоты используем FSM для временной корзины
class CartState(StatesGroup):
    items = State()  # dict {product_id: quantity}

@router.callback_query(F.data == "cart")
async def view_cart(callback: CallbackQuery, state: FSMContext, lang: str = 'ru'):
    data = await state.get_data()
    cart = data.get('cart', {})
    if not cart:
        await callback.message.edit_text(get_text('cart_empty', lang))
        return
    total = 0
    text = get_text('cart_title', lang) + "\n"
    for pid, qty in cart.items():
        async with async_session_maker() as session:
            prod = await session.get(Product, int(pid))
            if prod:
                text += f"{prod.name} x{qty} = {prod.price * qty} USDT\n"
                total += prod.price * qty
    text += f"\n<b>Итого: {total} USDT</b>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text('checkout', lang), callback_data="checkout")],
        [InlineKeyboardButton(text=get_text('clear_cart', lang), callback_data="clear_cart")],
        [InlineKeyboardButton(text=get_text('continue_shopping', lang), callback_data="catalog")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("addcart_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext, lang: str = 'ru'):
    product_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    cart = data.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    await state.update_data(cart=cart)
    await callback.answer(get_text('added_to_cart', lang), show_alert=False)

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, state: FSMContext, lang: str = 'ru'):
    await state.update_data(cart={})
    await callback.message.edit_text(get_text('cart_cleared', lang))
    await callback.answer()

@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext, lang: str = 'ru'):
    data = await state.get_data()
    cart = data.get('cart', {})
    if not cart:
        await callback.answer(get_text('cart_empty', lang))
        return
    user_id = callback.from_user.id
    total = 0
    async with async_session_maker() as session:
        user = await session.execute(select(User).where(User.user_id == user_id))
        user = user.scalar_one()
        for pid, qty in cart.items():
            prod = await session.get(Product, int(pid))
            if prod:
                total += prod.price * qty
        if user.balance < total:
            await callback.message.edit_text(get_text('insufficient_balance', lang))
            return
        # Списание
        user.balance -= total
        for pid, qty in cart.items():
            prod = await session.get(Product, int(pid))
            for _ in range(qty):
                order = Order(user_id=user_id, product_id=prod.id, amount=prod.price, status='paid')
                session.add(order)
        await session.commit()
        await state.update_data(cart={})
        await callback.message.edit_text(get_text('order_success', lang))
    await callback.answer()
