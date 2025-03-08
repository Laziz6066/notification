from aiogram.fsm.state import StatesGroup, State


class AddOrder(StatesGroup):
    order_number = State()
    order_date = State()
    product_name = State()
    return_reason = State()