from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

import aiohttp
from loguru import logger

from .db import hash_content, Site
from .repository import CheckRecordRepository


@dataclass
class CheckResult:
    status_code: Optional[int]
    response_ms: Optional[int]
    is_up: bool
    content_hash: Optional[str]
    error: Optional[str]


async def http_check(url: str, session: aiohttp.ClientSession, timeout_s: int = 15) -> CheckResult:
    start = asyncio.get_event_loop().time()
    try:
        async with session.get(url, timeout=timeout_s) as resp:
            body = await resp.read()
            duration_ms = int((asyncio.get_event_loop().time() - start) * 1000)
            status = resp.status
            content = hash_content(body) if status == 200 else None
            return CheckResult(status_code=status, response_ms=duration_ms, is_up=200 <= status < 400, content_hash=content, error=None)
    except Exception as e:  # network/timeout/etc
        duration_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        return CheckResult(status_code=None, response_ms=duration_ms, is_up=False, content_hash=None, error=str(e))


class MonitorService:
    def __init__(self, session_factory, max_concurrent_checks: int = 10):
        self.session_factory = session_factory
        self.semaphore = asyncio.Semaphore(max_concurrent_checks)

    async def perform_check_and_store(self, site: Site, http_session: aiohttp.ClientSession) -> CheckResult:
        async with self.semaphore:
            result = await http_check(site.url, http_session)

        from sqlalchemy import update
        from sqlalchemy.ext.asyncio import AsyncSession
        from .db import Site as SiteModel
        from sqlalchemy import select

        async with self.session_factory() as db:  # type: AsyncSession
            record_repo = CheckRecordRepository(db)
            await record_repo.add_record(
                site_id=site.id,
                status_code=result.status_code,
                response_ms=result.response_ms,
                is_up=result.is_up,
                content_hash=result.content_hash,
                error=result.error,
            )
            # update site
            await db.execute(
                update(SiteModel)
                .where(SiteModel.id == site.id)
                .values(
                    last_status_code=result.status_code,
                    last_response_ms=result.response_ms,
                    last_content_hash=result.content_hash,
                    last_checked_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()

        return result
