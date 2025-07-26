# kognita/analyzer.py
import datetime
import logging
from collections import defaultdict
from . import database 

def get_analysis_data(start_date, end_date):
    """
    Belirtilen tarih aralığı için kullanım verilerini alır ve birleştirir.
    Kategori toplamlarını ve toplam süreyi içeren bir sözlük döndürür.
    """
    try:
        all_logs = database.get_all_usage_logs() # ID'yi de içeren loglar gelir
        if not all_logs:
            return defaultdict(int), 0
            
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp()) # UI'dan gelen end_date zaten kapsayıcı (son saniyeye kadar)

        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT process_name, category FROM app_categories")
            categories_map = dict(cursor.fetchall())

        category_totals = defaultdict(int)
        
        for log in all_logs:
            # Sadece ilgili tarih aralığındaki ve 'idle' olmayan logları işle
            if start_timestamp <= log.get('start_time', 0) <= end_timestamp and log.get('process_name') != 'idle':
                category = categories_map.get(log.get('process_name'), 'Other')
                category_totals[category] += log.get('duration_seconds', 0)
    
    except Exception as e:
        logging.error(f"Analiz verisi alınırken hata: {e}", exc_info=True)
        return defaultdict(int), 0
    
    total_duration = sum(category_totals.values())
    
    return category_totals, total_duration

def get_weekly_comparison():
    """Mevcut haftanın verilerini en iyi kategoriler için önceki haftayla karşılaştırır."""
    today = datetime.datetime.now()
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    
    end_of_today = today.replace(hour=23, minute=59, second=59, microsecond=999999) 
    
    end_of_last_week = start_of_this_week - datetime.timedelta(seconds=1) 
    start_of_last_week = end_of_last_week.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=6) # Geçen haftanın başlangıcı

    this_week_data, _ = get_analysis_data(start_of_this_week, end_of_today) 
    last_week_data, _ = get_analysis_data(start_of_last_week, end_of_last_week) 

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
        end_timestamp = int(now.timestamp()) # Bugünün mevcut anına kadar

        for log in all_logs:
            # Log'un başlangıç zamanı aralık içinde mi ve idle değil mi?
            if start_timestamp <= log.get('start_time', 0) <= end_timestamp and log.get('process_name') != 'idle':
                log_datetime = datetime.datetime.fromtimestamp(log['start_time'])
                hour = log_datetime.hour
                hourly_activity[hour] += log.get('duration_seconds', 0)
        
        # Her saat için ortalamayı 7 güne bölerek al
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


def get_daily_average_usage_by_category(num_days=7):
    """Son N gündeki kategori bazında günlük ortalama kullanımı hesaplar."""
    now = datetime.datetime.now()
    start_date_overall = (now - datetime.timedelta(days=num_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_overall = now.replace(hour=23, minute=59, second=59, microsecond=999999) # Bugünün sonu

    all_logs = database.get_all_usage_logs()
    
    daily_category_totals = defaultdict(lambda: defaultdict(int)) 

    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT process_name, category FROM app_categories")
        categories_map = dict(cursor.fetchall())

    for log in all_logs:
        log_datetime = datetime.datetime.fromtimestamp(log.get('start_time', 0))
        if start_date_overall <= log_datetime <= end_date_overall and log.get('process_name') != 'idle':
            log_date_str = log_datetime.strftime('%Y-%m-%d')
            category = categories_map.get(log.get('process_name'), 'Other')
            daily_category_totals[log_date_str][category] += log.get('duration_seconds', 0)

    avg_category_usage = defaultdict(int)
    
    if num_days == 0: return defaultdict(int) 

    for date_str, category_data in daily_category_totals.items():
        for category, duration in category_data.items():
            avg_category_usage[category] += duration

    for category in avg_category_usage:
        avg_category_usage[category] /= num_days 

    return avg_category_usage

def get_most_productive_day(productive_categories=['Office', 'Development', 'Communication']):
    """Son 30 gün içinde en çok verimli kullanımın olduğu haftanın gününü bulur."""
    now = datetime.datetime.now()
    start_date = (now - datetime.timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    all_logs = database.get_all_usage_logs()
    
    daily_productive_time = defaultdict(int) 

    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT process_name, category FROM app_categories")
        categories_map = dict(cursor.fetchall())

    weekday_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    for log in all_logs:
        log_datetime = datetime.datetime.fromtimestamp(log.get('start_time', 0))
        if start_date <= log_datetime <= end_date and log.get('process_name') != 'idle':
            category = categories_map.get(log.get('process_name'), 'Other')
            if category in productive_categories:
                weekday_index = log_datetime.weekday() 
                daily_productive_time[weekday_names[weekday_index]] += log.get('duration_seconds', 0)

    if not daily_productive_time:
        return "Yeterli Veri Yok", 0
    
    most_productive_day = max(daily_productive_time, key=daily_productive_time.get)
    max_time = daily_productive_time[most_productive_day]
    
    return most_productive_day, max_time

def get_app_usage_over_time(process_name, num_days=30):
    """
    Belirli bir uygulamanın son N gündeki günlük kullanım sürelerini döndürür.
    Dönüş formatı: {date_str: duration_seconds}
    """
    now = datetime.datetime.now()
    start_date_overall = (now - datetime.timedelta(days=num_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_overall = now.replace(hour=23, minute=59, second=59, microsecond=999999) # Bugünün sonu

    all_logs = database.get_all_usage_logs()
    
    daily_usage = defaultdict(int)

    for log in all_logs:
        log_datetime = datetime.datetime.fromtimestamp(log.get('start_time', 0))
        if start_date_overall <= log_datetime <= end_date_overall and log.get('process_name', '').lower() == process_name.lower():
            log_date_str = log_datetime.strftime('%Y-%m-%d')
            daily_usage[log_date_str] += log.get('duration_seconds', 0)
    
    return daily_usage

def get_user_suggestions(category_totals, total_duration):
    """Kullanım alışkanlıklarına dayalı basit, kural tabanlı öneriler sunar."""
    suggestions = []

    if not category_totals or total_duration == 0:
        return ["Henüz yeterli veri yok, uygulamayı kullanmaya devam edin!",
                "Kategorilerinizi yöneterek raporlarınızın daha doğru olmasını sağlayabilirsiniz."]

    total_active_minutes = total_duration / 60

    # En çok kullanılan "dikkat dağıtıcı" kategorileri bul
    distracting_categories = ['Social', 'Gaming', 'Media', 'Music'] # 'Web' kaldırıldı, bazen iş için de olabilir
    distraction_time = sum(category_totals.get(cat, 0) for cat in distracting_categories)
    
    work_categories = ['Office', 'Development', 'Design', 'Video', 'Communication']
    work_time = sum(category_totals.get(cat, 0) for cat in work_categories)

    # Öneri 1: Dikkat dağıtıcı kullanım
    if total_active_minutes > 120 and distraction_time / total_duration > 0.25: # 2 saatten fazla aktif ve %25'i dikkat dağıtıcıysa
        top_distracting_cat = ""
        max_dist_time = 0
        for cat in distracting_categories:
            if category_totals.get(cat, 0) > max_dist_time:
                max_dist_time = category_totals[cat]
                top_distracting_cat = cat
        if top_distracting_cat:
            suggestions.append(f"Görünüşe göre '{top_distracting_cat}' gibi dikkat dağıtıcı kategorilerde çok zaman harcıyorsunuz. Odaklanma modunu veya '{top_distracting_cat}' kategorisi için bir 'maksimum kullanım' hedefi belirlemeyi düşünebilirsiniz.")
    
    # Öneri 2: Verimli kullanıma teşvik
    if total_active_minutes > 60 and work_time / total_duration < 0.40: # 1 saatten fazla aktif ve %40'tan azı verimliyse
        suggestions.append("Verimlilik odaklı kategorilerde daha fazla zaman geçirmeye ne dersiniz? 'Office' veya 'Development' gibi kategoriler için kendinize 'minimum kullanım' hedefleri belirleyebilirsiniz.")

    # Öneri 3: Molaların önemi (Toplam aktif süre üzerinden)
    if total_duration > 3 * 3600: # 3 saatten fazla genel aktif kullanım varsa
        suggestions.append("Uzun süreli ekran başında kalmak göz yorgunluğuna ve zihinsel bitkinliğe yol açabilir. Düzenli aralıklarla kısa molalar vermeyi unutmayın.")

    # Öneri 4: Kategorize edilmemiş uygulamalar
    uncategorized_apps_count = len(database.get_uncategorized_apps())
    if uncategorized_apps_count > 5: # 5'ten fazla kategorize edilmemiş uygulama varsa
        suggestions.append(f"{uncategorized_apps_count} adet kategorize edilmemiş uygulamanız var. Bu uygulamalara kategori atayarak raporlarınızın doğruluğunu artırabilirsiniz.")
    
    # Varsayılan/Genel öneri eğer başka özel öneri yoksa
    if not suggestions:
        suggestions.append("Harika iş çıkarıyorsunuz! Dijital alışkanlıklarınız dengeli ve verimli görünüyor. Daha fazla kişiselleştirilmiş öneri için Kognita'yı düzenli kullanmaya devam edin.")
        suggestions.append("Hedefler belirleyerek ve başarımlar kazanarak motivasyonunuzu yüksek tutabilirsiniz.")

    return suggestions