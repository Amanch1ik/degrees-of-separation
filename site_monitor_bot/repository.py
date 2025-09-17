from __future__ import annotations

from typing import Iterable, Optional
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from .db import User, Site, CheckRecord


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_user(self, telegram_user_id: int, chat_id: int) -> User:
        user = await self.get_user(telegram_user_id)
        if user:
            user.chat_id = chat_id
        else:
            user = User(telegram_user_id=telegram_user_id, chat_id=chat_id)
            self.session.add(user)
        await self.session.flush()
        return user

    async def get_user(self, telegram_user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        return result.scalars().first()


class SiteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_site(self, user_id: int, url: str, interval_seconds: int) -> Site:
        site = Site(user_id=user_id, url=url, interval_seconds=interval_seconds)
        self.session.add(site)
        await self.session.flush()
        return site

    async def list_sites_by_user(self, user_id: int) -> list[Site]:
        result = await self.session.execute(select(Site).where(Site.user_id == user_id).order_by(Site.id))
        return list(result.scalars().all())

    async def get_site(self, site_id: int, user_id: Optional[int] = None) -> Optional[Site]:
        stmt = select(Site).where(Site.id == site_id)
        if user_id is not None:
            stmt = stmt.where(Site.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def remove_site(self, site_id: int, user_id: Optional[int] = None) -> int:
        stmt = delete(Site).where(Site.id == site_id)
        if user_id is not None:
            stmt = stmt.where(Site.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def update_interval(self, site_id: int, seconds: int, user_id: Optional[int] = None) -> int:
        stmt = update(Site).where(Site.id == site_id).values(interval_seconds=seconds)
        if user_id is not None:
            stmt = stmt.where(Site.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def list_all_active(self) -> list[Site]:
        result = await self.session.execute(select(Site).where(Site.is_active == True))
        return list(result.scalars().all())


class CheckRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_record(
        self,
        site_id: int,
        status_code: Optional[int],
        response_ms: Optional[int],
        is_up: bool,
        content_hash: Optional[str],
        error: Optional[str],
    ) -> CheckRecord:
        record = CheckRecord(
            site_id=site_id,
            status_code=status_code,
            response_ms=response_ms,
            is_up=is_up,
            content_hash=content_hash,
            error=error,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_recent(self, site_id: int, limit: int = 10) -> list[CheckRecord]:
        result = await self.session.execute(
            select(CheckRecord)
            .where(CheckRecord.site_id == site_id)
            .order_by(CheckRecord.checked_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
