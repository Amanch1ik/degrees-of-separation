from __future__ import annotations

import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from loguru import logger

from dotenv import load_dotenv

from .config import load_settings
from .logging_config import configure_logging
from .db import create_engine_and_session, init_db
from .monitor import MonitorService
from .scheduler import MonitorScheduler
from .bot import register_handlers
from .notifications import Notifier


async def run():
    load_dotenv()
    configure_logging()
    settings = load_settings()

    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    # Ensure data dir exists for sqlite
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    engine, session_factory = create_engine_and_session(settings.database_url)
    await init_db(engine)

    bot = Bot(settings.telegram_bot_token, parse_mode="HTML")
    dp = Dispatcher()

    register_handlers(dp, session_factory)

    monitor_service = MonitorService(session_factory, max_concurrent_checks=settings.max_concurrent_checks)
    scheduler = MonitorScheduler(
        session_factory,
        monitor_service,
        weekly_cron={
            "day_of_week": settings.weekly_report_day_of_week,
            "hour": settings.weekly_report_hour,
            "minute": settings.weekly_report_minute,
        },
    )
    await scheduler.start()

    notifier = Notifier(bot, session_factory)

    # Wire weekly report to notifier
    from apscheduler.triggers.cron import CronTrigger
    scheduler.scheduler.add_job(
        notifier.send_weekly_report,
        CronTrigger(day_of_week=settings.weekly_report_day_of_week, hour=settings.weekly_report_hour, minute=settings.weekly_report_minute, timezone="UTC"),
        id="weekly_report_notify",
        replace_existing=True,
    )

    logger.info("Bot is starting polling...")
    await dp.start_polling(bot)
