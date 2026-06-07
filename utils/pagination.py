from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Any

def paginate_keyboard(items: List[Any], page: int, callback_prefix: str, items_per_page: int = 5) -> InlineKeyboardMarkup:
    start = page * items_per_page
    end = start + items_per_page
    page_items = items[start:end]
    buttons = []
    for item in page_items:
        item_id = getattr(item, 'id', None) or item
        buttons.append([InlineKeyboardButton(text=str(item.name) if hasattr(item, 'name') else str(item), callback_data=f"{callback_prefix}{item_id}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"{callback_prefix}page_{page-1}"))
    if end < len(items):
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"{callback_prefix}page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
