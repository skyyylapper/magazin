from aiogram.fsm.state import State, StatesGroup

class ManualTopupState(StatesGroup):
    waiting_amount = State()
    waiting_txid = State()
