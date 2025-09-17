from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Callable

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import SiteRepository
from .monitor import MonitorService


class MonitorScheduler:
    def __init__(self, session_factory, monitor_service: MonitorService, weekly_cron: dict[str, str | int]):
        self.session_factory = session_factory
        self.monitor_service = monitor_service
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.weekly_cron = weekly_cron

    async def start(self):
        self.scheduler.start()
        await self.schedule_all_active_sites()
        # Weekly report job stub; actual notifications hooked in main
        self.scheduler.add_job(
            self._weekly_report_job,
            CronTrigger(day_of_week=self.weekly_cron["day_of_week"], hour=self.weekly_cron["hour"], minute=self.weekly_cron["minute"], timezone="UTC"),
            id="weekly_report",
            replace_existing=True,
        )

    async def schedule_all_active_sites(self):
        async with self.session_factory() as session:  # type: AsyncSession
            sites = await SiteRepository(session).list_all_active()
        for site in sites:
            self.schedule_site(site.id, site.interval_seconds)

    def schedule_site(self, site_id: int, interval_seconds: int):
        job_id = f"site_check_{site_id}"
        self.scheduler.add_job(
            self._check_site_job,
            IntervalTrigger(seconds=interval_seconds),
            id=job_id,
            kwargs={"site_id": site_id},
            replace_existing=True,
        )
        logger.info(f"Scheduled site {site_id} every {interval_seconds}s")

    async def _check_site_job(self, site_id: int):
        async with aiohttp.ClientSession() as http_session:
            # Fetch latest interval and ensure site still exists
            from .repository import SiteRepository
            async with self.session_factory() as session:  # type: AsyncSession
                site = await SiteRepository(session).get_site(site_id)
            if not site or not site.is_active:
                logger.info(f"Site {site_id} not active, skipping")
                return
            await self.monitor_service.perform_check_and_store(site, http_session)

    async def _weekly_report_job(self):
        # notification wiring added in main
        logger.info("Weekly report job tick")
