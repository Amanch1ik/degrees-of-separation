from dataclasses import dataclass
import os


@dataclass
class Settings:
    telegram_bot_token: str
    admin_user_id: int | None
    database_url: str
    max_concurrent_checks: int
    weekly_report_hour: int
    weekly_report_minute: int
    weekly_report_day_of_week: str


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        admin_user_id=int(os.getenv("ADMIN_USER_ID", "0")) or None,
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/monitor.db"),
        max_concurrent_checks=int(os.getenv("MAX_CONCURRENT_CHECKS", "10")),
        weekly_report_hour=int(os.getenv("WEEKLY_REPORT_HOUR", "9")),
        weekly_report_minute=int(os.getenv("WEEKLY_REPORT_MINUTE", "0")),
        weekly_report_day_of_week=os.getenv("WEEKLY_REPORT_DAY_OF_WEEK", "mon"),
    )
