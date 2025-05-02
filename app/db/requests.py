# app/db/requests.py
from __future__ import annotations
import asyncio
import logging
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.db.models import async_session, ReturnRequest


async def add_request(
        order_number: str,
        order_date: date,
        product_name: str,
        return_reason: str,
) -> None:

    max_retries = 3
    base_number = order_number.split()[0]

    for attempt in range(max_retries):
        async with async_session() as session:
            try:
                # Блокировка для предотвращения race condition
                async with session.begin():
                    count_query = select(func.count(ReturnRequest.id)) \
                        .where(ReturnRequest.order_number.like(f"{base_number}%"))
                    already = (await session.execute(count_query)).scalar_one()

                    final_number = f"{base_number} №{already + 1}" if already else base_number
                    logging.info(f"Attempt {attempt + 1}: Adding order {final_number}")

                    item = ReturnRequest(
                        order_number=final_number,
                        order_date=order_date,
                        product_name=product_name,
                        return_reason=return_reason,
                    )
                    session.add(item)
                    await session.commit()
                    return

            except IntegrityError as e:
                await session.rollback()
                logging.warning(f"Conflict on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    logging.error("Max retries reached for order %s", order_number)
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))


async def get_pending_requests() -> list[ReturnRequest]:
    """Получить все ещё не прибывшие заказы (is_arrived = False)."""
    async with async_session() as session:
        result = await session.execute(
            select(ReturnRequest).where(ReturnRequest.is_arrived.is_(False))
        )
        return list(result.scalars())


# app/db/requests.py (добавить новую функцию)
async def get_arrived_requests() -> list[ReturnRequest]:
    """Получить все прибывшие заказы (is_arrived = True)."""
    async with async_session() as session:
        result = await session.execute(
            select(ReturnRequest).where(ReturnRequest.is_arrived.is_(True)))
        return list(result.scalars())