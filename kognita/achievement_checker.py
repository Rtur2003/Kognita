# kognita/achievement_checker.py

from collections import defaultdict
import logging
import datetime
from . import database
from .analyzer import get_analysis_data
from plyer import notification
from .utils import resource_path 

# Başarım tanımları
# achievement_id: (Adı, Açıklama, İkon Dosya Adı, Kontrol Fonksiyonu, Parametre)
ACHIEVEMENTS = {
    'ROOKIE': ("Çaylak", "İlk 1 saatlik aktif kullanımını tamamladın.", "rookie.png", 
               lambda p: p['total_usage'] >= 3600, {}),
               
    'PERSISTENT_USER': ("Azimli Kullanıcı", "Kognita'yı 7 farklı günde kullandın.", "persistent_user.png", 
                        lambda p: p['active_days'] >= 7, {}),
                        
    'PRODUCTIVITY_GURU': ("Verimlilik Gurusu", "Toplamda 10 saat 'Office' veya 'Development' kategorisinde zaman geçirdin.", "productivity_guru.png",
                          lambda p: p['productive_time'] >= 36000, {}),
                          
    'GAME_ADDICT': ("Oyun Meraklısı", "Tek bir günde 4 saatten fazla 'Gaming' kategorisinde zaman geçirdin.", "game_addict.png",
                    lambda p: p['max_daily_gaming'] >= 14400, {}),
                    
    'NIGHT_OWL': ("Gece Kuşu", "Gece yarısı ile sabah 4 arasında en az 2 saat aktif oldun.", "night_owl.png",
                  lambda p: p['night_usage'] >= 7200, {}),

    'WEEKEND_WARRIOR': ("Hafta Sonu Savaşçısı", "Bir hafta sonunda (Cmt-Pzr) toplam 8 saat aktif oldun.", "weekend_warrior.png",
                        lambda p: p['weekend_usage'] >= 28800, {})
}

def _show_notification(title, message):
    """Başarım kazanıldığında bildirim gösterir."""
    try:
        icon_path = resource_path('icon.ico') # İkon yolu doğru mu kontrol et
        notification.notify(
            title=f"🏆 Yeni Başarım: {title}",
            message=message,
            app_name='Kognita',
            app_icon=icon_path,
            timeout=15
        )
        logging.info(f"Başarım bildirimi gösterildi: {title}")
    except Exception as e:
        logging.error(f"Başarım bildirimi gönderilemedi: {e}", exc_info=True)

def check_all_achievements():
    """Tüm kilitli başarımları kontrol eder ve koşullar sağlanıyorsa açar."""
    unlocked_achievements = database.get_unlocked_achievement_ids()
    
    achievements_to_check = {k: v for k, v in ACHIEVEMENTS.items() if k not in unlocked_achievements}

    if not achievements_to_check:
        return 

    params = _get_all_required_data()

    for ach_id, details in achievements_to_check.items():
        name, description, icon, condition, _ = details
        
        try:
            if condition(params):
                database.unlock_achievement(ach_id, name, description, icon) # Bu fonksiyon aynı zamanda add_notification çağırır
                logging.info(f"Başarım kazanıldı: {name}")
                _show_notification(name, description) # Plyer bildirimi de göster
        except Exception as e:
            logging.error(f"Başarım kontrolü sırasında hata ({ach_id}): {e}", exc_info=True)


def _get_all_required_data():
    """Başarım kontrolleri için gerekli tüm metrikleri hesaplayan merkezi fonksiyon."""
    # Tüm logları çekip Python'da filtrelemek, büyük veri kümelerinde yavaş olabilir.
    # Ancak mevcut şifreleme yapısında bu gerekli.

    all_logs = database.get_all_usage_logs() # ID'leri ile birlikte gelir

    total_usage = 0
    active_days_set = set()
    productive_time = 0
    daily_gaming_totals = defaultdict(int)
    night_usage = 0
    weekend_usage = 0

    # Kategorileri önbelleğe al
    categories_map = {}
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT process_name, category FROM app_categories")
        categories_map = dict(cursor.fetchall())

    for log in all_logs:
        process_name = log.get('process_name')
        duration_seconds = log.get('duration_seconds', 0)
        start_time = log.get('start_time', 0)

        if process_name == 'idle' or duration_seconds == 0 or start_time == 0:
            continue

        log_datetime = datetime.datetime.fromtimestamp(start_time)
        category = categories_map.get(process_name, 'Other')

        # Toplam kullanım süresi
        total_usage += duration_seconds

        # Aktif gün sayısı
        active_days_set.add(log_datetime.date())

        # Verimli zaman
        if category in ('Office', 'Development', 'Communication'):
            productive_time += duration_seconds

        # Oyun süresi (günlük)
        if category == 'Gaming':
            daily_gaming_totals[log_datetime.date()] += duration_seconds

        # Gece kullanımı (00:00 - 04:00)
        if 0 <= log_datetime.hour < 4:
            night_usage += duration_seconds

        # Hafta sonu kullanımı (Cumartesi=5, Pazar=6 - datetime.weekday())
        if log_datetime.weekday() in (5, 6):
            weekend_usage += duration_seconds

    max_daily_gaming = max(daily_gaming_totals.values()) if daily_gaming_totals else 0

    return {
        'total_usage': total_usage,
        'active_days': len(active_days_set),
        'productive_time': productive_time,
        'max_daily_gaming': max_daily_gaming,
        'night_usage': night_usage,
        'weekend_usage': weekend_usage
    }