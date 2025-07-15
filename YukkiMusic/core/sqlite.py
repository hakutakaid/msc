# YukkiMusic/core/sqlite.py

import logging
import sqlite3
import sys
import os

import config # Assuming this import is correct and needed

LOGGER = logging.getLogger(__name__)
DB_FILE = "yukki.db"

def init_db():
    """Initializes the SQLite database and creates necessary tables."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # --- Tables previously added for general bot functionality ---
        # Table for users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                join_date TEXT
            )
        ''')

        # Table for assistants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assistants (
                chat_id INTEGER PRIMARY KEY,
                assistant_number INTEGER NOT NULL
            )
        ''')

        # --- Tables for memorydatabase.py conversion ---
        # Table for filters
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filters (
                chat_id INTEGER PRIMARY KEY,
                filters_data TEXT -- Stores JSON string of filters
            )
        ''')

        # Table for notes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                chat_id INTEGER PRIMARY KEY,
                notes_data TEXT DEFAULT '{}', -- Stores JSON string of notes
                private_note BOOLEAN DEFAULT 0 -- 0 for False, 1 for True
            )
        ''')

        # Table for autoend
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS autoend (
                chat_id INTEGER PRIMARY KEY
            )
        ''')
        
        # Table for channelplaymode
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channelplaymode (
                chat_id INTEGER PRIMARY KEY,
                mode INTEGER NOT NULL
            )
        ''')

        # Table for playtype
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playtype (
                chat_id INTEGER PRIMARY KEY,
                mode TEXT NOT NULL -- "Everyone" or "Admins"
            )
        ''')

        # Table for playmode
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playmode (
                chat_id INTEGER PRIMARY KEY,
                mode TEXT NOT NULL -- "Direct" or "Inline"
            )
        ''')

        # Table for language
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS language (
                chat_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL -- e.g., "en", "id"
            )
        ''')

        # Table for adminauth (nonadmin chats)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adminauth (
                chat_id INTEGER PRIMARY KEY
            )
        ''')

        # Table for videocalls (video stream limit)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videocalls (
                chat_id INTEGER PRIMARY KEY,
                limit_val INTEGER NOT NULL
            )
        ''')

        # Table for onoff (general on/off settings, like maintenance)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS onoff (
                setting_key INTEGER PRIMARY KEY -- e.g., 1 for maintenance
            )
        ''')

        # --- Tables for mongodatabase.py conversion ---
        # Table for playlists (from playlistdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                chat_id INTEGER PRIMARY KEY,
                notes_data TEXT DEFAULT '{}' -- Stores JSON string of playlist items
            )
        ''')

        # Table for served_users (from usersdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS served_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')

        # Table for served_chats (from chatsdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS served_chats (
                chat_id INTEGER PRIMARY KEY
            )
        ''')

        # Table for blacklisted_chats (from blacklist_chatdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklisted_chats (
                chat_id INTEGER PRIMARY KEY
            )
        ''')

        # Table for private_chats (from privatedb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS private_chats (
                chat_id INTEGER PRIMARY KEY
            )
        ''')

        # Table for auth_users (from authuserdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_users (
                chat_id INTEGER PRIMARY KEY,
                notes_data TEXT DEFAULT '{}' -- Stores JSON string of auth users
            )
        ''')

        # Table for gbanned_users (from gbansdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gbanned_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')

        # Table for sudoers (from sudoersdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sudoers (
                key TEXT PRIMARY KEY, -- Will be 'sudo'
                user_ids TEXT DEFAULT '[]' -- Stores JSON string of list of user_ids
            )
        ''')

        # Table for queries (from queriesdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                chat_id INTEGER PRIMARY KEY, -- Will be hardcoded 98324
                mode INTEGER NOT NULL DEFAULT 0
            )
        ''')

        # Table for chat_tops (from chattopdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_tops (
                chat_id INTEGER PRIMARY KEY,
                vidid_data TEXT DEFAULT '{}' -- Stores JSON string of video IDs and their spots/titles
            )
        ''')

        # Table for user_tops (from userdb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_tops (
                user_id INTEGER PRIMARY KEY,
                vidid_data TEXT DEFAULT '{}' -- Stores JSON string of video IDs and user spots
            )
        ''')

        # Table for banned_users (from blockeddb)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY
            )
        ''')

        conn.commit()
        conn.close()
        LOGGER.info(f"SQLite database '{DB_FILE}' initialized successfully.")
    except sqlite3.Error as e:
        LOGGER.error(f"Error initializing SQLite database: {e}")
        sys.exit(1)

def get_db_connection():
    """Returns a connection object to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # This allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        LOGGER.error(f"Error connecting to SQLite database: {e}")
        sys.exit(1)

# Ensure the database is initialized when this module is imported
# This will create the database file and tables if they don't exist
if not os.path.exists(DB_FILE):
    LOGGER.info(f"SQLite database file '{DB_FILE}' not found. Initializing...")
    init_db()