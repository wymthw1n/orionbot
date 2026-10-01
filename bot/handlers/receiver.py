"""
Incoming file receiver handler.
Automatically downloads documents, photos, audio, video, etc., into the configured download folder.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from aiogram import Bot, F, Router
from aiogram.types import Message

from bot.config import get_config
from bot.utils.file_ops import (
    get_unique_filepath,
    human_readable_size,
    sanitize_filename,
)

logger = logging.getLogger(__name__)
router = Router()

# Telegram Bot API limits file downloads to 20MB unless using a custom local Bot API server
TELEGRAM_DOWNLOAD_LIMIT_BYTES = 20 * 1024 * 1024


async def handle_incoming_file(
    message: Message,
    bot: Bot,
    file_id: str,
    original_name: str,
    file_size: int | None = None,
) -> None:
    config = get_config()

    # Check size if available
    if file_size:
        max_bytes = config.max_file_size_mb * 1024 * 1024
        # Standard Bot API limit is 20MB for downloads if no custom bot api server
        effective_limit = max_bytes if config.bot_api_server else min(max_bytes, TELEGRAM_DOWNLOAD_LIMIT_BYTES)

        if file_size > effective_limit:
            limit_mb = round(effective_limit / (1024 * 1024))
            server_note = (
                "" if config.bot_api_server else
                "\n\n<i>Note: Telegram's official Bot API limits bot downloads to 20MB. "
                "To transfer up to 2GB files, configure a local Telegram Bot API Server.</i>"
            )
            await message.reply(
                f"❌ <b>File too large to download!</b>\n"
                f"• File size: <code>{human_readable_size(file_size)}</code>\n"
                f"• Limit: <code>{limit_mb} MB</code>{server_note}",
                parse_mode="HTML",
            )
            return

    safe_name = sanitize_filename(original_name)
    target_path = get_unique_filepath(config.download_dir, safe_name)

    size_label = human_readable_size(file_size) if file_size else "calculating..."
    status_msg = await message.reply(
        f"⏳ <b>Receiving file...</b>\n"
        f"📁 Name: <code>{safe_name}</code>\n"
        f"📦 Size: {size_label}",
        parse_mode="HTML",
    )

    start_time = time.monotonic()
    try:
        tg_file = await bot.get_file(file_id)
        if not tg_file.file_path:
            raise RuntimeError("Telegram did not provide a download file path.")

        # Download directly to destination
        await bot.download_file(tg_file.file_path, destination=target_path)
        elapsed = time.monotonic() - start_time

        actual_size = target_path.stat().st_size if target_path.exists() else (file_size or 0)
        formatted_size = human_readable_size(actual_size)

        # Show relative path if inside project, or absolute if outside
        try:
            display_path = target_path.relative_to(Path.cwd())
        except ValueError:
            display_path = target_path

        await status_msg.edit_text(
            f"✅ <b>File saved successfully!</b>\n\n"
            f"📁 <b>Name:</b> <code>{target_path.name}</code>\n"
            f"📦 <b>Size:</b> {formatted_size}\n"
            f"📍 <b>Location:</b> <code>{display_path}</code>\n"
            f"⏱ <b>Elapsed:</b> {elapsed:.2f}s",
            parse_mode="HTML",
        )
        logger.info(f"Saved file {target_path.name} ({formatted_size}) in {elapsed:.2f}s")

    except Exception as e:
        logger.exception(f"Error downloading file {safe_name}: {e}")
        # Clean up partial file if needed
        if target_path.exists() and target_path.stat().st_size == 0:
            target_path.unlink(missing_ok=True)

        err_text = str(e)
        if "file is too big" in err_text.lower():
            err_text += " (Telegram Bot API limit is 20MB for downloads)"

        await status_msg.edit_text(
            f"❌ <b>Download Failed</b>\n\n"
            f"📁 File: <code>{safe_name}</code>\n"
            f"⚠️ Reason: <code>{err_text}</code>",
            parse_mode="HTML",
        )


@router.message(F.document)
async def on_document(message: Message, bot: Bot) -> None:
    doc = message.document
    if not doc:
        return
    file_name = doc.file_name or f"document_{doc.file_unique_id}"
    await handle_incoming_file(
        message=message,
        bot=bot,
        file_id=doc.file_id,
        original_name=file_name,
        file_size=doc.file_size,
    )


@router.message(F.photo)
async def on_photo(message: Message, bot: Bot) -> None:
    photos = message.photo
    if not photos:
        return
    # Largest resolution photo is always last in the list
    photo = photos[-1]
    file_name = f"photo_{int(time.time())}_{photo.file_unique_id[:8]}.jpg"
    await handle_incoming_file(
        message=message,
        bot=bot,
        file_id=photo.file_id,
        original_name=file_name,
        file_size=photo.file_size,
    )


@router.message(F.video)
async def on_video(message: Message, bot: Bot) -> None:
    video = message.video
    if not video:
        return
    file_name = video.file_name or f"video_{int(time.time())}_{video.file_unique_id[:8]}.mp4"
    await handle_incoming_file(
        message=message,
        bot=bot,
        file_id=video.file_id,
        original_name=file_name,
        file_size=video.file_size,
    )


@router.message(F.audio)
async def on_audio(message: Message, bot: Bot) -> None:
    audio = message.audio
    if not audio:
        return
    file_name = audio.file_name or f"{audio.title or 'audio'}_{audio.file_unique_id[:8]}.mp3"
    await handle_incoming_file(
        message=message,
        bot=bot,
        file_id=audio.file_id,
        original_name=file_name,
        file_size=audio.file_size,
    )


@router.message(F.voice)
async def on_voice(message: Message, bot: Bot) -> None:
    voice = message.voice
    if not voice:
        return
    file_name = f"voice_{int(time.time())}_{voice.file_unique_id[:8]}.ogg"
    await handle_incoming_file(
        message=message,
        bot=bot,
        file_id=voice.file_id,
        original_name=file_name,
        file_size=voice.file_size,
    )


@router.message(F.video_note)
async def on_video_note(message: Message, bot: Bot) -> None:
    vnote = message.video_note
    if not vnote:
        return
    file_name = f"video_note_{int(time.time())}_{vnote.file_unique_id[:8]}.mp4"
    await handle_incoming_file(
        message=message,
        bot=bot,
        file_id=vnote.file_id,
        original_name=file_name,
        file_size=vnote.file_size,
    )


@router.message(F.animation)
async def on_animation(message: Message, bot: Bot) -> None:
    anim = message.animation
    if not anim:
        return
    file_name = anim.file_name or f"animation_{int(time.time())}_{anim.file_unique_id[:8]}.mp4"
    await handle_incoming_file(
        message=message,
        bot=bot,
        file_id=anim.file_id,
        original_name=file_name,
        file_size=anim.file_size,
    )
