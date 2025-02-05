from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import async_session, Payment, Student
from config import TOKEN
from telegram import Bot
from sqlalchemy import select

scheduler = AsyncIOScheduler()
bot = Bot(token=TOKEN)


async def check_payments():
    async with async_session() as session:
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        # Ищем платежи на завтра и сегодня
        result = await session.execute(
            select(Payment).where(
                (Payment.payment_date == tomorrow) |
                (Payment.payment_date == today),
                Payment.notified == False
            )
        )

        payments = result.scalars().all()

        for payment in payments:
            student = (await session.execute(
                select(Student).where(Student.id == payment.student_id)
            )).scalar()

            if payment.payment_date == tomorrow:
                message = f"Напоминание! Завтра ({tomorrow.strftime('%d-%m-%Y')}) оплата {payment.amount:.2f} руб. для {student.full_name}."
            else:
                message = f"Сегодня ({today.strftime('%d-%m-%Y')}) срок оплаты {payment.amount:.2f} руб. для {student.full_name}."

            await bot.send_message(
                chat_id=student.user_id,
                text=message
            )
            payment.notified = True
            await session.commit()


# Добавляем задачу в планировщик при импорте
scheduler.add_job(check_payments, 'cron', hour=9, minute=0)