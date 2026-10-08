import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH: str = os.getenv("DATABASE_PATH", "app.db")
REDIS_URL: str | None = os.getenv("REDIS_URL")
CLEANUP_INTERVAL_SECONDS: int = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "60"))
HOLD_TTL_MINUTES: int = int(os.getenv("HOLD_TTL_MINUTES", "5"))
MAX_SEATS_PER_USER_PER_EVENT: int = int(os.getenv("MAX_SEATS_PER_USER_PER_EVENT", "4"))
