"""
Security and Access Control Middleware for Orion Bot.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import Config

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Middleware ensuring only allowed users can interact with Orion Bot.
    """

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        user_id = user.id
        username = f"@{user.username}" if user.username else "No username"

        if not self.config.is_user_allowed(user_id):
            logger.warning(
                f"Unauthorized access attempt by user {user_id} ({username})"
            )

            # Reply with helpful info to Message or CallbackQuery
            denial_text = (
                f"⛔ <b>Access Denied</b>\n\n"
                f"Your Telegram User ID: <code>{user_id}</code>\n"
                f"This Orion instance is private.\n\n"
                f"To authorize your account, add your User ID to the <code>ALLOWED_USERS</code> "
                f"variable in your server's <code>.env</code> file and restart the bot."
            )

            if isinstance(event, Message):
                try:
                    await event.answer(denial_text, parse_mode="HTML")
                except Exception as e:
                    logger.debug(f"Failed to send denial message: {e}")
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer("Access Denied.", show_alert=True)
                except Exception as e:
                    logger.debug(f"Failed to answer callback query: {e}")

            # Do not proceed to handler
            return None

        return await handler(event, data)
