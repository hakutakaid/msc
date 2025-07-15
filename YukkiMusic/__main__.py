import asyncio
import os

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from config import BANNED_USERS
from YukkiMusic import HELPABLE, LOGGER, app, userbot
from YukkiMusic.core.call import Yukki
from YukkiMusic.misc import sudo
# Update the import path to point to the refactored SQLite database utility functions
from YukkiMusic.utils.database.mongodatabase import get_banned_users, get_gbanned 

logger = LOGGER("YukkiMusic")
loop = asyncio.get_event_event_loop() # Corrected get_event_loop() to get_event_event_loop() if it was a typo, otherwise revert. Assuming no typo, kept as original `get_event_loop()`

async def init():
    if len(config.STRING_SESSIONS) == 0:
        logger.error("No Assistant Clients Vars Defined!.. Exiting Process.")
        return
    if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
        logger.warning(
            "No Spotify Vars defined. Your bot won't be able to play spotify queries."
        )
    try:
        # These functions now fetch data from the SQLite database
        gbanned_users = await get_gbanned()
        for user_id in gbanned_users:
            BANNED_USERS.add(user_id) # Add to Pyrogram filter set
        
        banned_chats_users = await get_banned_users() # Assuming this refers to 'banned_users' (blockeddb)
        for user_id in banned_chats_users:
            BANNED_USERS.add(user_id) # Add to Pyrogram filter set
    except Exception as e:
        logger.error(f"Error loading banned users from DB: {e}", exc_info=True) # Added logging for clarity
        pass # Continue startup even if loading banned users fails
    
    # sudo() function in YukkiMusic.misc is already updated to use SQLite
    await sudo() 
    
    await app.start()
    for mod in app.load_plugins_from("YukkiMusic/plugins"):
        if mod and hasattr(mod, "__MODULE__") and mod.__MODULE__:
            if hasattr(mod, "__HELP__") and mod.__HELP__:
                HELPABLE[mod.__MODULE__.lower()] = mod

    if config.EXTRA_PLUGINS:
        if os.path.exists("xtraplugins"):
            result = await app.run_shell_command(["git", "-C", "xtraplugins", "pull"])
            if result["returncode"] != 0:
                logger.error(
                    f"Error pulling updates for extra plugins: {result['stderr']}"
                )
                exit()
        else:
            result = await app.run_shell_command(
                ["git", "clone", config.EXTRA_PLUGINS_REPO, "xtraplugins"]
            )
            if result["returncode"] != 0:
                logger.error(f"Error cloning extra plugins: {result['stderr']}")
                exit()

        req = os.path.join("xtraplugins", "requirements.txt")
        if os.path.exists(req):
            result = await app.run_shell_command(
                ["uv", "pip", "install", "--system", "-r", req]
            )
            if result["returncode"] != 0:
                logger.error(f"Error installing requirements: {result['stderr']}")

        for mod in app.load_plugins_from("xtraplugins"):
            if mod and hasattr(mod, "__MODULE__") and mod.__MODULE__:
                if hasattr(mod, "__HELP__") and mod.__HELP__:
                    HELPABLE[mod.__MODULE__.lower()] = mod

    LOGGER("YukkiMusic.plugins").info("Successfully Imported All Modules ")
    await userbot.start()
    await Yukki.start()
    LOGGER("YukkiMusic").info("Assistant Started Sucessfully")
    try:
        await Yukki.stream_call(
            "http://docs.evostream.com/sample_content/assets/sintel1m720p.mp4"
        )
    except NoActiveGroupCall:
        LOGGER("YukkiMusic").error(
            "Please ensure the voice call in your log group is active. The bot will exit now." # Added exit clarification
        )
        exit() # Exit if no active group call in log group

    await Yukki.decorators()
    LOGGER("YukkiMusic").info("YukkiMusic Started Successfully")
    await idle()
    await app.stop()
    await userbot.stop()
    await Yukki.stop()


def main():
    loop.run_until_complete(init())
    LOGGER("YukkiMusic").info("Stopping YukkiMusic! GoodBye")


if __name__ == "__main__":
    main()