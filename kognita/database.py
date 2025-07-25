# kognita/database.py
import sqlite3
import os
import logging
from pathlib import Path

# Proje kök dizinini belirle ve veritabanı dosyasını orada oluştur.
PROJECT_ROOT = Path(__file__).parent.parent
DB_FILE = PROJECT_ROOT / "kognita_data.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        # DB_FILE yoksa, connect onu oluşturacaktır.
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def _populate_initial_categories(conn):
    """Populates the database with a default set of application categories."""
    categories = {
        "winword.exe": "Office", "excel.exe": "Office", "powerpnt.exe": "Office",
        "outlook.exe": "Communication", "slack.exe": "Communication", "teams.exe": "Communication",
        "code.exe": "Development", "pycharm64.exe": "Development", "devenv.exe": "Development", "sublime_text.exe": "Development",
        "explorer.exe": "System", "cmd.exe": "System", "powershell.exe": "System", "taskmgr.exe": "System",
        "photoshop.exe": "Design", "illustrator.exe": "Design", "figma.exe": "Design",
        "adobe premiere pro.exe": "Video", "afterfx.exe": "Video",
        "vlc.exe": "Media", "spotify.exe": "Music",
        "chrome.exe": "Web", "firefox.exe": "Web", "msedge.exe": "Web",
        "discord.exe": "Social", "telegram.exe": "Social",
        "valorant-win64-shipping.exe": "Gaming", "cs2.exe": "Gaming", "league of legends.exe": "Gaming",
        "steam.exe": "Gaming Platform", "epicgameslauncher.exe": "Gaming Platform"
    }
    try:
        cursor = conn.cursor()
        for process, category in categories.items():
            cursor.execute("INSERT OR IGNORE INTO app_categories (process_name, category) VALUES (?, ?)", (process, category))
        conn.commit()
        logging.info("Initial categories populated.")
    except sqlite3.Error as e:
        logging.error(f"Failed to populate categories: {e}")

def initialize_database():
    """Creates all necessary tables if they don't exist."""
    is_new_db = not os.path.exists(DB_FILE)
    try:
        with get_db_connection() as conn:
            if conn is None: return
            cursor = conn.cursor()
            # Usage log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    window_title TEXT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    duration_seconds INTEGER NOT NULL
                )""")
            # Application categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_categories (
                    process_name TEXT PRIMARY KEY,
                    category TEXT NOT NULL
                )""")
            # Goals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    goal_type TEXT NOT NULL,
                    time_limit_minutes INTEGER NOT NULL,
                    UNIQUE(category, goal_type)
                )""")
            conn.commit()

            if is_new_db:
                logging.info("Creating Kognita database for the first time...")
                _populate_initial_categories(conn)
                logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.critical(f"Database initialization failed: {e}", exc_info=True)

# --- Category Management ---
def get_all_categories():
    """Fetches a sorted list of all unique categories."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM app_categories ORDER BY category")
        # Dönüşü [(Office,), (Web,)] gibi bir tuple listesi olacağından düzelt
        return [item[0] for item in cursor.fetchall()]

def get_uncategorized_apps():
    """Returns a list of process names that are logged but not categorized."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT T1.process_name
            FROM usage_log T1
            LEFT JOIN app_categories T2 ON T1.process_name = T2.process_name
            WHERE T2.category IS NULL AND T1.process_name NOT IN ('idle', 'unknown')
            ORDER BY T1.process_name
        """
        cursor.execute(query)
        return [item[0] for item in cursor.fetchall()]

def update_app_category(process_name, category):
    """Assigns or updates the category for a given process name."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO app_categories (process_name, category) VALUES (?, ?)",
                       (process_name, category))
        conn.commit()
        logging.info(f"Assigned category '{category}' to process '{process_name}'.")

# --- Goal Management ---
def get_goals():
    """Fetches all goals from the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, goal_type, time_limit_minutes FROM goals ORDER BY category")
        return cursor.fetchall()

def add_goal(category, goal_type, time_limit):
    """Adds a new goal to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO goals (category, goal_type, time_limit_minutes) VALUES (?, ?, ?)",
                       (category, goal_type.lower(), time_limit))
        conn.commit()
        logging.info(f"Goal added/updated for category '{category}'.")

def delete_goal(goal_id):
    """Deletes a specific goal from the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()
        logging.info(f"Goal with ID {goal_id} deleted.")

