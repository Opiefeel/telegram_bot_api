from telegram.ext import Application
from config import TOKEN
import handlers
import scheduler
from database import init_db
import asyncio


async def main():
    await init_db()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(handlers.conv_handler)

    scheduler.scheduler.start()

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()


async def shutdown(application: Application):
    await application.updater.stop()
    await application.stop()
    await application.shutdown()


if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(shutdown(application))