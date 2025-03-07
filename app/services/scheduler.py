from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from app.db.requests import get_pending_requests
from dotenv import load_dotenv
import logging, os


group_id = os.getenv("GROUP_ID")


async def schedule_jobs(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    # Ежедневно в 9:00, кроме воскресенья (0 - воскресенье, 1-6 - понедельник-суббота)
    scheduler.add_job(
        send_daily_report,
        trigger=CronTrigger(day_of_week="mon-sat", hour=9, minute=0),
        args=(bot,),
        name="daily_report"
    )

    scheduler.start()
    logging.info("Scheduler started")

async def send_daily_report(bot: Bot):
    try:
        requests = await get_pending_requests()
        if not requests:
            return

        message = "⚠️ *Неподтвержденные приемки на сегодня:*\n\n"
        for req in requests:
            message += (
                f"📦 Номер заказа: `{req.order_number}`\n"
                f"📅 Дата заказа: {req.order_date}\n"
                f"🛍️ Товар: {req.product_name}\n\n"
            )

        await bot.send_message(
            chat_id=GROUP_ID,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Error sending daily report: {str(e)}")