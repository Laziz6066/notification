from datetime import datetime
from aiogram import types
from aiogram import F, Router
import re
import logging

from app.db.requests import add_request

router = Router()


def parse_structured_text(text: str) -> dict:
    data = {}
    text = text.replace("\xa0", " ").replace("\r", "")  # Очистка от специальных символов
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Проверка ключевой фразы для активации парсинга
    if "Принят товар – на возврат" not in text:
        return {}

    # Поиск всех дат в тексте
    date_pattern = r"\b\d{2}\.\d{2}\.\d{4}\b"
    dates = re.findall(date_pattern, text)

    # Основные паттерны
    order_pattern = re.compile(
        r"Заказ №\s*(?P<order_id>[^\s]+)\s*(?P<order_date>\d{2}\.\d{2}\.\d{4})?"
    )

    # Поиск информации о заказе
    for line in lines:
        if "Заказ №" in line:
            match = order_pattern.search(line)
            if match:
                data["order_id"] = match.group("order_id")
                if match.group("order_date"):
                    data["order_date"] = match.group("order_date")
            continue

        if "дата приема" in line.lower() and not data.get("acceptance_date"):
            date_match = re.search(date_pattern, line)
            if date_match:
                data["acceptance_date"] = date_match.group()

        if "Причина возврата:" in line:
            reason_match = re.search(r'"([^"]+)"', line)
            if reason_match:
                data["reason"] = reason_match.group(1)

        if "сообщить до" in line.lower() and not data.get("deadline"):
            date_match = re.search(date_pattern, line)
            if date_match:
                data["deadline"] = date_match.group()

    # Сбор названия товара
    product_lines = []
    collect_product = False
    for line in lines:
        if "Заказ №" in line:
            collect_product = True
            continue

        if collect_product and any(key in line for key in ["Причина возврата:", "Клиента интересует:"]):
            break

        if collect_product:
            product_lines.append(line)

    if product_lines:
        data["product_name"] = " ".join(product_lines).strip()

    # Автозаполнение недостающих дат из общего поиска
    if not data.get("order_date") and len(dates) > 0:
        data["order_date"] = dates[0]
    if not data.get("acceptance_date") and len(dates) > 1:
        data["acceptance_date"] = dates[1]

    return data


@router.message(F.text | F.caption)
async def handle_text(message: types.Message):
    text = message.text or message.caption
    if not text or "Принят товар – на возврат" not in text:
        return

    extracted_data = parse_structured_text(text)

    # Валидация обязательных полей
    required_fields = ['order_id', 'order_date', 'acceptance_date']
    if not all(extracted_data.get(field) for field in required_fields):
        await message.reply("❌ В сообщении отсутствуют обязательные данные: номер заказа, дата заказа или дата приема")
        return

    try:
        order_date = datetime.strptime(extracted_data['order_date'], "%d.%m.%Y").date()
        admission_date = datetime.strptime(extracted_data['acceptance_date'], "%d.%m.%Y").date()
    except ValueError as e:
        await message.reply(f"❌ Ошибка формата даты: {str(e)}")
        return

    # Формирование ответа
    response = (
        "**Извлеченные данные:**\n"
        f"📦 Номер заказа: `{extracted_data['order_id']}`\n"
        f"📅 Дата заказа: `{extracted_data.get('order_date', 'не указана')}`\n"
        f"🛍️ Товар: _{extracted_data.get('product_name', 'не указан')}_\n"
        f"🔧 Причина: _{extracted_data.get('reason', 'не указана')}_\n"
        f"⏳ Дедлайн: `{extracted_data.get('deadline', 'не указан')}`"
    )

    try:
        await add_request(
            order_number=extracted_data['order_id'],
            order_date=order_date,
            product_name=extracted_data.get('product_name', 'не указан'),
            return_reason=extracted_data.get('reason', 'не указана')
        )

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        await message.reply("❌ Произошла ошибка при сохранении данных")