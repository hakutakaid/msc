from pyrogram import filters
from pyrogram.types import Message

# MONGO_DB_URI is no longer relevant for this module's logic
from config import BANNED_USERS, OWNER_ID
from strings import command
from YukkiMusic import app
from YukkiMusic.misc import SUDOERS
# Ensure these imports point to your SQLite-backed functions
from YukkiMusic.utils.database.mongodatabase import add_sudo, remove_sudo # It's okay to keep this path if you refactored the file.
from YukkiMusic.utils.decorators.language import language


@app.on_message(command("ADDSUDO_COMMAND") & filters.user(OWNER_ID))
@language
async def useradd(client, message: Message, _):
    # The check for MONGO_DB_URI is removed as we are now exclusively using SQLite.
    # The bot will always be on the "Yukki Database" (SQLite).

    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
        user_input = message.text.split(None, 1)[1] # Renamed from 'user' to avoid confusion with Pyrogram's user object
        if "@" in user_input:
            user_input = user_input.replace("@", "")
        
        try:
            user = await app.get_users(user_input)
        except Exception:
            return await message.reply_text(_["general_2"]) # Add a generic error message for user not found if needed, or let Pyrogram handle it.

        if user.id in SUDOERS:
            return await message.reply_text(_["sudo_1"].format(user.mention))
        
        added = await add_sudo(user.id)
        if added:
            SUDOERS.add(user.id)
            await message.reply_text(_["sudo_2"].format(user.mention))
        else:
            await message.reply_text("Something wrong happened while adding sudo user.") # More descriptive error
        return
    
    # Logic for reply_to_message
    target_user = message.reply_to_message.from_user
    if target_user.id in SUDOERS:
        return await message.reply_text(
            _["sudo_1"].format(target_user.mention)
        )
    
    added = await add_sudo(target_user.id)
    if added:
        SUDOERS.add(target_user.id)
        await message.reply_text(
            _["sudo_2"].format(target_user.mention)
        )
    else:
        await message.reply_text("Something wrong happened while adding sudo user from reply.")
    return


@app.on_message(command("DELSUDO_COMMAND") & filters.user(OWNER_ID))
@language
async def userdel(client, message: Message, _):
    # The check for MONGO_DB_URI is removed.

    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
        user_input = message.text.split(None, 1)[1] # Renamed
        if "@" in user_input:
            user_input = user_input.replace("@", "")
        
        try:
            user = await app.get_users(user_input)
        except Exception:
            return await message.reply_text(_["general_2"]) # Add generic error for user not found

        if user.id not in SUDOERS:
            return await message.reply_text(_["sudo_3"])
        
        removed = await remove_sudo(user.id)
        if removed:
            SUDOERS.remove(user.id)
            await message.reply_text(_["sudo_4"])
            return
        await message.reply_text(f"Something wrong happened while removing sudo user.") # More descriptive error
        return
    
    # Logic for reply_to_message
    user_id = message.reply_to_message.from_user.id
    if user_id not in SUDOERS:
        return await message.reply_text(_["sudo_3"])
    
    removed = await remove_sudo(user_id)
    if removed:
        SUDOERS.remove(user_id)
        await message.reply_text(_["sudo_4"])
        return
    await message.reply_text(f"Something wrong happened while removing sudo user from reply.")


@app.on_message(command("SUDOUSERS_COMMAND") & ~BANNED_USERS)
@language
async def sudoers_list(client, message: Message, _):
    text = _["sudo_5"]
    count = 0
    # OWNER_ID is always considered sudo. Loop through it first.
    for x in OWNER_ID:
        try:
            user = await app.get_users(x)
            user_mention = user.mention if user.mention else user.first_name # Prefer mention if available
            count += 1
            text += f"{count}➤ {user_mention} (`{x}`)\n"
        except Exception:
            # Log the error if a user in OWNER_ID cannot be found/accessed
            logger.warning(f"Could not retrieve info for OWNER_ID: {x}")
            continue
    
    smex = 0 # This variable name is a bit unusual; consider renaming for clarity if possible.
    # Iterate through SUDOERS filter which is populated from both OWNER_ID and DB
    # and exclude those already listed from OWNER_ID to avoid duplicates.
    for user_id in SUDOERS:
        if user_id not in OWNER_ID: # Only add if not already in OWNER_ID list
            try:
                user = await app.get_users(user_id)
                user_mention = user.mention if user.mention else user.first_name
                if smex == 0:
                    smex += 1
                    text += _["sudo_6"] # "Additional Sudoers" or similar header
                count += 1
                text += f"{count}➤ {user_mention} (`{user_id}`)\n"
            except Exception:
                # Log the error if a user from SUDOERS cannot be found/accessed
                logger.warning(f"Could not retrieve info for sudo user: {user_id}")
                continue
    
    if not text.strip() == _["sudo_5"].strip(): # Check if only the initial header is present
        await message.reply_text(text)
    else:
        # If no sudoers are found beyond the default OWNER_ID (or if OWNER_ID failed to resolve)
        await message.reply_text(_["sudo_7"])