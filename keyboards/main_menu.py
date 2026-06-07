from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_USERNAME

def main_menu_keyboard(lang='ru'):
    if lang == 'ru':
        btn_catalog = "🛍 Каталог"
        btn_balance = "💰 Баланс"
        btn_support = "🆘 Поддержка"
        btn_cart = "🛒 Корзина"
        btn_profile = "👤 Профиль"
    else:
        btn_catalog = "🛍 Catalog"
        btn_balance = "💰 Balance"
        btn_support = "🆘 Support"
        btn_cart = "🛒 Cart"
        btn_profile = "👤 Profile"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_catalog, callback_data="catalog"),
         InlineKeyboardButton(text=btn_cart, callback_data="cart")],
        [InlineKeyboardButton(text=btn_balance, callback_data="balance"),
         InlineKeyboardButton(text=btn_profile, callback_data="profile")],
        [InlineKeyboardButton(text=btn_support, url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
