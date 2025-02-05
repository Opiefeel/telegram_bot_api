from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters
)
from datetime import datetime
from dateutil.relativedelta import relativedelta
from database import async_session, Student, Payment
from sqlalchemy import select

# Состояния
FULL_NAME, PERCENTAGE, AMOUNT, MONTHS, START_DATE = range(5)


async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Привет! Сначала добавим ученика. Введите его имя и фамилию:")
    return FULL_NAME


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Отменено')
    return ConversationHandler.END


async def full_name(update: Update, context: CallbackContext) -> int:
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("Введите процент от оффера (целое число):")
    return PERCENTAGE


async def percentage(update: Update, context: CallbackContext) -> int:
    try:
        percent = int(update.message.text)
        if not 1 <= percent <= 999:
            raise ValueError
        context.user_data['percentage'] = percent
        await update.message.reply_text("Введите сумму на руки (целое число):")
        return AMOUNT
    except ValueError:
        await update.message.reply_text("Неверный формат! Введите число от 1 до 999")
        return PERCENTAGE


async def amount(update: Update, context: CallbackContext) -> int:
    try:
        amount = int(update.message.text)
        context.user_data['amount'] = amount
        await update.message.reply_text(
            "Выберите количество месяцев на сколько делить оплату:",
            reply_markup=ReplyKeyboardMarkup([['3', '4', '5'], ['Отмена']], resize_keyboard=True,
                                             one_time_keyboard=True)
        )
        return MONTHS
    except ValueError:
        await update.message.reply_text("Неверный формат! Введите целое число")
        return AMOUNT


async def months(update: Update, context: CallbackContext) -> int:
    months = update.message.text
    if months not in ['3', '4', '5']:
        await update.message.reply_text("Выберите 3, 4 или 5, ну пожалуйста")
        return MONTHS
    context.user_data['months'] = int(months)
    await update.message.reply_text("Введите дату трудоустройства (ДД-ММ-ГГГГ (например: 31-12-2023):")
    return START_DATE


async def start_date(update: Update, context: CallbackContext) -> int:
    try:
        date = datetime.strptime(update.message.text, "%d-%m-%Y").date()

        total = (context.user_data['amount'] * context.user_data['percentage'] / 100)
        base_payment = total // context.user_data['months']
        remainder = total % context.user_data['months']

        async with async_session() as session:
            student = Student(
                user_id=update.effective_user.id,
                full_name=context.user_data['full_name'],
                percentage=context.user_data['percentage'],
                amount=context.user_data['amount'],
                months=context.user_data['months'],
                start_date=date
            )
            session.add(student)
            await session.commit()

            for i in range(context.user_data['months']):
                payment_date = date + relativedelta(days=30 * (i + 1))
                amount = base_payment + (remainder if i == context.user_data['months'] - 1 else 0)
                payment = Payment(
                    student_id=student.id,
                    payment_date=payment_date,
                    amount=float(amount)
                )
                session.add(payment)

            await session.commit()

        await update.message.reply_text("Ученик добавлен!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Неверный формат даты! Используйте ДД-ММ-ГГГГ (например: 31-12-2023)")
        return START_DATE

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
        PERCENTAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, percentage)],
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
        MONTHS: [MessageHandler(filters.TEXT & ~filters.COMMAND, months)],
        START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_date)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)