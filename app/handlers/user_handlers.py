from datetime import datetime
from aiogram import types
from aiogram import F, Router
import re
import logging

from app.db.requests import add_request

router = Router()


def parse_structured_text(text: str) -> dict:
    data = {}
    text = text.replace("\xa0", " ").replace("\r", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    if "Принят товар – на возврат" not in text:
        return {}

    date_pattern = r"\b\d{1,2}\.\d{1,2}\.\d{4}\b"

    order_pattern = re.compile(
        r"Заказ №\s*(?P<order_id>[^\s]+)\s+(?P<order_date>\d{1,2}\.\d{1,2}\.\d{4})\s*(?P<product_name>.+)?"
    )

    for line in lines:
        if "Заказ №" in line:
            match = order_pattern.search(line)
            if match:
                data["order_id"] = match.group("order_id")
                print(f"Номер заказа найден: {data['order_id']}")

                if match.group("order_date"):
                    data["order_date"] = match.group("order_date")
                    print(f"Дата заказа найдена: {data['order_date']}")

                if match.group("product_name"):
                    data["product_name"] = match.group("product_name").strip()
                    print(f"Наименование товара найдено в строке заказа: {data['product_name']}")
            else:
                print(f"Номер заказа не найден в строке: {line}")
            continue

        if "дата приема" in line.lower():
            date_match = re.search(date_pattern, line)
            if date_match:
                data["acceptance_date"] = date_match.group()
                print(f"Дата приема найдена: {data['acceptance_date']}")
            else:
                print(f"Дата приема не найдена в строке: {line}")

        if "Причина возврата:" in line:
            reason_match = re.search(r'Причина возврата:\s*(?:"([^"]+)"|(.*))', line)
            if reason_match:
                reason = reason_match.group(1) or reason_match.group(2)
                reason = reason.strip()
                if len(reason) < 5:
                    reason = "Не удалось извлечь данные из-за изменения структуры сообщения!"
                data["reason"] = reason
                print(f"Причина возврата найдена: {data['reason']}")
            else:
                print(f"Причина возврата не найдена в строке: {line}")

    if "product_name" not in data:
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
            print(f"Наименование товара собрано из следующих строк: {data['product_name']}")
        else:
            data["product_name"] = "Не удалось извлечь данные из-за изменения структуры сообщения!"

    return data



@router.message(F.text | F.caption)
async def handle_text(message: types.Message):
    text = message.text or message.caption
    if not text or "Принят товар – на возврат" not in text:
        return

    extracted_data = parse_structured_text(text)

    required_fields = ['order_id', 'acceptance_date', 'reason']
    if not all(extracted_data.get(field) for field in required_fields):
        await message.bot.send_message(chat_id=661394290,
                                       text='❌ В сообщении отсутствуют обязательные '
                                            'данные: номер заказа, дата приема, '
                                            'товар или причина возврата')
        return

    try:
        acceptance_date = datetime.strptime(extracted_data['acceptance_date'], "%d.%m.%Y").date()
    except ValueError as e:
        await message.bot.send_message(661394290, f"❌ Ошибка формата даты: {str(e)}")
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
            order_date=acceptance_date,
            product_name=extracted_data['product_name'],
            return_reason=extracted_data['reason']
        )
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        await message.bot.send_message(661394290, "❌ Произошла ошибка при сохранении данных")
