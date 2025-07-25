# kognita/database.py
import sqlite3
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_FILE = PROJECT_ROOT / "kognita_data.db"

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def _populate_initial_categories(conn):
    categories = {
        "winword.exe": "Office", "excel.exe": "Office", "powerpnt.exe": "Office",
        "outlook.exe": "Communication", "slack.exe": "Communication", "teams.exe": "Communication",
        "code.exe": "Development", "pycharm64.exe": "Development", "devenv.exe": "Development",
        "explorer.exe": "System", "cmd.exe": "System", "powershell.exe": "System",
        "photoshop.exe": "Design", "illustrator.exe": "Design", "figma.exe": "Design",
        "adobe premiere pro.exe": "Video", "afterfx.exe": "Video",
        "vlc.exe": "Media", "spotify.exe": "Music",
        "chrome.exe": "Web", "firefox.exe": "Web", "msedge.exe": "Web",
        "discord.exe": "Social", "telegram.exe": "Social",
        "valorant-win64-shipping.exe": "Gaming", "cs2.exe": "Gaming", "league of legends.exe": "Gaming",
        "steam.exe": "Gaming Platform"
    }
    cursor = conn.cursor()
    for process, category in categories.items():
        cursor.execute("INSERT OR IGNORE INTO app_categories (process_name, category) VALUES (?, ?)", (process, category))
    conn.commit()

def initialize_database():
    is_new_db = not os.path.exists(DB_FILE)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, process_name TEXT NOT NULL, window_title TEXT,
                    start_time INTEGER NOT NULL, end_time INTEGER NOT NULL, duration_seconds INTEGER NOT NULL
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_categories (
                    process_name TEXT PRIMARY KEY, category TEXT NOT NULL
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY, category TEXT NOT NULL, goal_type TEXT NOT NULL, time_limit_minutes INTEGER NOT NULL
                )""")
            conn.commit()
            if is_new_db:
                print("Creating Kognita database for the first time...")
                _populate_initial_categories(conn)
                print("Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}")

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
        cursor.execute("INSERT INTO goals (category, goal_type, time_limit_minutes) VALUES (?, ?, ?)",
                       (category, goal_type, time_limit))
        conn.commit()

def delete_goal(goal_id):
    """Deletes a specific goal from the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()