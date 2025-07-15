import json # Import json for serialization
import sqlite3
from pytgcalls import types as _types

import config
from YukkiMusic.core.sqlite import get_db_connection # Import from your new sqlite.py

# No direct 'db' objects for MongoDB collections needed anymore.
# We'll interact with the DB via get_db_connection()

# Shifting to memory [ mongo sucks often] - These will remain in-memory
audio = {}
video = {}
loop = {}
playtype = {}
playmode = {}
channelconnect = {}
langm = {}
pause = {}
mute = {}
active = []
activevideo = []
command = [] # Command delete mode
cleanmode = [] # Clean mode
nonadmin = {} # Non-admin chat
vlimit = [] # Video stream limit (though this one is also fetched from DB)
maintenance = []
autoend = {}
greeting_message = {"welcome": {}, "goodbye": {}}


# --- Filters Database Operations ---
# Table: filters (chat_id INTEGER PRIMARY KEY, filters_data TEXT)

async def get_filters_count() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    chats_count = 0
    filters_count = 0
    try:
        # Assuming chat_id < 0 for group chats as per MongoDB query
        cursor.execute("SELECT chat_id, filters_data FROM filters WHERE chat_id < 0")
        chats = cursor.fetchall()
        chats_count = len(chats)
        for chat in chats:
            filters_data = json.loads(chat['filters_data'])
            filters_count += len(filters_data)
    except sqlite3.Error as e:
        print(f"Error getting filters count: {e}")
    finally:
        conn.close()
    return {
        "chats_count": chats_count,
        "filters_count": filters_count,
    }


async def _get_filters(chat_id: int) -> dict[str, int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    _filters = {}
    try:
        cursor.execute("SELECT filters_data FROM filters WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            _filters = json.loads(record['filters_data'])
    except sqlite3.Error as e:
        print(f"Error fetching filters for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    return _filters


async def get_filters_names(chat_id: int) -> list[str]:
    _filters = await _get_filters(chat_id)
    return list(_filters.keys())


async def get_filter(chat_id: int, name: str) -> bool | dict:
    name = name.lower().strip()
    _filters = await _get_filters(chat_id)
    return _filters.get(name, False)


async def save_filter(chat_id: int, name: str, _filter: dict):
    name = name.lower().strip()
    _filters = await _get_filters(chat_id)
    _filters[name] = _filter
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        filters_json = json.dumps(_filters)
        cursor.execute(
            "INSERT OR REPLACE INTO filters (chat_id, filters_data) VALUES (?, ?)",
            (chat_id, filters_json)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving filter for chat_id {chat_id}, name {name}: {e}")
    finally:
        conn.close()


async def delete_filter(chat_id: int, name: str) -> bool:
    filtersd = await _get_filters(chat_id)
    name = name.lower().strip()
    if name in filtersd:
        del filtersd[name]
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if filtersd: # If there are still filters, update the record
                filters_json = json.dumps(filtersd)
                cursor.execute(
                    "UPDATE filters SET filters_data = ? WHERE chat_id = ?",
                    (filters_json, chat_id)
                )
            else: # If no filters left, delete the record
                cursor.execute("DELETE FROM filters WHERE chat_id = ?", (chat_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting filter for chat_id {chat_id}, name {name}: {e}")
        finally:
            conn.close()
    return False


async def deleteall_filters(chat_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM filters WHERE chat_id = ?", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting all filters for chat_id {chat_id}: {e}")
    finally:
        conn.close()


# --- Notes Database Operations ---
# Table: notes (chat_id INTEGER PRIMARY KEY, notes_data TEXT, private_note BOOLEAN)

async def get_notes_count() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    chats_count = 0
    notes_count = 0
    try:
        cursor.execute("SELECT chat_id, notes_data FROM notes")
        chats = cursor.fetchall()
        chats_count = len(chats)
        for chat in chats:
            notes_data = json.loads(chat['notes_data'])
            notes_count += len(notes_data)
    except sqlite3.Error as e:
        print(f"Error getting notes count: {e}")
    finally:
        conn.close()
    return {"chats_count": chats_count, "notes_count": notes_count}


async def _get_notes(chat_id: int) -> dict[str, int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    _notes = {}
    try:
        cursor.execute("SELECT notes_data FROM notes WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            _notes = json.loads(record['notes_data'])
    except sqlite3.Error as e:
        print(f"Error fetching notes for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    return _notes


async def get_note_names(chat_id: int) -> list[str]:
    _notes = await _get_notes(chat_id)
    return list(_notes.keys())


async def get_note(chat_id: int, name: str) -> bool | dict:
    name = name.lower().strip()
    _notes = await _get_notes(chat_id)
    return _notes.get(name, False)


async def save_note(chat_id: int, name: str, note: dict):
    name = name.lower().strip()
    _notes = await _get_notes(chat_id)
    _notes[name] = note

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        notes_json = json.dumps(_notes)
        cursor.execute(
            "INSERT OR REPLACE INTO notes (chat_id, notes_data) VALUES (?, ?)",
            (chat_id, notes_json)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving note for chat_id {chat_id}, name {name}: {e}")
    finally:
        conn.close()


async def delete_note(chat_id: int, name: str) -> bool:
    notesd = await _get_notes(chat_id)
    name = name.lower().strip()
    if name in notesd:
        del notesd[name]
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if notesd: # If there are still notes, update the record
                notes_json = json.dumps(notesd)
                cursor.execute(
                    "UPDATE notes SET notes_data = ? WHERE chat_id = ?",
                    (notes_json, chat_id)
                )
            else: # If no notes left, delete the record
                cursor.execute("DELETE FROM notes WHERE chat_id = ?", (chat_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting note for chat_id {chat_id}, name {name}: {e}")
        finally:
            conn.close()
    return False


async def deleteall_notes(chat_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM notes WHERE chat_id = ?", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting all notes for chat_id {chat_id}: {e}")
    finally:
        conn.close()


async def set_private_note(chat_id: int, private_note: bool):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Notes can have private_note or notes_data or both.
        # Ensure we don't overwrite notes_data if it exists.
        cursor.execute(
            "INSERT INTO notes (chat_id, private_note) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET private_note = ?",
            (chat_id, private_note, private_note)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting private note for chat_id {chat_id}: {e}")
    finally:
        conn.close()


async def is_pnote_on(chat_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    private_note = False
    try:
        cursor.execute("SELECT private_note FROM notes WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record and record['private_note'] is not None:
            private_note = bool(record['private_note']) # SQLite stores bool as 0 or 1
    except sqlite3.Error as e:
        print(f"Error checking private note for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    return private_note


# --- Auto End Stream ---
# Table: autoend (chat_id INTEGER PRIMARY KEY)

async def is_autoend() -> bool:
    chat_id = 123 # Hardcoded chat_id as in original
    mode = autoend.get(chat_id)
    if mode is not None: # Check if it's already in the in-memory cache
        return mode
    
    conn = get_db_connection()
    cursor = conn.cursor()
    is_on_db = False
    try:
        cursor.execute("SELECT chat_id FROM autoend WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            is_on_db = True
    except sqlite3.Error as e:
        print(f"Error checking autoend from DB: {e}")
    finally:
        conn.close()
    
    autoend[chat_id] = is_on_db # Update in-memory cache
    return is_on_db


async def autoend_on():
    chat_id = 123 # Hardcoded chat_id as in original
    autoend[chat_id] = True
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO autoend (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error turning autoend on: {e}")
    finally:
        conn.close()


async def autoend_off():
    chat_id = 123 # Hardcoded chat_id as in original
    autoend[chat_id] = False
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM autoend WHERE chat_id = ?", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error turning autoend off: {e}")
    finally:
        conn.close()


# --- LOOP PLAY (In-Memory Only) ---
# This functionality seems to be purely in-memory in the original, so no DB changes.
async def get_loop(chat_id: int) -> int:
    return loop.get(chat_id, 0) # Default to 0 if not set

async def set_loop(chat_id: int, mode: int):
    loop[chat_id] = mode


# --- Channel Play IDS ---
# Table: channelplaymode (chat_id INTEGER PRIMARY KEY, mode INTEGER)

async def get_cmode(chat_id: int) -> int | None:
    mode = channelconnect.get(chat_id)
    if mode is not None:
        return mode
    
    conn = get_db_connection()
    cursor = conn.cursor()
    db_mode = None
    try:
        cursor.execute("SELECT mode FROM channelplaymode WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            db_mode = record['mode']
    except sqlite3.Error as e:
        print(f"Error fetching channel mode for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    
    if db_mode is not None:
        channelconnect[chat_id] = db_mode
    return db_mode


async def set_cmode(chat_id: int, mode: int):
    channelconnect[chat_id] = mode
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO channelplaymode (chat_id, mode) VALUES (?, ?)",
            (chat_id, mode)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting channel mode for chat_id {chat_id}: {e}")
    finally:
        conn.close()


# --- PLAY TYPE WHETHER ADMINS ONLY OR EVERYONE ---
# Table: playtype (chat_id INTEGER PRIMARY KEY, mode TEXT)

async def get_playtype(chat_id: int) -> str:
    mode = playtype.get(chat_id)
    if mode is not None:
        return mode
    
    conn = get_db_connection()
    cursor = conn.cursor()
    db_mode = "Everyone"
    try:
        cursor.execute("SELECT mode FROM playtype WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            db_mode = record['mode']
    except sqlite3.Error as e:
        print(f"Error fetching playtype for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    
    playtype[chat_id] = db_mode
    return db_mode


async def set_playtype(chat_id: int, mode: str):
    playtype[chat_id] = mode
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO playtype (chat_id, mode) VALUES (?, ?)",
            (chat_id, mode)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting playtype for chat_id {chat_id}: {e}")
    finally:
        conn.close()


# --- play mode whether inline or direct query ---
# Table: playmode (chat_id INTEGER PRIMARY KEY, mode TEXT)

async def get_playmode(chat_id: int) -> str:
    mode = playmode.get(chat_id)
    if mode is not None:
        return mode
    
    conn = get_db_connection()
    cursor = conn.cursor()
    db_mode = "Direct"
    try:
        cursor.execute("SELECT mode FROM playmode WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            db_mode = record['mode']
    except sqlite3.Error as e:
        print(f"Error fetching playmode for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    
    playmode[chat_id] = db_mode
    return db_mode


async def set_playmode(chat_id: int, mode: str):
    playmode[chat_id] = mode
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO playmode (chat_id, mode) VALUES (?, ?)",
            (chat_id, mode)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting playmode for chat_id {chat_id}: {e}")
    finally:
        conn.close()


# --- language ---
# Table: language (chat_id INTEGER PRIMARY KEY, lang TEXT)

async def get_lang(chat_id: int) -> str:
    mode = langm.get(chat_id)
    if mode is not None:
        return mode
    
    conn = get_db_connection()
    cursor = conn.cursor()
    db_lang = "en"
    try:
        cursor.execute("SELECT lang FROM language WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            db_lang = record['lang']
    except sqlite3.Error as e:
        print(f"Error fetching language for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    
    langm[chat_id] = db_lang
    return db_lang


async def set_lang(chat_id: int, lang: str):
    langm[chat_id] = lang
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO language (chat_id, lang) VALUES (?, ?)",
            (chat_id, lang)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting language for chat_id {chat_id}: {e}")
    finally:
        conn.close()


# --- Muted (In-Memory Only) ---
async def is_muted(chat_id: int) -> bool:
    return mute.get(chat_id, False) # Default to False

async def mute_on(chat_id: int):
    mute[chat_id] = True

async def mute_off(chat_id: int):
    mute[chat_id] = False


# --- Pause-Skip (In-Memory Only) ---
async def is_music_playing(chat_id: int) -> bool:
    return pause.get(chat_id, False) # Default to False

async def music_on(chat_id: int):
    pause[chat_id] = True

async def music_off(chat_id: int):
    pause[chat_id] = False


# --- Active Voice Chats (In-Memory Only) ---
async def get_active_chats() -> list:
    return active

async def is_active_chat(chat_id: int) -> bool:
    return chat_id in active

async def add_active_chat(chat_id: int):
    if chat_id not in active:
        active.append(chat_id)

async def remove_active_chat(chat_id: int):
    if chat_id in active:
        active.remove(chat_id)


# --- Active Video Chats (In-Memory Only) ---
async def get_active_video_chats() -> list:
    return activevideo

async def is_active_video_chat(chat_id: int) -> bool:
    return chat_id in activevideo

async def add_active_video_chat(chat_id: int):
    if chat_id not in activevideo:
        activevideo.append(chat_id)

async def remove_active_video_chat(chat_id: int):
    if chat_id in activevideo:
        activevideo.remove(chat_id)


# --- Delete command mode (In-Memory Only) ---
# (Note: Original cleanmode and command seem to use lists as inverted logic,
# meaning if chat_id IS NOT in list, then it's ON. This is preserved.)

async def is_cleanmode_on(chat_id: int) -> bool:
    return chat_id not in cleanmode

async def cleanmode_off(chat_id: int):
    if chat_id not in cleanmode:
        cleanmode.append(chat_id)

async def cleanmode_on(chat_id: int):
    if chat_id in cleanmode:
        cleanmode.remove(chat_id)


async def is_commanddelete_on(chat_id: int) -> bool:
    return chat_id not in command

async def commanddelete_off(chat_id: int):
    if chat_id not in command:
        command.append(chat_id)

async def commanddelete_on(chat_id: int):
    if chat_id in command:
        command.remove(chat_id)


# --- Non Admin Chat ---
# Table: adminauth (chat_id INTEGER PRIMARY KEY)

async def check_nonadmin_chat(chat_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    is_nonadmin = False
    try:
        cursor.execute("SELECT chat_id FROM adminauth WHERE chat_id = ?", (chat_id,))
        record = cursor.fetchone()
        if record:
            is_nonadmin = True
    except sqlite3.Error as e:
        print(f"Error checking nonadmin chat from DB for chat_id {chat_id}: {e}")
    finally:
        conn.close()
    return is_nonadmin


async def is_nonadmin_chat(chat_id: int) -> bool:
    mode = nonadmin.get(chat_id)
    if mode is not None:
        return mode
    
    is_nonadmin_db = await check_nonadmin_chat(chat_id) # Call the DB function
    nonadmin[chat_id] = is_nonadmin_db # Update in-memory cache
    return is_nonadmin_db


async def add_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = True
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO adminauth (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding nonadmin chat for chat_id {chat_id}: {e}")
    finally:
        conn.close()


async def remove_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = False
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM adminauth WHERE chat_id = ?", (chat_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error removing nonadmin chat for chat_id {chat_id}: {e}")
    finally:
        conn.close()


# --- Video Limit ---
# Table: videocalls (chat_id INTEGER PRIMARY KEY, limit_val INTEGER)

async def is_video_allowed(chat_idd: int) -> bool: # Renamed parameter for clarity
    chat_id = 123456 # Hardcoded chat_id as in original
    
    # Try to get limit from in-memory cache first
    limit = vlimit[0] if vlimit else None
    if limit is None: # If not in cache, fetch from DB
        conn = get_db_connection()
        cursor = conn.cursor()
        db_limit = config.VIDEO_STREAM_LIMIT # Default from config
        try:
            cursor.execute("SELECT limit_val FROM videocalls WHERE chat_id = ?", (chat_id,))
            record = cursor.fetchone()
            if record:
                db_limit = record['limit_val']
        except sqlite3.Error as e:
            print(f"Error fetching video limit from DB: {e}")
        finally:
            conn.close()
        
        vlimit.clear()
        vlimit.append(db_limit)
        limit = db_limit
    
    if limit == 0:
        return False
    
    count = len(await get_active_video_chats())
    if int(count) == int(limit):
        if not await is_active_video_chat(chat_idd):
            return False
    return True


async def get_video_limit() -> int: # Changed return type to int
    chat_id = 123456 # Hardcoded chat_id as in original
    
    limit = vlimit[0] if vlimit else None
    if limit is None:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_limit = config.VIDEO_STREAM_LIMIT
        try:
            cursor.execute("SELECT limit_val FROM videocalls WHERE chat_id = ?", (chat_id,))
            record = cursor.fetchone()
            if record:
                db_limit = record['limit_val']
        except sqlite3.Error as e:
            print(f"Error fetching video limit from DB for get_video_limit: {e}")
        finally:
            conn.close()
        vlimit.clear()
        vlimit.append(db_limit)
        limit = db_limit
    return limit


async def set_video_limit(limt: int):
    chat_id = 123456 # Hardcoded chat_id as in original
    vlimit.clear()
    vlimit.append(limt)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO videocalls (chat_id, limit_val) VALUES (?, ?)",
            (chat_id, limt)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error setting video limit: {e}")
    finally:
        conn.close()


# --- On Off ---
# Table: onoff (setting_key INTEGER PRIMARY KEY)

async def is_on_off(on_off_key: int) -> bool: # Renamed parameter for clarity
    conn = get_db_connection()
    cursor = conn.cursor()
    is_on = False
    try:
        cursor.execute("SELECT setting_key FROM onoff WHERE setting_key = ?", (on_off_key,))
        record = cursor.fetchone()
        if record:
            is_on = True
    except sqlite3.Error as e:
        print(f"Error checking on/off status for key {on_off_key}: {e}")
    finally:
        conn.close()
    return is_on


async def add_on(on_off_key: int):
    is_on = await is_on_off(on_off_key)
    if is_on:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO onoff (setting_key) VALUES (?)", (on_off_key,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding on status for key {on_off_key}: {e}")
    finally:
        conn.close()


async def add_off(on_off_key: int):
    is_off = await is_on_off(on_off_key)
    if not is_off:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM onoff WHERE setting_key = ?", (on_off_key,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding off status for key {on_off_key}: {e}")
    finally:
        conn.close()


# --- Maintenance ---
# This uses the same 'onoff' table, with key 1 representing maintenance.

async def is_maintenance() -> bool:
    if maintenance: # Check in-memory cache first
        if 1 in maintenance: # 1 means maintenance ON in cache
            return False # Not in maintenance
        else: # 2 means maintenance OFF in cache
            return True # In maintenance
    
    # If not in cache, fetch from DB using is_on_off
    is_on_db = await is_on_off(1) # Key 1 signifies maintenance status
    if not is_on_db: # If key 1 is NOT in onoff table, means maintenance is OFF
        maintenance.clear()
        maintenance.append(2) # Cache: 2 means maintenance OFF
        return True # Return True because is_maintenance() means "is it in maintenance mode"
    else: # If key 1 IS in onoff table, means maintenance is ON
        maintenance.clear()
        maintenance.append(1) # Cache: 1 means maintenance ON
        return False # Return False because not "in maintenance mode"

async def maintenance_off():
    maintenance.clear()
    maintenance.append(2) # Cache: 2 means maintenance OFF
    await add_off(1) # Remove key 1 from onoff table (means maintenance OFF)

async def maintenance_on():
    maintenance.clear()
    maintenance.append(1) # Cache: 1 means maintenance ON
    await add_on(1) # Add key 1 to onoff table (means maintenance ON)


# --- Bitrate settings (In-Memory Only) ---
async def save_audio_bitrate(chat_id: int, bitrate: str):
    audio[chat_id] = bitrate

async def save_video_bitrate(chat_id: int, bitrate: str):
    video[chat_id] = bitrate

async def get_aud_bit_name(chat_id: int) -> str:
    return audio.get(chat_id, "STUDIO")

async def get_vid_bit_name(chat_id: int) -> str:
    return video.get(chat_id, "UHD_4K")

async def get_audio_bitrate(chat_id: int) -> str:
    mode = audio.get(chat_id, "STUDIO")
    return {
        "STUDIO": _types.AudioQuality.STUDIO,
        "HIGH": _types.AudioQuality.HIGH,
        "MEDIUM": _types.AudioQuality.MEDIUM,
        "LOW": _types.AudioQuality.LOW,
    }.get(mode, _types.AudioQuality.STUDIO)

async def get_video_bitrate(chat_id: int) -> str:
    mode = video.get(chat_id, "UHD_4K")
    return {
        "UHD_4K": _types.VideoQuality.UHD_4K,
        "QHD_2K": _types.VideoQuality.QHD_2K,
        "FHD_1080p": _types.VideoQuality.FHD_1080p,
        "HD_720p": _types.VideoQuality.HD_720p,
        "SD_480p": _types.VideoQuality.SD_480p,
        "SD_360p": _types.VideoQuality.SD_360p,
    }.get(mode, _types.VideoQuality.UHD_4K)