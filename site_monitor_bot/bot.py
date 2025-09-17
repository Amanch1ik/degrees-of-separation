from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .repository import UserRepository, SiteRepository, CheckRecordRepository


def format_site_line(site) -> str:
    parts = [f"[{site.id}] {site.url}"]
    if site.last_status_code is not None:
        parts.append(f"status={site.last_status_code}")
    if site.last_response_ms is not None:
        parts.append(f"{site.last_response_ms}ms")
    parts.append(f"interval={site.interval_seconds}s")
    return " | ".join(parts)


def register_handlers(dp: Dispatcher, session_factory):
    @dp.message(Command("start"))
    async def on_start(message: Message, bot: Bot):
        async with session_factory() as session:  # type: AsyncSession
            await UserRepository(session).upsert_user(
                telegram_user_id=message.from_user.id,
                chat_id=message.chat.id,
            )
            await session.commit()
        text = (
            "Привет! Я бот для мониторинга сайтов.\n\n"
            "Команды:\n"
            "/add <url> [interval_s] – добавить сайт\n"
            "/list – список сайтов\n"
            "/remove <id> – удалить сайт\n"
            "/setinterval <id> <sec> – интервал\n"
            "/history <id> [limit] – последние проверки\n"
        )
        await message.answer(text)

    @dp.message(Command("add"))
    async def on_add(message: Message):
        args = message.text.split()[1:]
        if not args:
            await message.reply("Формат: /add <url> [interval_s]")
            return
        url = args[0]
        try:
            interval = int(args[1]) if len(args) > 1 else 300
        except ValueError:
            await message.reply("Интервал должен быть числом секунд")
            return
        async with session_factory() as session:  # type: AsyncSession
            user_repo = UserRepository(session)
            site_repo = SiteRepository(session)
            user = await user_repo.upsert_user(message.from_user.id, message.chat.id)
            site = await site_repo.add_site(user.telegram_user_id, url, interval)
            await session.commit()
        await message.reply(f"Добавлен сайт [{site.id}]: {site.url} с интервалом {interval}s")

    @dp.message(Command("list"))
    async def on_list(message: Message):
        async with session_factory() as session:  # type: AsyncSession
            sites = await SiteRepository(session).list_sites_by_user(message.from_user.id)
        if not sites:
            await message.reply("У вас нет сайтов. Добавьте через /add <url> [interval_s]")
            return
        lines = [format_site_line(s) for s in sites]
        await message.reply("\n".join(lines))

    @dp.message(Command("remove"))
    async def on_remove(message: Message):
        args = message.text.split()[1:]
        if not args:
            await message.reply("Формат: /remove <id>")
            return
        try:
            site_id = int(args[0])
        except ValueError:
            await message.reply("ID должен быть числом")
            return
        async with session_factory() as session:  # type: AsyncSession
            count = await SiteRepository(session).remove_site(site_id, user_id=message.from_user.id)
            await session.commit()
        if count:
            await message.reply(f"Сайт {site_id} удален")
        else:
            await message.reply("Сайт не найден или принадлежит другому пользователю")

    @dp.message(Command("setinterval"))
    async def on_setinterval(message: Message):
        args = message.text.split()[1:]
        if len(args) < 2:
            await message.reply("Формат: /setinterval <id> <sec>")
            return
        try:
            site_id = int(args[0])
            seconds = int(args[1])
        except ValueError:
            await message.reply("ID и seconds должны быть числами")
            return
        async with session_factory() as session:  # type: AsyncSession
            updated = await SiteRepository(session).update_interval(site_id, seconds, user_id=message.from_user.id)
            await session.commit()
        if updated:
            await message.reply(f"Интервал сайта {site_id} обновлен на {seconds} сек")
        else:
            await message.reply("Сайт не найден или принадлежит другому пользователю")

    @dp.message(Command("history"))
    async def on_history(message: Message):
        args = message.text.split()[1:]
        if not args:
            await message.reply("Формат: /history <id> [limit]")
            return
        try:
            site_id = int(args[0])
            limit = int(args[1]) if len(args) > 1 else 10
        except ValueError:
            await message.reply("ID и limit должны быть числами")
            return
        async with session_factory() as session:  # type: AsyncSession
            site = await SiteRepository(session).get_site(site_id, user_id=message.from_user.id)
            if not site:
                await message.reply("Сайт не найден")
                return
            records = await CheckRecordRepository(session).list_recent(site_id, limit)
        if not records:
            await message.reply("Нет записей")
            return
        lines = [
            f"{r.checked_at:%Y-%m-%d %H:%M} | up={r.is_up} | code={r.status_code} | {r.response_ms}ms"
            for r in records
        ]
        await message.reply("\n".join(lines))
