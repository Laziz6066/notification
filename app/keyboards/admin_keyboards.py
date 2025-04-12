from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from app.config import ADMINS, ADMIN


async def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:

    buttons = []

    if user_id in ADMINS:
        buttons.extend([
            [KeyboardButton(text='Просмотр')],
            [KeyboardButton(text='Приемка')],
        ])

    if ADMIN and user_id == ADMIN:
        buttons.insert(1, [KeyboardButton(text='Добавить')])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)