# kognita/analyzer.py

import sqlite3
import datetime
from collections import defaultdict
from .database import get_db_connection

def get_analysis_data(days=1):
    """
    Fetches and processes usage data from the database for a given period.
    Returns a tuple: (category_totals, total_duration_seconds) or (None, 0).
    """
    try:
        with get_db_connection() as conn:
            if not conn: return None, 0
            cursor = conn.cursor()
            start_timestamp = (datetime.datetime.now() - datetime.timedelta(days=days)).timestamp()
            query = """
            SELECT L.duration_seconds, COALESCE(C.category, 'Other') as category
            FROM usage_log L
            LEFT JOIN app_categories C ON L.process_name = C.process_name
            WHERE L.start_time >= ?
            """
            cursor.execute(query, (int(start_timestamp),))
            records = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Failed to fetch analysis data: {e}")
        return None, 0
    
    if not records: return None, 0

    category_totals = defaultdict(int)
    total_duration = sum(r[0] for r in records)
    for duration, category in records:
        category_totals[category] += duration
    
    return category_totals, total_duration

def define_user_persona(category_totals, total_duration):
    """Defines a user persona based on the distribution of time across categories."""
    if not category_totals or total_duration == 0:
        return "Not Enough Data"

    percentages = {category: (time / total_duration) for category, time in category_totals.items()}
    work_percent = percentages.get('Office', 0) + percentages.get('Development', 0) + percentages.get('Communication', 0)
    game_percent = percentages.get('Gaming', 0) + percentages.get('Gaming Platform', 0)
    creative_percent = percentages.get('Design', 0) + percentages.get('Video', 0) + percentages.get('Media', 0)
    web_percent = percentages.get('Web', 0) + percentages.get('Social', 0)

    if game_percent > 0.45: return "The Focused Gamer"
    if work_percent > 0.50: return "The Productivity Guru"
    if creative_percent > 0.40: return "The Creative Artist"
    if work_percent > 0.25 and game_percent > 0.25: return "The Work-Life Balancer"
    if web_percent > 0.50: return "The Digital Explorer"

    return "The Balanced User"