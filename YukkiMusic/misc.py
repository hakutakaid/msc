import logging
import socket
import time

import heroku3
from pyrogram import filters

import config
from YukkiMusic.utils.database.mongodatabase import get_sudoers, add_sudo, remove_sudo # Import SQLite functions

SUDOERS = filters.user()


HAPP = None
_boot_ = time.time()
logger = logging.getLogger(__name__)


def is_heroku():
    # This function remains unchanged as it checks the environment
    return "heroku" in socket.getfqdn()


XCB = [
    "/",
    "@",
    ".",
    "com",
    ":",
    "git",
    "heroku",
    "push",
    str(config.HEROKU_API_KEY),
    "https",
    str(config.HEROKU_APP_NAME),
    "HEAD",
    "main",
]


def dbb():
    # This function was a placeholder for MongoDB initialization.
    # With SQLite, the database is initialized on import of core/sqlite.py,
    # so this specific function as it was is not strictly needed for DB setup.
    # It can be kept as a no-op or removed if no other logic relies on it.
    # For now, it's modified to reflect that DB is handled elsewhere.
    global db
    db = {} # Still initializes an empty dict as it did before.
    logger.info(f"Database Initialization Placeholder Executed (SQLite handled by core/sqlite.py).")


async def sudo():
    # Load sudoers from config.OWNER_ID and then from the database
    # The MongoDB logic is replaced with calls to the new SQLite functions
    
    # Always add OWNER_ID from config to SUDOERS filter and database
    for user_id in config.OWNER_ID:
        SUDOERS.add(user_id)
        # Add to SQLite database if not already present
        # The add_sudo function handles the upsert logic
        await add_sudo(user_id) 

    # Fetch all sudoers from the SQLite database
    db_sudoers = await get_sudoers()
    
    # Add all database sudoers to the SUDOERS filter
    for x in db_sudoers:
        SUDOERS.add(x)

    logger.info("Sudoers Loaded.")


def heroku():
    global HAPP
    if is_heroku(): # Call the function
        if config.HEROKU_API_KEY and config.HEROKU_APP_NAME:
            try:
                Heroku = heroku3.from_key(config.HEROKU_API_KEY)
                HAPP = Heroku.app(config.HEROKU_APP_NAME)
                logger.info(f"Heroku App Configured")
            except Exception as e: # Catch the specific exception
                logger.warning(
                    f"Please make sure your Heroku API Key and Your App name are configured correctly in the heroku. Error: {e}"
                )