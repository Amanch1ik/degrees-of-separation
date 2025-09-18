from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy import select, func
from typing import Optional
import hashlib
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False)

    sites: Mapped[list[Site]] = relationship("Site", back_populates="user", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_user_id"), index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_response_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="sites")
    records: Mapped[list[CheckRecord]] = relationship("CheckRecord", back_populates="site", cascade="all, delete-orphan")


class CheckRecord(Base):
    __tablename__ = "check_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_up: Mapped[bool] = mapped_column(Boolean, default=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    site: Mapped[Site] = relationship("Site", back_populates="records")


def create_engine_and_session(database_url: str):
    engine = create_async_engine(database_url, echo=False, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, session_factory


async def init_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
