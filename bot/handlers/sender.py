"""
File sender and file browser handlers.
Allows sending files from VPS to Telegram user via /send, /get, and /list.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.config import get_config
from bot.utils.file_ops import (
    human_readable_size,
    list_directory_files,
)

logger = logging.getLogger(__name__)
router = Router()

# Telegram Bot API limits sending files to 50MB (unless using custom Bot API server)
TELEGRAM_UPLOAD_LIMIT_BYTES = 50 * 1024 * 1024


async def send_file_to_user(
    message: Message | CallbackQuery,
    bot: Bot,
    file_path: Path,
) -> None:
    config = get_config()

    if not file_path.exists():
        err = f"❌ File not found: <code>{file_path.name}</code>"
        if isinstance(message, CallbackQuery):
            await message.answer("File not found!", show_alert=True)
            return
        await message.reply(err, parse_mode="HTML")
        return

    if not file_path.is_file():
        err = f"❌ Specified path is a directory, not a file: <code>{file_path}</code>"
        if isinstance(message, CallbackQuery):
            await message.answer("Not a file!", show_alert=True)
            return
        await message.reply(err, parse_mode="HTML")
        return

    file_size = file_path.stat().st_size
    max_bytes = config.max_file_size_mb * 1024 * 1024
    effective_limit = max_bytes if config.bot_api_server else min(max_bytes, TELEGRAM_UPLOAD_LIMIT_BYTES)

    if file_size > effective_limit:
        limit_mb = round(effective_limit / (1024 * 1024))
        err = (
            f"❌ <b>File too large to send!</b>\n\n"
            f"• File: <code>{file_path.name}</code>\n"
            f"• Size: <code>{human_readable_size(file_size)}</code>\n"
            f"• Limit: <code>{limit_mb} MB</code>\n\n"
            f"<i>Telegram Bot API limits bot file sending to 50MB. "
            f"Consider splitting or compressing the file.</i>"
        )
        if isinstance(message, CallbackQuery):
            await message.answer("File exceeds 50MB limit!", show_alert=True)
            if message.message:
                await message.message.reply(err, parse_mode="HTML")
            return
        await message.reply(err, parse_mode="HTML")
        return

    chat_id = message.message.chat.id if isinstance(message, CallbackQuery) and message.message else message.chat.id
    target_msg = message.message if isinstance(message, CallbackQuery) else message

    status_msg = await target_msg.reply(
        f"📤 <b>Uploading to Telegram...</b>\n"
        f"📁 <code>{file_path.name}</code> ({human_readable_size(file_size)})",
        parse_mode="HTML",
    )

    start_time = time.monotonic()
    try:
        input_file = FSInputFile(str(file_path), filename=file_path.name)
        caption = (
            f"📦 <b>{file_path.name}</b>\n"
            f"📏 Size: {human_readable_size(file_size)}"
        )
        await bot.send_document(
            chat_id=chat_id,
            document=input_file,
            caption=caption,
            parse_mode="HTML",
        )
        elapsed = time.monotonic() - start_time
        await status_msg.edit_text(
            f"✅ <b>Sent successfully!</b>\n"
            f"📁 <code>{file_path.name}</code>\n"
            f"⏱ Upload time: {elapsed:.2f}s",
            parse_mode="HTML",
        )
        logger.info(f"Sent {file_path.name} ({human_readable_size(file_size)}) in {elapsed:.2f}s")
    except Exception as e:
        logger.exception(f"Error sending file {file_path}: {e}")
        await status_msg.edit_text(
            f"❌ <b>Failed to send file</b>\n\n"
            f"⚠️ Reason: <code>{e}</code>",
            parse_mode="HTML",
        )


@router.message(Command("send"))
async def cmd_send(message: Message, bot: Bot) -> None:
    config = get_config()
    text = message.text or ""
    parts = text.strip().split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        await message.reply(
            "ℹ️ <b>Usage:</b> <code>/send &lt;filepath&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/send downloads/backup.zip</code>\n"
            "• <code>/send report.pdf</code> (looks in downloads folder first)\n"
            "• <code>/send /var/log/syslog</code>\n\n"
            "💡 Or use <code>/list</code> to pick files with 1-tap buttons!",
            parse_mode="HTML",
        )
        return

    raw_path = parts[1].strip()

    # Resolution strategy:
    # 1. Check if relative to download_dir
    cand1 = config.download_dir / raw_path
    if cand1.exists() and cand1.is_file():
        file_path = cand1
    else:
        # 2. Check if absolute or relative to current working directory
        cand2 = Path(raw_path)
        if not cand2.is_absolute():
            cand2 = (Path.cwd() / cand2).resolve()
        file_path = cand2

    await send_file_to_user(message, bot, file_path)


@router.message(Command("get"))
async def cmd_get(message: Message, bot: Bot) -> None:
    config = get_config()
    text = message.text or ""
    parts = text.strip().split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        await message.reply(
            "ℹ️ <b>Usage:</b> <code>/get &lt;filename&gt;</code>\n\n"
            f"Fetches a file located in <code>{config.download_dir}</code>.\n"
            "Example: <code>/get document.pdf</code>\n\n"
            "Tip: Use <code>/list</code> to see all available files.",
            parse_mode="HTML",
        )
        return

    filename = parts[1].strip()
    file_path = config.download_dir / filename
    await send_file_to_user(message, bot, file_path)


@router.message(Command("list", "ls"))
async def cmd_list(message: Message) -> None:
    config = get_config()
    files, total = list_directory_files(config.download_dir, limit=15)

    if total == 0:
        await message.reply(
            f"📂 <b>Download storage is currently empty.</b>\n\n"
            f"Path: <code>{config.download_dir}</code>\n"
            f"Send any file to this bot to save it here!",
            parse_mode="HTML",
        )
        return

    lines = [
        f"📂 <b>Files in Orion Storage</b> ({len(files)} of {total} shown):",
        f"📍 <code>{config.download_dir}</code>\n",
    ]

    keyboard_rows: list[list[InlineKeyboardButton]] = []

    for idx, f in enumerate(files, 1):
        lines.append(f"{idx}. <b>{f['name']}</b> ({f['size']}) — <i>{f['mtime']}</i>")
        # Build 1-tap download button (callback data has max 64 bytes limit in Telegram)
        # Use filename or truncated filename safely
        cb_name = str(f["name"])
        # Callback data: 'dl:<idx>' or short name
        keyboard_rows.append(
            [InlineKeyboardButton(text=f"📥 Download #{idx} ({f['size']})", callback_data=f"dl:{idx-1}")]
        )

    lines.append("\n💡 <i>Tap a button below or type <code>/get filename</code> to download.</i>")
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await message.reply("\n".join(lines), reply_markup=markup, parse_mode="HTML")


@router.callback_query(lambda c: c.data and c.data.startswith("dl:"))
async def on_download_callback(callback: CallbackQuery, bot: Bot) -> None:
    config = get_config()
    try:
        idx = int(callback.data.split(":", 1)[1])
        files, _ = list_directory_files(config.download_dir, limit=50)
        if 0 <= idx < len(files):
            target_path = Path(files[idx]["path"])
            await callback.answer(f"Fetching {target_path.name}...")
            await send_file_to_user(callback, bot, target_path)
        else:
            await callback.answer("File index expired. Please run /list again.", show_alert=True)
    except Exception as e:
        logger.exception(f"Callback error: {e}")
        await callback.answer("Error fetching file.", show_alert=True)
