"""
Start, help, id, and status command handlers.
"""

from __future__ import annotations

import os
from pathlib import Path
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import get_config
from bot.utils.file_ops import get_disk_usage, human_readable_size

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    config = get_config()
    first_name = message.from_user.first_name if message.from_user else "Commander"

    welcome_text = (
        f"🌌 <b>Welcome to Orion, {first_name}!</b>\n\n"
        f"Orion is your secure file bridge between Telegram and your VPS.\n\n"
        f"📥 <b>Upload files to VPS:</b>\n"
        f"Simply send any file, document, photo, video, or audio here. "
        f"It will be auto-saved to <code>{config.download_dir}</code>.\n\n"
        f"📤 <b>Download files from VPS:</b>\n"
        f"• <code>/list</code> — Browse and download files in storage\n"
        f"• <code>/get &lt;filename&gt;</code> — Fetch a specific file from storage\n"
        f"• <code>/send &lt;filepath&gt;</code> — Send any file from the VPS by path\n\n"
        f"ℹ️ <b>System:</b>\n"
        f"• <code>/status</code> — Check VPS disk space and storage stats\n"
        f"• <code>/id</code> — View your Telegram User ID\n"
        f"• <code>/help</code> — Full command manual\n"
    )
    await message.answer(welcome_text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    config = get_config()
    help_text = (
        "📖 <b>Orion Bot Commands Manual</b>\n\n"
        "<b>📥 Receiving / Auto-saving Files:</b>\n"
        "• Send any document, zip, image, video, audio, or archive.\n"
        f"• Files are instantly saved to <code>{config.download_dir}</code>.\n"
        "• If a file already exists, it is saved with a non-conflicting incrementing name.\n\n"
        "<b>📤 Sending Files from VPS to You:</b>\n"
        "• <code>/list</code> or <code>/ls</code> — List recently stored files with quick 1-tap download buttons.\n"
        "• <code>/get filename.ext</code> — Instantly fetch a file from the downloads directory.\n"
        "• <code>/send /path/to/file</code> — Send any file from your VPS by absolute or relative path.\n\n"
        "<b>📊 Diagnostics:</b>\n"
        "• <code>/status</code> — View VPS disk space usage and storage metrics.\n"
        "• <code>/id</code> — Display your Telegram User ID and Chat ID.\n"
        "• <code>/help</code> — Show this manual.\n\n"
        "💡 <i>Tip: Standard Telegram Bot API supports sending files up to 50MB and receiving up to 20MB.</i>"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else "Unknown"
    chat_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else "None"

    text = (
        f"🆔 <b>Telegram Identity Information</b>\n\n"
        f"• <b>User ID:</b> <code>{user_id}</code>\n"
        f"• <b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"• <b>Username:</b> {username}\n"
        f"• <b>Status:</b> ✅ Authorized"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("status", "disk"))
async def cmd_status(message: Message) -> None:
    config = get_config()
    disk = get_disk_usage(config.download_dir)

    # Calculate download dir metrics
    total_files = 0
    total_bytes = 0
    try:
        for root, _, files in os.walk(config.download_dir):
            for f in files:
                fp = Path(root) / f
                if fp.is_file():
                    total_files += 1
                    total_bytes += fp.stat().st_size
    except Exception:
        pass

    storage_used = human_readable_size(total_bytes)

    status_text = (
        "📊 <b>Orion VPS & Storage Status</b>\n\n"
        f"📁 <b>Storage Path:</b> <code>{config.download_dir}</code>\n"
        f"📦 <b>Stored Files:</b> <code>{total_files}</code> ({storage_used})\n\n"
        "<b>VPS Disk Usage:</b>\n"
        f"• <b>Total Space:</b> {disk['total']}\n"
        f"• <b>Used Space:</b> {disk['used']} ({disk['percent']}%)\n"
        f"• <b>Free Space:</b> {disk['free']}\n\n"
        f"⚡ <b>Max File Transfer Limit:</b> {config.max_file_size_mb} MB"
    )
    await message.answer(status_text, parse_mode="HTML")
