from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states.admin_states import AddProductState, EditProductState
from database import get_all_products, get_product, create_product, update_product, delete_product
from config import ADMIN_IDS
from utils.pagination import paginate_keyboard

router = Router()

def is_admin(user_id): return user_id in ADMIN_IDS

@router.message(Command("products"))
async def list_products_for_admin(message: Message):
    if not is_admin(message.from_user.id): return
    products = await get_all_products(only_available=False)
    kb = paginate_keyboard(products, page=0, callback_prefix="admin_product_", items_per_page=5)
    await message.answer("📦 Товары:", reply_markup=kb)

@router.callback_query(F.data.startswith("admin_product_"))
async def admin_product_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    product_id = int(callback.data.split("_")[2])
    product = await get_product(product_id)
    if product:
        text = f"ID: {product.id}\nНазвание: {product.name}\nЦена: {product.price} USDT\nДоступен: {'Да' if product.is_available else 'Нет'}\n\n{product.description}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_product_{product.id}"),
             InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_product_{product.id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_products")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await list_products_for_admin(callback.message)

@router.message(Command("add_product"))
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await message.answer("Введите название товара:")
    await state.set_state(AddProductState.waiting_for_name)

@router.message(AddProductState.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await state.set_state(AddProductState.waiting_for_description)

@router.message(AddProductState.waiting_for_description)
async def add_product_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену в USDT (число):")
    await state.set_state(AddProductState.waiting_for_price)

@router.message(AddProductState.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Пришлите фото товара (или нажмите /skip):")
        await state.set_state(AddProductState.waiting_for_photo)
    except:
        await message.answer("Некорректная цена. Введите число.")

@router.message(AddProductState.waiting_for_photo)
async def add_product_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text == "/skip":
        photo_file_id = None
    else:
        await message.answer("Пришлите фото или /skip")
        return
    await state.update_data(photo_file_id=photo_file_id)
    await message.answer("Товар доступен? (да/нет):")
    await state.set_state(AddProductState.waiting_for_availability)

@router.message(AddProductState.waiting_for_availability)
async def add_product_availability(message: Message, state: FSMContext):
    data = await state.get_data()
    is_available = message.text.lower() in ['да', 'yes', 'true', '1']
    await create_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        photo_file_id=data['photo_file_id'],
        is_available=is_available
    )
    await message.answer("✅ Товар добавлен!")
    await state.clear()
