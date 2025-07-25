# kognita/analyzer.py
import sqlite3
import datetime
import logging
from collections import defaultdict
from .database import get_db_connection

def get_analysis_data(start_date, end_date):
    """
    Fetches and aggregates usage data for a specified date range.
    Returns a dictionary of category totals and the total duration.
    """
    try:
        with get_db_connection() as conn:
            if not conn: return defaultdict(int), 0
            cursor = conn.cursor()
            
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())

            query = """
            SELECT L.duration_seconds, COALESCE(C.category, 'Other') as category
            FROM usage_log L
            LEFT JOIN app_categories C ON L.process_name = C.process_name
            WHERE L.start_time >= ? AND L.start_time < ?
              AND L.process_name != 'idle'
            """
            cursor.execute(query, (start_timestamp, end_timestamp))
            records = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch analysis data: {e}", exc_info=True)
        return defaultdict(int), 0
    
    if not records: 
        return defaultdict(int), 0

    category_totals = defaultdict(int)
    for duration, category in records:
        category_totals[category] += duration
    
    total_duration = sum(category_totals.values())
    
    return category_totals, total_duration

def get_weekly_comparison():
    """Compares data from the current week with the previous week for top categories."""
    today = datetime.datetime.now()
    # Haftanın başlangıcını Pazartesi olarak kabul edelim (weekday() == 0)
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    start_of_last_week = start_of_this_week - datetime.timedelta(days=7)

    # Bu hafta şu ana kadar
    this_week_data, _ = get_analysis_data(start_of_this_week, today + datetime.timedelta(days=1))
    # Geçen haftanın tamamı
    last_week_data, _ = get_analysis_data(start_of_last_week, start_of_this_week)

    # Determine top categories based on this week's usage
    top_categories = sorted(this_week_data, key=this_week_data.get, reverse=True)[:3]
    if not top_categories: return None
    
    comparison = {}
    for category in top_categories:
        this_week_minutes = this_week_data.get(category, 0) / 60
        last_week_minutes = last_week_data.get(category, 0) / 60
        comparison[category] = {
            "this_week": this_week_minutes,
            "last_week": last_week_minutes
        }
    return comparison

def get_hourly_activity():
    """Calculates average hourly activity over the last 7 days."""
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)
    
    hourly_activity = defaultdict(int)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            start_timestamp = int(seven_days_ago.timestamp())
            end_timestamp = int(now.timestamp())
            
            cursor.execute("""
                SELECT start_time, duration_seconds FROM usage_log 
                WHERE start_time >= ? AND start_time < ? AND process_name != 'idle'
            """, (start_timestamp, end_timestamp))
            records = cursor.fetchall()

            for start_time, duration in records:
                hour = datetime.datetime.fromtimestamp(start_time).hour
                hourly_activity[hour] += duration
            
            # Ortalama almak için 7'ye böl
            for hour in hourly_activity:
                hourly_activity[hour] /= 7

    except sqlite3.Error as e:
        logging.error(f"Failed to fetch hourly data: {e}", exc_info=True)

    return hourly_activity

def define_user_persona(category_totals, total_duration):
    """Defines a 'digital persona' based on category usage percentages."""
    if not category_totals or total_duration == 0:
        return "Yeterli Veri Yok"

    percentages = {category: (time / total_duration) for category, time in category_totals.items()}
    
    work_percent = percentages.get('Office', 0) + percentages.get('Development', 0) + percentages.get('Communication', 0)
    game_percent = percentages.get('Gaming', 0) + percentages.get('Gaming Platform', 0)
    creative_percent = percentages.get('Design', 0) + percentages.get('Video', 0)
    web_percent = percentages.get('Web', 0) + percentages.get('Social', 0)
    media_percent = percentages.get('Media', 0) + percentages.get('Music', 0)

    if game_percent > 0.45: return "Odaklanmış Oyuncu"
    if work_percent > 0.50: return "Verimlilik Gurusu"
    if creative_percent > 0.40: return "Yaratıcı Sanatçı"
    if work_percent > 0.25 and game_percent > 0.25: return "İş-Oyun Dengeleyicisi"
    if web_percent > 0.50: return "Dijital Kaşif"
    if work_percent > 0.3 and web_percent > 0.3: return "Modern Profesyonel"

    # En yüksek yüzdeye sahip kategoriyi bul
    if percentages:
        dominant_category = max(percentages, key=percentages.get)
        return f"Dengeli Kullanıcı ({dominant_category})"
    
    return "Dengeli Kullanıcı"
