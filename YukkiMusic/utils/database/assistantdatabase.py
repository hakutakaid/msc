import random
import sqlite3

from pytgcalls import PyTgCalls

from YukkiMusic import userbot
from YukkiMusic.core.sqlite import get_db_connection, DB_FILE # Import from your new sqlite.py

# A simple in-memory cache, similar to the original assistantdict
assistantdict = {}

# We'll manage the database interaction directly in these functions.
# No direct 'db = mongodb.assistants' equivalent needed.

async def get_client(assistant: int):
    """
    Retrieves the userbot client for a given assistant number.
    This part remains the same as it interacts with the userbot module, not the database.
    """
    clients = userbot.clients
    if 1 <= assistant <= len(userbot.clients):
        return clients[assistant - 1]
    return None

async def save_assistant(chat_id: int, number: int):
    """
    Saves or updates the chosen assistant for a given chat_id in the database.
    """
    number = int(number)
    assistantdict[chat_id] = number

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO assistants (chat_id, assistant_number) VALUES (?, ?)",
            (chat_id, number)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving assistant for chat_id {chat_id}: {e}")
        # Depending on your error handling strategy, you might want to re-raise or log.
    finally:
        conn.close()
    
    # The original function returned await get_assistant(chat_id)
    # which would then return the userbot client. Let's maintain that behavior.
    return await get_client(number)


async def set_assistant(chat_id: int):
    """
    Selects and sets a random assistant for a chat_id,
    prioritizing a different one if one is currently set.
    """
    from YukkiMusic.core.userbot import assistants

    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_assistant = None
    try:
        cursor.execute("SELECT assistant_number FROM assistants WHERE chat_id = ?", (chat_id,))
        db_record = cursor.fetchone()
        if db_record:
            current_assistant = db_record['assistant_number']
    except sqlite3.Error as e:
        print(f"Error fetching current assistant for chat_id {chat_id}: {e}")
    finally:
        conn.close()

    available_assistants = [assi for assi in assistants if assi != current_assistant]

    if not available_assistants or len(available_assistants) <= 1: # Added check for empty list
        ran_assistant = random.choice(assistants)
    else:
        ran_assistant = random.choice(available_assistants)

    assistantdict[chat_id] = ran_assistant
    
    # Save the chosen assistant to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO assistants (chat_id, assistant_number) VALUES (?, ?)",
            (chat_id, ran_assistant)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting random assistant for chat_id {chat_id}: {e}")
    finally:
        conn.close()

    userbot_client = await get_client(ran_assistant)
    return userbot_client


async def get_assistant(chat_id: int):
    """
    Retrieves the assistant for a given chat_id, falling back to setting one if not found or invalid.
    """
    from YukkiMusic.core.userbot import assistants

    # 1. Check in-memory cache
    assistant = assistantdict.get(chat_id)

    if assistant:
        if assistant in assistants:
            # Found in cache and is valid
            userbot_client = await get_client(assistant)
            return userbot_client
        else:
            # Found in cache but invalid, set a new one
            userbot_client = await set_assistant(chat_id)
            return userbot_client
    else:
        # Not in cache, try database
        conn = get_db_connection()
        cursor = conn.cursor()
        db_assistant = None
        try:
            cursor.execute("SELECT assistant_number FROM assistants WHERE chat_id = ?", (chat_id,))
            db_record = cursor.fetchone()
            if db_record:
                db_assistant = db_record['assistant_number']
        except sqlite3.Error as e:
            print(f"Error fetching assistant from DB for chat_id {chat_id}: {e}")
        finally:
            conn.close()

        if db_assistant:
            if db_assistant in assistants:
                # Found in DB and valid, add to cache
                assistantdict[chat_id] = db_assistant
                userbot_client = await get_client(db_assistant)
                return userbot_client
            else:
                # Found in DB but invalid, set a new one
                userbot_client = await set_assistant(chat_id)
                return userbot_client
        else:
            # Not in DB, set a new one
            userbot_client = await set_assistant(chat_id)
            return userbot_client


async def set_calls_assistant(chat_id: int):
    """
    Selects and sets a random assistant for calls for a chat_id.
    This function seems to be specifically for PyTgCalls related assistant selection.
    """
    from YukkiMusic.core.userbot import assistants

    ran_assistant = random.choice(assistants)
    assistantdict[chat_id] = ran_assistant
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO assistants (chat_id, assistant_number) VALUES (?, ?)",
            (chat_id, ran_assistant)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting calls assistant for chat_id {chat_id}: {e}")
    finally:
        conn.close()

    return ran_assistant


async def group_assistant(self, chat_id: int) -> PyTgCalls:
    """
    Determines and returns the PyTgCalls instance for a given chat_id.
    """
    from YukkiMusic.core.userbot import assistants

    # 1. Check in-memory cache
    assistant_num = assistantdict.get(chat_id)
    
    if assistant_num:
        if assistant_num in assistants:
            # Found in cache and valid
            assis = assistant_num
        else:
            # Found in cache but invalid, set a new one
            assis = await set_calls_assistant(chat_id)
    else:
        # Not in cache, try database
        conn = get_db_connection()
        cursor = conn.cursor()
        db_assistant_num = None
        try:
            cursor.execute("SELECT assistant_number FROM assistants WHERE chat_id = ?", (chat_id,))
            db_record = cursor.fetchone()
            if db_record:
                db_assistant_num = db_record['assistant_number']
        except sqlite3.Error as e:
            print(f"Error fetching group assistant from DB for chat_id {chat_id}: {e}")
        finally:
            conn.close()

        if db_assistant_num:
            if db_assistant_num in assistants:
                # Found in DB and valid, add to cache
                assistantdict[chat_id] = db_assistant_num
                assis = db_assistant_num
            else:
                # Found in DB but invalid, set a new one
                assis = await set_calls_assistant(chat_id)
        else:
            # Not in DB, set a new one
            assis = await set_calls_assistant(chat_id)

    assistant_index = int(assis) - 1

    if 0 <= assistant_index < len(self.calls):
        return self.calls[assistant_index]
    else:
        raise ValueError(f"Assistant index {assistant_index + 1} is out of range. Please check your assistant configuration.")