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
                print(f"Номер заказа найден: {data['order_id']}")  # Отладочное сообщение
            else:
                print(f"Номер заказа не найден в строке: {line}")  # Отладочное сообщение
            continue

        # Извлечение даты приема
        if "дата приема" in line.lower():
            date_match = re.search(date_pattern, line)
            if date_match:
                data["acceptance_date"] = date_match.group()
                print(f"Дата приема найдена: {data['acceptance_date']}")  # Отладочное сообщение
            else:
                print(f"Дата приема не найдена в строке: {line}")  # Отладочное сообщение

        # Извлечение причины возврата
        if "Причина возврата:" in line:
            reason_match = re.search(r'"([^"]+)"', line)
            if reason_match:
                data["reason"] = reason_match.group(1)
                print(f"Причина возврата найдена: {data['reason']}", len(data['reason']))  # Отладочное сообщение
                if len(data['reason']) < 5:
                    data["reason"] = "Не удалось извлечь данные из-за изменения структуры сообщения!"
            else:
                print(f"Причина возврата не найдена в строке: {line}")  # Отладочное сообщение

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
        print(f"Наименование товара найдено: {data['product_name']}")  # Отладочное сообщение
    else:
        data["product_name"] =  "Не удалось извлечь данные из-за изменения структуры сообщения!"

    return data


@router.message(F.text | F.caption)
async def handle_text(message: types.Message):
    text = message.text or message.caption
    if not text or "Принят товар – на возврат" not in text:
        return

    extracted_data = parse_structured_text(text)

    # Валидация обязательных полей
    required_fields = ['order_id', 'acceptance_date', 'reason']
    if not all(extracted_data.get(field) for field in required_fields):
        await message.reply("❌ В сообщении отсутствуют обязательные данные: номер заказа,"
                            " дата приема, товар или причина возврата")
        return

    try:
        acceptance_date = datetime.strptime(extracted_data['acceptance_date'], "%d.%m.%Y").date()
    except ValueError as e:
        await message.reply(f"❌ Ошибка формата даты: {str(e)}")
        return


    # Формирование ответа
    response = (
        "**Извлеченные данные:**\n"
        f"📦 Номер заказа: {extracted_data['order_id']}\n"
        f"📅 Дата приема: {extracted_data['acceptance_date']}\n"
        f"🛍️ Товар: {extracted_data.get('product_name', 'не найдено')}\n"
        f"🔧 Причина: {extracted_data['reason']}"
    )

    try:
        await add_request(
            order_number=extracted_data['order_id'],
            order_date=acceptance_date,  # Используем дату приема как дату заказа
            product_name=extracted_data['product_name'],
            return_reason=extracted_data['reason']
        )
          # Отправляем извлеченные данные пользователю
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        await message.reply("❌ Произошла ошибка при сохранении данных")