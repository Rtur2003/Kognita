# kognita/analyzer.py
import datetime
import logging
from collections import defaultdict
from . import database # database import'u güncel haliyle kalıyor

def get_analysis_data(start_date, end_date):
    """
    Belirtilen tarih aralığı için kullanım verilerini alır ve birleştirir.
    Kategori toplamlarını ve toplam süreyi içeren bir sözlük döndürür.
    """
    try:
        # --- DEĞİŞTİ: Veritabanından tüm logları çözülmüş olarak alıyoruz ---
        all_logs = database.get_all_usage_logs()
        if not all_logs:
            return defaultdict(int), 0
            
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        # Kategorileri önbelleğe alalım
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT process_name, category FROM app_categories")
            categories_map = dict(cursor.fetchall())

        category_totals = defaultdict(int)
        
        # Filtrelemeyi ve analizleri Python içinde yapıyoruz
        for log in all_logs:
            if start_timestamp <= log['start_time'] < end_timestamp and log['process_name'] != 'idle':
                category = categories_map.get(log['process_name'], 'Other')
                category_totals[category] += log['duration_seconds']
    
    except Exception as e:
        logging.error(f"Analiz verisi alınırken hata: {e}", exc_info=True)
        return defaultdict(int), 0
    
    total_duration = sum(category_totals.values())
    
    return category_totals, total_duration

def get_weekly_comparison():
    """Mevcut haftanın verilerini en iyi kategoriler için önceki haftayla karşılaştırır."""
    today = datetime.datetime.now()
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    start_of_last_week = start_of_this_week - datetime.timedelta(days=7)

    this_week_data, _ = get_analysis_data(start_of_this_week, today + datetime.timedelta(days=1))
    last_week_data, _ = get_analysis_data(start_of_last_week, start_of_this_week)

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
    """Son 7 günün saatlik aktivite ortalamasını hesaplar."""
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)
    
    hourly_activity = defaultdict(int)
    
    try:
        all_logs = database.get_all_usage_logs()
        start_timestamp = int(seven_days_ago.timestamp())
        end_timestamp = int(now.timestamp())

        for log in all_logs:
            if start_timestamp <= log['start_time'] < end_timestamp and log['process_name'] != 'idle':
                hour = datetime.datetime.fromtimestamp(log['start_time']).hour
                hourly_activity[hour] += log['duration_seconds']
        
        for hour in hourly_activity:
            hourly_activity[hour] /= 7

    except Exception as e:
        logging.error(f"Saatlik veri alınırken hata: {e}", exc_info=True)

    return hourly_activity

def define_user_persona(category_totals, total_duration):
    """Kategori kullanım yüzdelerine göre bir 'dijital persona' tanımlar."""
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

    if percentages:
        dominant_category = max(percentages, key=percentages.get)
        return f"Dengeli Kullanıcı ({dominant_category})"
    
    return "Dengeli Kullanıcı"