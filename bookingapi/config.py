import os

from dotenv import load_dotenv

load_dotenv()

# Subjects accepted by the API (must match the frontend list).
SUBJECTS = ["Middle School Math", "Algebra", "Geometry", "Pre-Calculus", "Computer Science"]


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    SUPABASE_URL = _require("SUPABASE_URL")
    SUPABASE_KEY = _require("SUPABASE_KEY")
    ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
    RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
    PROXY_HOPS = int(os.getenv("PROXY_HOPS", "1"))

    # Rate limits (Flask-Limiter syntax)
    DEFAULT_LIMIT = "120 per hour"
    READ_LIMIT = "60 per minute"
    BOOKING_LIMIT = "5 per hour;20 per day"

    # #Mail integration
    # MAIL_SERVER = 'smtp.gmail.com'
    # MAIL_PORT = 465
    # MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    # MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    # MAIL_USE_TLS = False
    # MAIL_USE_SSL = True
