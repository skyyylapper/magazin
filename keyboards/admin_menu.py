from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_USERNAME

def admin_main_keyboard(lang='ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Товары", callback_data="admin_products"),
         InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="🤝 Партнёры", callback_data="admin_partners"),
         InlineKeyboardButton(text="💰 Ручные пополнения", callback_data="admin_manual_topups")],
        [InlineKeyboardButton(text="📤 Заявки на вывод", callback_data="admin_withdraw_requests"),
         InlineKeyboardButton(text="🆘 Поддержка", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])

def partner_main_keyboard(lang='ru'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="partner_balance"),
         InlineKeyboardButton(text="🔗 Моя ссылка", callback_data="partner_link")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="partner_stats"),
         InlineKeyboardButton(text="💸 Вывести", callback_data="partner_withdraw")],
        [InlineKeyboardButton(text="🆘 Поддержка", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
