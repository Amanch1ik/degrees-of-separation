import pytest
import asyncio

from site_monitor_bot.db import create_engine_and_session, init_db
from site_monitor_bot.repository import UserRepository, SiteRepository, CheckRecordRepository


@pytest.mark.asyncio
async def test_repositories_crud(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    engine, session_factory = create_engine_and_session(db_url)
    await init_db(engine)

    async with session_factory() as session:
        user = await UserRepository(session).upsert_user(telegram_user_id=1, chat_id=100)
        await session.commit()

    async with session_factory() as session:
        site = await SiteRepository(session).add_site(user_id=1, url="https://example.com", interval_seconds=60)
        await session.commit()

    async with session_factory() as session:
        sites = await SiteRepository(session).list_sites_by_user(1)
        assert len(sites) == 1
        rec_repo = CheckRecordRepository(session)
        await rec_repo.add_record(site_id=sites[0].id, status_code=200, response_ms=120, is_up=True, content_hash="hash", error=None)
        await session.commit()

    async with session_factory() as session:
        records = await CheckRecordRepository(session).list_recent(site_id=1, limit=5)
        assert len(records) >= 1
