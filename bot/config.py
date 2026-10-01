"""
Configuration management for Orion Bot.
Loads environment variables from .env with validation and sane defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Set
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root
load_dotenv(dotenv_path=BASE_DIR / ".env")


class ConfigError(ValueError):
    """Raised when required configuration is missing or invalid."""
    pass


class Config:
    def __init__(self) -> None:
        self.bot_token: str = os.getenv("BOT_TOKEN", "").strip()
        if not self.bot_token:
            raise ConfigError("BOT_TOKEN is required. Please set it in your .env file.")

        allowed_users_raw = os.getenv("ALLOWED_USERS", "").strip()
        self.allowed_users: Set[int] = set()
        if allowed_users_raw:
            for item in allowed_users_raw.split(","):
                cleaned = item.strip()
                if cleaned:
                    try:
                        self.allowed_users.add(int(cleaned))
                    except ValueError:
                        raise ConfigError(
                            f"Invalid Telegram User ID in ALLOWED_USERS: '{cleaned}'. Must be integer IDs."
                        )

        # Download directory
        download_dir_raw = os.getenv("DOWNLOAD_DIR", "downloads").strip()
        download_path = Path(download_dir_raw)
        if not download_path.is_absolute():
            self.download_dir: Path = (BASE_DIR / download_path).resolve()
        else:
            self.download_dir = download_path.resolve()

        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Custom Telegram Bot API Server (supports up to 2GB file transfers)
        self.bot_api_server: str | None = os.getenv("BOT_API_SERVER", "").strip() or None
        is_local_raw = os.getenv("BOT_API_IS_LOCAL", "").strip().lower()
        if is_local_raw in ("true", "1", "yes"):
            self.is_local_api: bool = True
        elif is_local_raw in ("false", "0", "no"):
            self.is_local_api = False
        else:
            # Auto-detect local server if URL contains localhost or 127.0.0.1
            self.is_local_api = bool(
                self.bot_api_server and ("localhost" in self.bot_api_server or "127.0.0.1" in self.bot_api_server)
            )

        # Maximum file size in MB (defaults to 2000 if custom API server, otherwise 50)
        default_max = 2000 if self.bot_api_server else 50
        try:
            self.max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", str(default_max)))
        except ValueError:
            self.max_file_size_mb = default_max


    def is_user_allowed(self, user_id: int | None) -> bool:
        """Check if user_id is in allowed_users. If allowed_users is empty, deny by default for security."""
        if user_id is None:
            return False
        if not self.allowed_users:
            return False
        return user_id in self.allowed_users


# Lazy or explicit config instance
_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
