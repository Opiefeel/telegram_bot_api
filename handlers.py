from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
FULL_NAME, PERCENTAGE, AMOUNT, MONTHS, START_DATE, CONFIRMATION = range(6)


async def restart(update: Update, context: CallbackContext) -> int:
    """Сброс текущего диалога"""
    await update.message.reply_text(
        "Начинаем заново!",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return await start(update, context)


async def start(update: Update, context: CallbackContext) -> int:
    """Начало диалога"""
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! Давайте добавим ученика. Введите имя и фамилию:",
        reply_markup=ReplyKeyboardRemove()
    )
    return FULL_NAME


async def full_name(update: Update, context: CallbackContext) -> int:
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text(
        "Введите процент от оффера (целое число от 1 до 999):",
        reply_markup=ReplyKeyboardMarkup(
            [['Давай по новой']],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return PERCENTAGE


async def percentage(update: Update, context: CallbackContext) -> int:
    try:
        percent = int(update.message.text)
        if not 1 <= percent <= 999:
            raise ValueError
        context.user_data['percentage'] = percent
        await update.message.reply_text(
            "Введите сумму на руки (целое число):",
            reply_markup=ReplyKeyboardMarkup(
                [['Давай по новой']],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return AMOUNT
    except ValueError:
        await update.message.reply_text("Неверный формат! Введите число от 1 до 999")
        return PERCENTAGE


async def amount(update: Update, context: CallbackContext) -> int:
    try:
        amount = int(update.message.text)
        context.user_data['amount'] = amount
        await update.message.reply_text(
            "Выберите количество месяца:",
            reply_markup=ReplyKeyboardMarkup(
                [['3', '4', '5'], ['Давай по новой']],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return MONTHS
    except ValueError:
        await update.message.reply_text("Неверный формат! Введите целое число")
        return AMOUNT


async def months(update: Update, context: CallbackContext) -> int:
    months = update.message.text
    if months not in ['3', '4', '5']:
        await update.message.reply_text("Выберите 3, 4 или 5")
        return MONTHS
    context.user_data['months'] = int(months)
    await update.message.reply_text(
        "Введите дату трудоустройства (ДД-ММ-ГГГГ):",
        reply_markup=ReplyKeyboardMarkup(
            [['Давай по новой']],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return START_DATE


async def start_date(update: Update, context: CallbackContext) -> int:
    try:
        date = datetime.strptime(update.message.text, "%d-%m-%Y").date()
        context.user_data['start_date'] = date

        # Формируем текст подтверждения
        confirmation_text = (
            "Проверьте данные:\n"
            f"Имя: {context.user_data['full_name']}\n"
            f"Процент: {context.user_data['percentage']}%\n"
            f"Сумма на руки: {context.user_data['amount']} руб.\n"
            f"Делим на {context.user_data['months']} месяца\n"
            f"Дата трудоустройства: {date.strftime('%d-%m-%Y')}\n"
            "\nВсё верно?"
        )

        await update.message.reply_text(
            confirmation_text,
            reply_markup=ReplyKeyboardMarkup(
                [['Да, сохранить', 'Нет, начать заново']],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return CONFIRMATION

    except ValueError:
        await update.message.reply_text("Неверный формат даты! Используйте ДД-ММ-ГГГГ (например: 31-12-2023)")
        return START_DATE


async def confirmation(update: Update, context: CallbackContext) -> int:
    if update.message.text == 'Да, сохранить':
        # Сохранение в базу данных
        try:
            date = context.user_data['start_date']
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

                # Добавляем платежи
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

            # Отправляем финальное сообщение
            await update.message.reply_text(
                "✅ Ученик успешно добавлен!\n"
                "Хотите добавить ещё одного?",
                reply_markup=ReplyKeyboardMarkup(
                    [['Добавить ещё одного ученика']],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
            context.user_data.clear()
            return ConversationHandler.END

        except Exception as e:
            await update.message.reply_text(f"Ошибка сохранения: {str(e)}")
            return ConversationHandler.END

    else:
        return await restart(update, context)


# Обновленный обработчик диалога
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        FULL_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)
        ],
        PERCENTAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, percentage)
        ],
        AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, amount)
        ],
        MONTHS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, months)
        ],
        START_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, start_date)
        ],
        CONFIRMATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)
        ]
    },
    fallbacks=[
        CommandHandler('cancel', lambda update, context: ConversationHandler.END),
        MessageHandler(filters.Regex(r'^Добавить ещё одного ученика$'), start)
    ],
    allow_reentry=True
)