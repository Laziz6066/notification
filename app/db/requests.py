from app.db.models import async_session
from app.db.models import ReturnRequest
from sqlalchemy import select, update, delete
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date


async def add_request(
        order_number: str,
        order_date: date,
        product_name: str,
        admission_date: date,
        return_reason: str
):
    logging.info(f"Добавление запроса: {order_number}\n, {order_date}\n, {product_name}\n, {admission_date}\n, "
                 f"{return_reason}")

    async with async_session() as session:
        item = ReturnRequest(
            order_number=order_number,
            order_date=order_date,
            product_name=product_name,
            admission_date=admission_date,
            return_reason=return_reason
        )
        session.add(item)
        await session.commit()


async def get_pending_requests() -> list[ReturnRequest]:
    async with async_session() as session:
        result = await session.execute(
            select(ReturnRequest).where(ReturnRequest.is_arrived == False))
        return result.scalars().all()


