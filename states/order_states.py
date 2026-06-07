from aiogram.fsm.state import State, StatesGroup

class OrderState(StatesGroup):
    confirming = State()
    waiting_for_address = State()  # если товар физический
