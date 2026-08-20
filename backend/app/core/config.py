"""Application settings — env-driven, nothing school-specific hard-coded (REQ-CFG-01)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- app / environment ---
    app_name: str = "SMS"
    environment: str = "dev"  # dev | staging | prod
    dev_mode: bool = True  # relaxes cookie-secure; exposes dev reset tokens
    timezone: str = "Africa/Accra"

    # --- database ---
    database_url: str = "sqlite:///./dev.db"
    database_echo: bool = False

    # --- sessions / auth ---
    session_cookie_name: str = "sms_session"
    session_cookie_secure: bool = False  # True behind HTTPS in prod
    session_cookie_domain: str = ""
    session_idle_hours: int = 12
    session_absolute_days: int = 7
    csrf_header: str = "X-CSRF-Token"
    login_max_failures: int = 5
    login_lock_minutes: int = 15
    password_min_length: int = 10
    # Argon2id parameters (design §06). Tests may lower via env for speed.
    argon_time_cost: int = 3
    argon_memory_cost_kib: int = 64 * 1024
    argon_parallelism: int = 4

    # --- rate limiting (in-memory baseline; Redis-backed in prod) ---
    ratelimit_enabled: bool = True

    # --- school bootstrap defaults (configurable later via settings UI) ---
    default_school_name: str = "Hope Star Academy (DEMO)"
    admission_code_prefix: str = "HSA"
    receipt_prefix: str = "HSA"


@lru_cache
def get_settings() -> Settings:
    return Settings()
