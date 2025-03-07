from aiogram import Router, F
from app.keyboards.admin_keyboards import get_main_keyboard
from aiogram.types import Message
from aiogram.filters import Command
from app.db.models import async_session
from app.db.models import ReturnRequest
from sqlalchemy import select
import logging
from app.db.requests import get_pending_requests

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Выберите действие:", reply_markup=await get_main_keyboard(message.from_user.id))


@router.message(F.text == "Приемка")
async def start_acceptance(message: Message):
    await message.answer("Введите номер заказа:")


@router.message(F.text.regexp(r'^\d+$'))
async def process_order_number(message: Message):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(ReturnRequest).where(ReturnRequest.order_number == message.text)
            )
            request = result.scalars().first()

            if request:
                request.is_arrived = True
                await message.answer("Статус товара обновлен!")
            else:
                await message.answer("Заказ не найден")


@router.message(F.text == "Просмотр")
async def send_daily_report(message: Message):
    try:
        requests = await get_pending_requests()
        if not requests:
            return

        text = "⚠️ *Напоминаем что эти товары не поступили в ПВЗ:*\n\n"
        for req in requests:
            text += (
                f"📦 Номер заказа: `{req.order_number}`\n"
                f"📅 Дата приема: {req.admission_date}\n"
                f"🛍️ Товар: {req.product_name}\n"
                f"🟥 Причина возврата: {req.return_reason}\n\n"
            )

        await message.answer(
            text=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error sending daily report: {str(e)}")