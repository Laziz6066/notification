from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from app.config import ADMINS


async def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text="Просмотр")]]

    if user_id in ADMINS:
        buttons.append([KeyboardButton(text='Приемка')])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)