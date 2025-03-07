from sqlalchemy import String, Column, Integer, Date, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_async_engine(url=os.getenv('POSTGRESQL_1'))

async_session = async_sessionmaker(engine, expire_on_commit=False)  # Добавьте expire_on_commit=False

class Base(AsyncAttrs, DeclarativeBase):
    pass

class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True)
    order_date = Column(Date)
    product_name = Column(String)
    admission_date = Column(Date)
    return_reason = Column(String)
    is_arrived = Column(Boolean, default=False)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)