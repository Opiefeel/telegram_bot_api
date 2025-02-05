from telegram.ext import Application
from config import TOKEN
import handlers
import scheduler
import asyncio
from database import init_db


async def main():
    await init_db()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(handlers.conv_handler)

    scheduler.scheduler.start()

    await application.run_polling()


if __name__ == '__main__':
    asyncio.run(main())