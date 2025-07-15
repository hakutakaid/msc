import asyncio
import os
import shutil # For copying files safely
import logging # For logging potential issues

from pyrogram import filters
from pyrogram.errors import FloodWait, MessageIdInvalid # Added MessageIdInvalid for robustness

from config import BANNED_USERS, OWNER_ID # MONGO_DB_URI is no longer needed here
from YukkiMusic import app
from YukkiMusic.core.sqlite import DB_FILE # Import the SQLite database file path

LOGGER = logging.getLogger(__name__)

async def edit_or_reply(mystic, text):
    """Helper function to edit or reply to a message, handling FloodWait."""
    try:
        return await mystic.edit_text(text, disable_web_page_preview=True)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await mystic.edit_text(text, disable_web_page_preview=True)
    except MessageIdInvalid: # Handle cases where message might have been deleted
        LOGGER.warning(f"Message ID invalid for editing, sending new message instead.")
        return await app.send_message(mystic.chat.id, text, disable_web_page_preview=True)
    except Exception: # Fallback to sending new message if edit fails for other reasons
        LOGGER.exception("Failed to edit message, sending new message.")
        return await app.send_message(mystic.chat.id, text, disable_web_page_preview=True)


@app.on_message(filters.command("export") & filters.user(OWNER_ID) & ~BANNED_USERS)
async def export_database(client, message):
    """
    Exports the SQLite database file.
    """
    mystic = await message.reply_text("Preparing to export your SQLite database...")

    if not os.path.exists(DB_FILE):
        return await edit_or_reply(mystic, f"Error: SQLite database file `{DB_FILE}` not found.")

    try:
        # Send the SQLite database file
        await app.send_document(
            chat_id=message.chat.id,
            document=DB_FILE,
            caption=f"YukkiMusic SQLite Database Backup ({os.path.basename(DB_FILE)})",
            file_name=os.path.basename(DB_FILE), # Ensure the file name is correct
            progress=lambda current, total: asyncio.create_task(
                edit_or_reply(mystic, f"Uploading database... {current * 100 / total:.1f}%")
            )
        )
        await mystic.delete() # Delete the "Uploading..." message
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await app.send_document(
            chat_id=message.chat.id,
            document=DB_FILE,
            caption=f"YukkiMusic SQLite Database Backup ({os.path.basename(DB_FILE)})",
            file_name=os.path.basename(DB_FILE)
        )
        await mystic.delete()
    except Exception as e:
        LOGGER.error(f"Error exporting SQLite database: {e}", exc_info=True)
        await edit_or_reply(mystic, f"Failed to export database: {e}")


@app.on_message(filters.command("import") & filters.user(OWNER_ID) & ~BANNED_USERS)
async def import_database(client, message):
    """
    Imports an SQLite database file, replacing the current one.
    WARNING: This operation will overwrite your existing database and requires bot restart.
    """
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply_text(
            "To import, reply to an SQLite database file (`.db` extension)."
        )

    # Check if the replied document is likely an SQLite database file
    if not message.reply_to_message.document.file_name.endswith(".db"):
        return await message.reply_text(
            "The replied file does not seem to be an SQLite database. Please reply to a `.db` file."
        )

    mystic = await message.reply_text("Downloading database file...")

    download_path = os.path.join("cache", message.reply_to_message.document.file_name)

    try:
        # Download the new database file
        await message.reply_to_message.download(
            file_name=download_path,
            progress=lambda current, total: asyncio.create_task(
                edit_or_reply(mystic, f"Downloading... {current * 100 / total:.1f}%")
            )
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_to_message.download(file_name=download_path)
    except Exception as e:
        LOGGER.error(f"Error downloading database file: {e}", exc_info=True)
        return await edit_or_reply(mystic, f"Failed to download database file: {e}")

    try:
        # Crucial step: Replace the existing database file
        # It's best to stop the bot or ensure no active DB connections before this.
        # For a live bot, this is risky. A full restart is recommended after.
        
        # Make a quick backup of the *current* database before overwriting
        backup_current_db_path = f"{DB_FILE}.pre_import_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if os.path.exists(DB_FILE):
            shutil.copy2(DB_FILE, backup_current_db_path)
            LOGGER.info(f"Backed up current DB to: {backup_current_db_path}")

        shutil.move(download_path, DB_FILE)
        
        await edit_or_reply(
            mystic,
            f"Database imported successfully! The bot needs to be **restarted** for changes to take effect.\n\n"
            f"**WARNING:** Your old database was backed up to `{backup_current_db_path}` in the bot's cache directory. "
            f"Please ensure you restart the bot immediately."
        )
        LOGGER.info(f"SQLite database replaced with {download_path}. Restart required.")

    except Exception as e:
        LOGGER.error(f"Error during database import/replacement: {e}", exc_info=True)
        await edit_or_reply(mystic, f"Error during import: {e}\n\n"
                                     f"The database might be corrupted. Please check bot logs and restart manually.")
    finally:
        # Clean up the downloaded file if it still exists in cache
        if os.path.exists(download_path):
            os.remove(download_path)