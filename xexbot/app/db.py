import sqlite3
import os
import logging

DB_FILE = "xexbot.db"
logger = logging.getLogger(__name__)

def get_db_connection():
    """Gets a database connection."""
    return sqlite3.connect(DB_FILE)

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    if os.path.exists(DB_FILE):
        logger.info("Database already exists.")
        return

    logger.info("Initializing new database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for conversation history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tweet_id INTEGER NOT NULL UNIQUE,
        author_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table for research cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS research_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL UNIQUE,
        result TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table for application state (e.g., last processed mention ID)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_state (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def get_last_mention_id() -> int | None:
    """Retrieves the ID of the most recently processed mention."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_state WHERE key = 'last_mention_id'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return int(row[0])
    return None

def set_last_mention_id(mention_id: int):
    """Saves the ID of the most recently processed mention."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
        ('last_mention_id', str(mention_id))
    )
    conn.commit()
    conn.close()
    logger.info(f"Updated last_mention_id to {mention_id}")

if __name__ == "__main__":
    init_db()