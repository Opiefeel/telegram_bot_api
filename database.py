from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from config import DB_URL

Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    full_name = Column(String)
    percentage = Column(Integer)
    amount = Column(Integer)
    months = Column(Integer)
    start_date = Column(Date)

    payments = relationship("Payment", back_populates="student")


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    payment_date = Column(Date)
    amount = Column(Float)
    notified = Column(Boolean, default=False)

    student = relationship("Student", back_populates="payments")


engine = create_async_engine(DB_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)