from telegram import ReplyKeyboardMarkup

def months_keyboard():
    return ReplyKeyboardMarkup(
        [['3', '4', '5'], ['Отмена']],
        resize_keyboard=True,
        one_time_keyboard=True
    )