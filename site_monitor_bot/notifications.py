from __future__ import annotations

from aiogram import Bot
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .db import Site, User


class Notifier:
    def __init__(self, bot: Bot, session_factory):
        self.bot = bot
        self.session_factory = session_factory

    async def notify_downtime(self, site_id: int):
        async with self.session_factory() as session:  # type: AsyncSession
            site, user = await self._load_site_user(session, site_id)
        if not site or not user:
            return
        text = f"⚠️ Сайт недоступен: {site.url}"
        await self.bot.send_message(user.chat_id, text)

    async def notify_recovery(self, site_id: int, status_code: int | None, response_ms: int | None):
        async with self.session_factory() as session:  # type: AsyncSession
            site, user = await self._load_site_user(session, site_id)
        if not site or not user:
            return
        extra = []
        if status_code is not None:
            extra.append(f"code={status_code}")
        if response_ms is not None:
            extra.append(f"{response_ms}ms")
        text = f"✅ Сайт восстановлен: {site.url} ({' | '.join(extra)})"
        await self.bot.send_message(user.chat_id, text)

    async def send_weekly_report(self):
        # Simple version: per user count of up/down last week could be implemented here
        # For MVP send a stub message to all users
        async with self.session_factory() as session:  # type: AsyncSession
            result = await session.execute(select(User))
            users = result.scalars().all()
        for user in users:
            try:
                await self.bot.send_message(user.chat_id, "Еженедельный отчет: статистика доступности доступна в /history")
            except Exception as e:
                logger.warning(f"Failed to send weekly report to {user.chat_id}: {e}")

    async def _load_site_user(self, session: AsyncSession, site_id: int):
        site = await session.get(Site, site_id)
        if not site:
            return None, None
        user = await session.get(User, site.user_id)
        return site, user
