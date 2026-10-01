"""
Unit tests for bot/config.py.
"""

import os
from unittest import mock
import pytest
from bot.config import Config, ConfigError


def test_missing_bot_token_raises_error() -> None:
    with mock.patch.dict(os.environ, {"BOT_TOKEN": ""}, clear=True):
        with pytest.raises(ConfigError, match="BOT_TOKEN is required"):
            Config()


def test_valid_config_loading(tmp_path) -> None:
    env_vars = {
        "BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "ALLOWED_USERS": "12345678, 87654321",
        "DOWNLOAD_DIR": str(tmp_path / "custom_downloads"),
        "MAX_FILE_SIZE_MB": "100",
    }
    with mock.patch.dict(os.environ, env_vars, clear=True):
        config = Config()
        assert config.bot_token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert config.allowed_users == {12345678, 87654321}
        assert config.max_file_size_mb == 100
        assert config.download_dir.exists()
        assert config.is_user_allowed(12345678) is True
        assert config.is_user_allowed(99999999) is False
        assert config.is_user_allowed(None) is False


def test_local_api_config(tmp_path) -> None:
    env_vars = {
        "BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "ALLOWED_USERS": "12345678",
        "BOT_API_SERVER": "http://127.0.0.1:8081",
    }
    with mock.patch.dict(os.environ, env_vars, clear=True):
        config = Config()
        assert config.bot_api_server == "http://127.0.0.1:8081"
        assert config.is_local_api is True
        assert config.max_file_size_mb == 2000


def test_invalid_allowed_users_raises_error() -> None:
    env_vars = {
        "BOT_TOKEN": "123456:test",
        "ALLOWED_USERS": "12345,not_an_int",
    }
    with mock.patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ConfigError, match="Invalid Telegram User ID"):
            Config()

