import json # Import json for serialization
import sqlite3

from YukkiMusic.core.sqlite import get_db_connection # Import from your new sqlite.py

# No direct 'db' objects for MongoDB collections needed anymore.
# We'll interact with the DB via get_db_connection()

playlist = [] # This appears to be an in-memory list, not directly database-backed.

# --- Playlists Operations ---
# Table: playlists (chat_id INTEGER PRIMARY KEY, notes_data TEXT)
# Using 'notes_data' to maintain consistency with the original MongoDB structure's key for data.


async def _get_playlists(chat_id: int) -> dict[str, dict]: # Changed return type hint
    conn = get_db_connection()
    cursor = conn.cursor()
    _playlists = {}
    try:
        cursor.execute("SELECT notes_data FROM playlists WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record and record['notes_data']:
            _playlists = json.loads(record['notes_data'])
    except sqlite3.Error as e:
        print(f"Error fetching playlists for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    return _playlists


async def get_playlist_names(chat_id: int) -> list[str]:
    _playlists = await _get_playlists(chat_id)
    return list(_playlists.keys())


async def get_playlist(chat_id: int, name: str) -> bool | dict:
    # name is used directly, not lowercased/stripped in original for playlist.
    _playlists = await _get_playlists(chat_id)
    return _playlists.get(name, False)


async def save_playlist(chat_id: int, name: str, note: dict):
    # name is used directly
    _playlists = await _get_playlists(chat_id)
    _playlists[name] = note

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        playlists_json = json.dumps(_playlists)
        cursor.execute(
            "INSERT OR REPLACE INTO playlists (chat_id, notes_data) VALUES (?, ?)",
            (chat_id, playlists_json)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving playlist for chat_id {chat_id}, name {name}: {e}")
    finally:
        conn.close()


async def delete_playlist(chat_id: int, name: str) -> bool:
    playlistsd = await _get_playlists(chat_id)
    # name is used directly
    if name in playlistsd:
        del playlistsd[name]
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if playlistsd:
                playlists_json = json.dumps(playlistsd)
                cursor.execute(
                    "UPDATE playlists SET notes_data = ? WHERE chat_id = ?",
                    (playlists_json, chat_id)
                )
            else:
                cursor.execute("DELETE FROM playlists WHERE chat_id = ?", (chat_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting playlist for chat_id {chat_id}, name {name}: {e}")
        finally:
            conn.close()
    return False


# --- Users Operations (tgusersdb) ---
# Table: served_users (user_id INTEGER PRIMARY KEY)

async def is_served_user(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    is_served = False
    try:
        cursor.execute("SELECT user_id FROM served_users WHERE user_id = ?", (user_id,))
        record = cursor.fetchone()
        if record:
            is_served = True
    except sqlite3.Error as e:
        print(f"Error checking served user {user_id}: {e}")
    finally:
        conn.close()
    return is_served


async def get_served_users() -> list[dict]: # Changed return type hint
    conn = get_db_connection()
    cursor = conn.cursor()
    users_list = []
    try:
        cursor.execute("SELECT user_id FROM served_users WHERE user_id > 0") # MongoDB equivalent of $gt 0
        records = cursor.fetchall()
        for record in records:
            users_list.append({"user_id": record['user_id']}) # Mimic original output structure
    except sqlite3.Error as e:
        print(f"Error getting served users: {e}")
    finally:
        conn.close()
    return users_list


async def add_served_user(user_id: int):
    is_served = await is_served_user(user_id)
    if is_served:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO served_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding served user {user_id}: {e}")
    finally:
        conn.close()


async def delete_served_user(user_id: int):
    # The original logic deletes even if not served, which is fine for SQLite.
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM served_users WHERE user_id = ?", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting served user {user_id}: {e}")
    finally:
        conn.close()


# --- Served Chats Operations (chatsdb) ---
# Table: served_chats (chat_id INTEGER PRIMARY KEY)

async def get_served_chats() -> list[dict]: # Changed return type hint
    conn = get_db_connection()
    cursor = conn.cursor()
    chats_list = []
    try:
        cursor.execute("SELECT chat_id FROM served_chats WHERE chat_id < 0") # MongoDB equivalent of $lt 0
        records = cursor.fetchall()
        for record in records:
            chats_list.append({"chat_id": record['chat_id']}) # Mimic original output structure
    except sqlite3.Error as e:
        print(f"Error getting served chats: {e}")
    finally:
        conn.close()
    return chats_list


async def is_served_chat(chat_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    is_served = False
    try:
        cursor.execute("SELECT chat_id FROM served_chats WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            is_served = True
    except sqlite3.Error as e:
        print(f"Error checking served chat {chat_id}: {e}")
    finally:
        conn.close()
    return is_served


async def add_served_chat(chat_id: int):
    is_served = await is_served_chat(chat_id)
    if is_served:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO served_chats (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding served chat {chat_id}: {e}")
    finally:
        conn.close()


async def delete_served_chat(chat_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM served_chats WHERE chat_id = ?", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting served chat {chat_id}: {e}")
    finally:
        conn.close()


# --- Blacklisted Chats Operations ---
# Table: blacklisted_chats (chat_id INTEGER PRIMARY KEY)

async def blacklisted_chats() -> list[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    chats_list = []
    try:
        cursor.execute("SELECT chat_id FROM blacklisted_chats WHERE chat_id < 0")
        records = cursor.fetchall()
        for record in records:
            chats_list.append(record['chat_id'])
    except sqlite3.Error as e:
        print(f"Error getting blacklisted chats: {e}")
    finally:
        conn.close()
    return chats_list


async def blacklist_chat(chat_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT chat_id FROM blacklisted_chats WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if not record:
            cursor.execute("INSERT INTO blacklisted_chats (chat_id) VALUES (?)", (chat_id,))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        print(f"Error blacklisting chat {chat_id}: {e}")
        return False
    finally:
        conn.close()


async def whitelist_chat(chat_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT chat_id FROM blacklisted_chats WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            cursor.execute("DELETE FROM blacklisted_chats WHERE chat_id = ?", (chat_id,))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        print(f"Error whitelisting chat {chat_id}: {e}")
        return False
    finally:
        conn.close()


# --- Private Served Chats Operations ---
# Table: private_chats (chat_id INTEGER PRIMARY KEY)

async def get_private_served_chats() -> list[dict]: # Changed return type hint
    conn = get_db_connection()
    cursor = conn.cursor()
    chats_list = []
    try:
        cursor.execute("SELECT chat_id FROM private_chats WHERE chat_id < 0")
        records = cursor.fetchall()
        for record in records:
            chats_list.append({"chat_id": record['chat_id']})
    except sqlite3.Error as e:
        print(f"Error getting private served chats: {e}")
    finally:
        conn.close()
    return chats_list


async def is_served_private_chat(chat_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    is_served = False
    try:
        cursor.execute("SELECT chat_id FROM private_chats WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            is_served = True
    except sqlite3.Error as e:
        print(f"Error checking private served chat {chat_id}: {e}")
    finally:
        conn.close()
    return is_served


async def add_private_chat(chat_id: int):
    is_served = await is_served_private_chat(chat_id)
    if is_served:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO private_chats (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding private chat {chat_id}: {e}")
    finally:
        conn.close()


async def remove_private_chat(chat_id: int):
    is_served = await is_served_private_chat(chat_id)
    if not is_served:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM private_chats WHERE chat_id = ?", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error removing private chat {chat_id}: {e}")
    finally:
        conn.close()


# --- Auth Users DB Operations ---
# Table: auth_users (chat_id INTEGER PRIMARY KEY, notes_data TEXT)

async def _get_authusers(chat_id: int) -> dict[str, dict]: # Changed return type hint
    conn = get_db_connection()
    cursor = conn.cursor()
    _authusers = {}
    try:
        cursor.execute("SELECT notes_data FROM auth_users WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record and record['notes_data']:
            _authusers = json.loads(record['notes_data'])
    except sqlite3.Error as e:
        print(f"Error fetching authusers for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    return _authusers


async def get_authuser_names(chat_id: int) -> list[str]:
    _authusers = await _get_authusers(chat_id)
    return list(_authusers.keys())


async def get_authuser(chat_id: int, name: str) -> bool | dict:
    # name is used directly
    _authusers = await _get_authusers(chat_id)
    return _authusers.get(name, False)


async def save_authuser(chat_id: int, name: str, note: dict):
    # name is used directly
    _authusers = await _get_authusers(chat_id)
    _authusers[name] = note

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        authusers_json = json.dumps(_authusers)
        cursor.execute(
            "INSERT OR REPLACE INTO auth_users (chat_id, notes_data) VALUES (?, ?)",
            (chat_id, authusers_json)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving authuser for chat_id {chat_id}, name {name}: {e}")
    finally:
        conn.close()


async def delete_authuser(chat_id: int, name: str) -> bool:
    authusersd = await _get_authusers(chat_id)
    # name is used directly
    if name in authusersd:
        del authusersd[name]
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if authusersd:
                authusers_json = json.dumps(authusersd)
                cursor.execute(
                    "UPDATE auth_users SET notes_data = ? WHERE chat_id = ?",
                    (authusers_json, chat_id)
                )
            else:
                cursor.execute("DELETE FROM auth_users WHERE chat_id = ?", (chat_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting authuser for chat_id {chat_id}, name {name}: {e}")
        finally:
            conn.close()
    return False


# --- Global Bans Operations (gbansdb) ---
# Table: gbanned_users (user_id INTEGER PRIMARY KEY)

async def get_gbanned() -> list[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute("SELECT user_id FROM gbanned_users WHERE user_id > 0")
        records = cursor.fetchall()
        for record in records:
            results.append(record['user_id'])
    except sqlite3.Error as e:
        print(f"Error getting gbanned users: {e}")
    finally:
        conn.close()
    return results


async def is_gbanned_user(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    is_gbanned = False
    try:
        cursor.execute("SELECT user_id FROM gbanned_users WHERE user_id = ?", (user_id,))
        record = cursor.fetchone()
        if record:
            is_gbanned = True
    except sqlite3.Error as e:
        print(f"Error checking gban for user {user_id}: {e}")
    finally:
        conn.close()
    return is_gbanned


async def add_gban_user(user_id: int):
    is_gbanned = await is_gbanned_user(user_id)
    if is_gbanned:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO gbanned_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding gban for user {user_id}: {e}")
    finally:
        conn.close()


async def remove_gban_user(user_id: int):
    is_gbanned = await is_gbanned_user(user_id)
    if not is_gbanned:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM gbanned_users WHERE user_id = ?", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error removing gban for user {user_id}: {e}")
    finally:
        conn.close()


# --- Sudoers Operations ---
# Table: sudoers (key TEXT PRIMARY KEY, user_ids TEXT) - 'key' will be 'sudo'

async def get_sudoers() -> list[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    sudoers_list = []
    try:
        cursor.execute("SELECT user_ids FROM sudoers WHERE key = 'sudo'")
        record = cursor.fetchone()
        if record and record['user_ids']:
            sudoers_list = json.loads(record['user_ids'])
    except sqlite3.Error as e:
        print(f"Error fetching sudoers: {e}")
    finally:
        conn.close()
    return sudoers_list


async def add_sudo(user_id: int) -> bool:
    sudoers_list = await get_sudoers()
    if user_id in sudoers_list: # Check if already sudo
        return False
    sudoers_list.append(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sudoers_json = json.dumps(sudoers_list)
        cursor.execute(
            "INSERT OR REPLACE INTO sudoers (key, user_ids) VALUES (?, ?)",
            ('sudo', sudoers_json)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding sudo user {user_id}: {e}")
        return False
    finally:
        conn.close()


async def remove_sudo(user_id: int) -> bool:
    sudoers_list = await get_sudoers()
    if user_id not in sudoers_list: # Check if not sudo
        return False
    sudoers_list.remove(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sudoers_json = json.dumps(sudoers_list)
        cursor.execute(
            "INSERT OR REPLACE INTO sudoers (key, user_ids) VALUES (?, ?)",
            ('sudo', sudoers_json)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error removing sudo user {user_id}: {e}")
        return False
    finally:
        conn.close()


# --- Total Queries on bot ---
# Table: queries (chat_id INTEGER PRIMARY KEY, mode INTEGER) - 'chat_id' is hardcoded 98324

async def get_queries() -> int:
    chat_id = 98324
    conn = get_db_connection()
    cursor = conn.cursor()
    queries_count = 0
    try:
        cursor.execute("SELECT mode FROM queries WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            queries_count = record['mode']
    except sqlite3.Error as e:
        print(f"Error fetching queries count: {e}")
    finally:
        conn.close()
    return queries_count


async def set_queries(mode: int):
    chat_id = 98324
    current_queries = await get_queries() # Get current value via the new function
    new_mode = current_queries + mode # Add to current value
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO queries (chat_id, mode) VALUES (?, ?)",
            (chat_id, new_mode)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting queries count: {e}")
    finally:
        conn.close()


# --- Top Chats DB Operations ---
# Table: chat_tops (chat_id INTEGER PRIMARY KEY, vidid_data TEXT)
# 'vidid_data' will store the JSON string of the dictionary 'vidid'

async def get_top_chats() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    results = {}
    try:
        cursor.execute("SELECT chat_id, vidid_data FROM chat_tops WHERE chat_id < 0")
        records = cursor.fetchall()
        for record in records:
            chat_id = record['chat_id']
            vidid_data = json.loads(record['vidid_data'])
            total = 0
            for i in vidid_data:
                counts_ = vidid_data[i].get("spot", 0) # Use .get for safety
                if counts_ > 0:
                    total += counts_
            if total > 0: # Only add if total is meaningful
                results[chat_id] = total
    except sqlite3.Error as e:
        print(f"Error getting top chats: {e}")
    finally:
        conn.close()
    return results


async def get_global_tops() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    results = {}
    try:
        cursor.execute("SELECT vidid_data FROM chat_tops WHERE chat_id < 0")
        records = cursor.fetchall()
        for record in records:
            vidid_data = json.loads(record['vidid_data'])
            for i in vidid_data:
                counts_ = vidid_data[i].get("spot", 0)
                title_ = vidid_data[i].get("title") # Use .get for safety
                if counts_ > 0 and title_:
                    if i not in results:
                        results[i] = {"spot": counts_, "title": title_}
                    else:
                        spot = results[i]["spot"]
                        count_ = spot + counts_
                        results[i]["spot"] = count_
    except sqlite3.Error as e:
        print(f"Error getting global tops: {e}")
    finally:
        conn.close()
    return results


async def get_particulars(chat_id: int) -> dict[str, dict]: # Changed return type hint
    conn = get_db_connection()
    cursor = conn.cursor()
    ids = {}
    try:
        cursor.execute("SELECT vidid_data FROM chat_tops WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record and record['vidid_data']:
            ids = json.loads(record['vidid_data'])
    except sqlite3.Error as e:
        print(f"Error fetching particulars for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    return ids


async def get_particular_top(chat_id: int, name: str) -> bool | dict:
    ids = await get_particulars(chat_id)
    return ids.get(name, False) # Using .get for consistency and safety


async def update_particular_top(chat_id: int, name: str, vidid: dict):
    ids = await get_particulars(chat_id)
    ids[name] = vidid # Update the specific video ID's data
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        vidid_json = json.dumps(ids)
        cursor.execute(
            "INSERT OR REPLACE INTO chat_tops (chat_id, vidid_data) VALUES (?, ?)",
            (chat_id, vidid_json)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating particular top for chat_id {chat_id}, name {name}: {e}")
    finally:
        conn.close()


# --- Top User DB Operations ---
# Table: user_tops (chat_id INTEGER PRIMARY KEY, vidid_data TEXT)
# Original used 'chat_id' for 'user_id' but queried for "$gt 0". Will rename table to user_tops
# and use 'user_id' for clarity in SQLite table.

async def get_userss(user_id: int) -> dict[str, dict]: # Renamed parameter and type hint
    conn = get_db_connection()
    cursor = conn.cursor()
    ids = {}
    try:
        cursor.execute("SELECT vidid_data FROM user_tops WHERE user_id = ?", (user_id,))
        record = cursor.fetchone()
        if record and record['vidid_data']:
            ids = json.loads(record['vidid_data'])
    except sqlite3.Error as e:
        print(f"Error fetching users data for user_id {user_id}: {e}")
    finally:
        conn.close()
    return ids


async def delete_userss(user_id: int) -> bool: # Renamed parameter
    conn = get_db_connection()
    cursor = conn.cursor()
    rows_deleted = 0
    try:
        cursor.execute("DELETE FROM user_tops WHERE user_id = ?", (user_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
    except sqlite3.Error as e:
        print(f"Error deleting users data for user_id {user_id}: {e}")
    finally:
        conn.close()
    return rows_deleted > 0


async def get_user_top(user_id: int, name: str) -> bool | dict: # Renamed parameter
    ids = await get_userss(user_id)
    return ids.get(name, False)


async def update_user_top(user_id: int, name: str, vidid: dict): # Renamed parameter
    ids = await get_userss(user_id)
    ids[name] = vidid
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        vidid_json = json.dumps(ids)
        cursor.execute(
            "INSERT OR REPLACE INTO user_tops (user_id, vidid_data) VALUES (?, ?)",
            (user_id, vidid_json)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating user top for user_id {user_id}, name {name}: {e}")
    finally:
        conn.close()


async def get_topp_users() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    results = {}
    try:
        cursor.execute("SELECT user_id, vidid_data FROM user_tops WHERE user_id > 0")
        records = cursor.fetchall()
        for record in records:
            user_id = record['user_id']
            vidid_data = json.loads(record['vidid_data'])
            total = 0
            for i in vidid_data:
                counts_ = vidid_data[i].get("spot", 0)
                if counts_ > 0:
                    total += counts_
            if total > 0:
                results[user_id] = total
    except sqlite3.Error as e:
        print(f"Error getting top users: {e}")
    finally:
        conn.close()
    return results


# --- Gban Users (from blockeddb - global block) ---
# Note: The original had 'gbansdb' and 'blockeddb'. 'gbansdb' was used for get/add/remove_gban_user,
# while 'blockeddb' was used for get_banned_users/count, is_banned_user, add/remove_banned_user.
# I will assume 'blockeddb' is for "globally blocked" in the context of user interaction,
# and 'gbansdb' was a distinct global ban which I've mapped to 'gbanned_users'.
# Let's keep 'blockeddb' as a separate table for "banned users".
# Table: banned_users (user_id INTEGER PRIMARY KEY)

async def get_banned_users() -> list[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute("SELECT user_id FROM banned_users WHERE user_id > 0")
        records = cursor.fetchall()
        for record in records:
            results.append(record['user_id'])
    except sqlite3.Error as e:
        print(f"Error getting banned users: {e}")
    finally:
        conn.close()
    return results


async def get_banned_count() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    try:
        cursor.execute("SELECT COUNT(user_id) FROM banned_users WHERE user_id > 0")
        record = cursor.fetchone()
        if record:
            count = record[0] # COUNT returns a single value in the first column
    except sqlite3.Error as e:
        print(f"Error getting banned count: {e}")
    finally:
        conn.close()
    return count


async def is_banned_user(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    is_banned = False
    try:
        cursor.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
        record = cursor.fetchone()
        if record:
            is_banned = True
    except sqlite3.Error as e:
        print(f"Error checking banned user {user_id}: {e}")
    finally:
        conn.close()
    return is_banned


async def add_banned_user(user_id: int):
    is_banned = await is_banned_user(user_id)
    if is_banned:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding banned user {user_id}: {e}")
    finally:
        conn.close()


async def remove_banned_user(user_id: int):
    is_banned = await is_banned_user(user_id)
    if not is_banned:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error removing banned user {user_id}: {e}")
    finally:
        conn.close()