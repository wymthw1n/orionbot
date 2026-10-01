"""
Main application entry point for Orion Telegram Bot.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from bot.config import ConfigError, get_config
from bot.handlers import receiver, sender, start
from bot.security import AuthMiddleware

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("orionbot")


async def main() -> None:
    try:
        config = get_config()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Configure custom Bot API server if specified (for up to 2GB large file transfers)
    session = None
    if config.bot_api_server:
        logger.info(
            f"Using custom Telegram Bot API Server: {config.bot_api_server} (is_local={config.is_local_api})"
        )
        server = TelegramAPIServer.from_base(config.bot_api_server, is_local=config.is_local_api)
        session = AiohttpSession(api=server)

    bot = Bot(
        token=config.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Security: Attach Authorization Middleware to all incoming messages and callbacks
    auth_mw = AuthMiddleware(config)
    dp.message.middleware(auth_mw)
    dp.callback_query.middleware(auth_mw)

    # Register handlers
    dp.include_router(start.router)
    dp.include_router(sender.router)
    dp.include_router(receiver.router)

    # Print startup banner
    bot_info = await bot.get_me()
    logger.info("=" * 50)
    logger.info(f"🚀 Orion Bot started successfully: @{bot_info.username} (ID: {bot_info.id})")
    logger.info(f"📁 Download Directory: {config.download_dir}")
    logger.info(f"👥 Authorized Users: {len(config.allowed_users)} configured")
    logger.info("=" * 50)

    try:
        # Start long polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Orion Bot terminated gracefully.")
