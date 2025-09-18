import asyncio
import pytest

from site_monitor_bot.db import hash_content
from site_monitor_bot.monitor import http_check
import aiohttp


def test_hash_content():
    assert hash_content(b"abc") == hash_content(b"abc")
    assert hash_content(b"abc") != hash_content(b"abd")


@pytest.mark.asyncio
async def test_http_check_invalid_domain():
    async with aiohttp.ClientSession() as session:
        result = await http_check("http://invalid.domain.example", session, timeout_s=2)
        assert result.is_up is False
        assert result.status_code is None or isinstance(result.status_code, int)


@pytest.mark.asyncio
async def test_http_check_success_google():
    async with aiohttp.ClientSession() as session:
        result = await http_check("https://example.com", session, timeout_s=10)
        assert result.response_ms is not None
        assert isinstance(result.is_up, bool)
