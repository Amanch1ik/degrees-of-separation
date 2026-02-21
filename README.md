## Telegram Website Monitoring B
- Weekly summary reports
- History and uptime statistics

### Tech Stack
- Python 3.10+
- aiogram 3.x
- SQLAlchemy 2.x (async, SQLite via aiosqlite)
- aiohttp, APScheduler

### Quick Start
1) Create and fill environment file:
```
cp .env.example .env
```
Edit `.env` with your values.

2) (Optional) Create and activate venv.

3) Install dependencies:
```
pip install -r requirements.txt
```

4) Run the bot:
```
python -m site_monitor_bot
```

### Commands (basic)
- /start – welcome and help
- /add <url> [interval_s] – add a site with interval in seconds (default 300)
- /list – list your monitored sites
- /remove <site_id> – remove a site
- /setinterval <site_id> <seconds> – change interval
- /history <site_id> [limit] – show recent checks

### Database Schema (simplified)
- `users`(telegram_user_id PK, chat_id)
- `sites`(id PK, user_id FK, url, interval_seconds, is_active, last_status_code, last_response_ms, last_content_hash, last_checked_at, next_check_at)
- `check_records`(id PK, site_id FK, checked_at, status_code, response_ms, is_up, content_hash, error)

### Testing
```
pytest -q
```

### Notes
- Logging via Loguru, configuration in `site_monitor_bot/logging_config.py`
- Error handling: all network and DB ops are guarded; retries can be added if needed
