from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from app.config import ADMINS, ADMIN


async def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:

    if user_id in ADMINS:
        buttons = [
            [KeyboardButton(text='Просмотр')],
            [KeyboardButton(text='Приемка')],
        ]
        if user_id in ADMIN:
            buttons.insert(__index=1, __object=[KeyboardButton(text='Добавить')])
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)