from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import async_session, Payment, Student
from config import TOKEN
from telegram import Bot
from sqlalchemy import select

bot = Bot(token=TOKEN)


async def check_payments():
    async with async_session() as session:
        tomorrow = datetime.now().date() + timedelta(days=1)
        result = await session.execute(
            select(Payment).where(Payment.payment_date == tomorrow, Payment.notified == False)
        )
        payments = result.scalars().all()

        for payment in payments:
            student = (await session.execute(
                select(Student).where(Student.id == payment.student_id)
            )).scalar()

            await bot.send_message(
                chat_id=student.user_id,
                text=f"Завтра ({tomorrow}) оплата {payment.amount:.2f} руб. для {student.full_name}."
            )
            payment.notified = True
            await session.commit()


scheduler = AsyncIOScheduler()
scheduler.add_job(check_payments, 'cron', hour=9, minute=0)