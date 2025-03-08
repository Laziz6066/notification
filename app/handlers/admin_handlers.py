from aiogram import Router, F
from datetime import datetime
from app.db.state import AddOrder
from app.keyboards.admin_keyboards import get_main_keyboard
from aiogram.types import Message
from aiogram.filters import Command
from app.db.models import async_session
from app.db.models import ReturnRequest
from sqlalchemy import select
import logging
from app.db.requests import get_pending_requests, add_request
from app.config import ADMINS
from aiogram.fsm.context import FSMContext


router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Выберите действие:", reply_markup=await get_main_keyboard(message.from_user.id))


@router.message(F.text == "Добавить")
async def add_order(message: Message, state: FSMContext):
    if message.from_user.id in ADMINS:

        await state.set_state(AddOrder.order_number)
        await message.answer("№ заказа:")
    else:
        await message.answer("У вас нет доступа !!!")


@router.message(AddOrder.order_number)
async def order_num(message: Message, state: FSMContext):
    await state.update_data(order_number=message.text)
    await state.set_state(AddOrder.order_date)
    await message.answer("Введите дату приема в формате: <b>26.12.2024</b>", parse_mode="HTML")


@router.message(AddOrder.order_date)
async def order_date(message: Message, state: FSMContext):
    date_obj = datetime.strptime(message.text, "%d.%m.%Y").date()
    await state.update_data(order_date=date_obj)
    await state.set_state(AddOrder.product_name)
    await message.answer("Введите название товара: ")


@router.message(AddOrder.product_name)
async def order_item_name(message: Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await state.set_state(AddOrder.return_reason)
    await message.answer("Введите причину возврата: ")


@router.message(AddOrder.return_reason)
async def order_reason(message: Message, state: FSMContext):
    await state.update_data(return_reason=message.text.strip())
    data = await state.get_data()

    await add_request(
        order_number=data['order_number'],
        order_date=data['order_date'],
        product_name=data['product_name'],
        return_reason=data['return_reason']
    )

    await state.clear()
    await message.answer("Заказ успешно добавлен!")


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
                f"📅 Дата приема: {req.order_date}\n"
                f"🛍️ Товар: {req.product_name}\n"
                f"🟥 Причина возврата: {req.return_reason}\n\n"
            )

        await message.answer(
            text=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error sending daily report: {str(e)}")
