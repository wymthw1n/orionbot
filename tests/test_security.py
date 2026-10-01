"""
Unit tests for bot/security.py AuthMiddleware.
"""

from unittest.mock import AsyncMock, MagicMock
import pytest
from aiogram.types import Message, User
from bot.config import Config
from bot.security import AuthMiddleware


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.is_user_allowed.side_effect = lambda uid: uid == 123456
    return config


@pytest.mark.asyncio
async def test_auth_middleware_allows_authorized_user(mock_config) -> None:
    middleware = AuthMiddleware(mock_config)
    handler = AsyncMock(return_value="handler_called")

    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "valid_user"

    message = MagicMock(spec=Message)
    data = {"event_from_user": user}

    result = await middleware(handler, message, data)
    assert result == "handler_called"
    handler.assert_awaited_once_with(message, data)


@pytest.mark.asyncio
async def test_auth_middleware_blocks_unauthorized_user(mock_config) -> None:
    middleware = AuthMiddleware(mock_config)
    handler = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 999999
    user.username = "intruder"

    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    data = {"event_from_user": user}

    result = await middleware(handler, message, data)
    assert result is None
    handler.assert_not_called()
    message.answer.assert_awaited_once()
    assert "Access Denied" in message.answer.call_args[0][0]
