from aiogram.fsm.state import State, StatesGroup

class AddProductState(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_availability = State()

class EditProductState(StatesGroup):
    selecting_product = State()
    choosing_field = State()
    waiting_for_new_name = State()
    waiting_for_new_description = State()
    waiting_for_new_price = State()
    waiting_for_new_photo = State()
    waiting_for_new_availability = State()
