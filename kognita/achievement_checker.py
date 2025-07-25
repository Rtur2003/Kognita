# kognita/achievement_checker.py

import logging
import datetime
from . import database
from .analyzer import get_analysis_data
from plyer import notification
from .utils import resource_path # DEĞİŞTİ

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
        icon_path = resource_path('icon.ico')
        notification.notify(
            title=f"🏆 Yeni Başarım: {title}",
            message=message,
            app_name='Kognita',
            app_icon=icon_path,
            timeout=15
        )
        logging.info(f"Başarım bildirimi gösterildi: {title}")
    except Exception as e:
        logging.error(f"Başarım bildirimi gönderilemedi: {e}")

def check_all_achievements():
    """Tüm kilitli başarımları kontrol eder ve koşullar sağlanıyorsa açar."""
    unlocked_achievements = database.get_unlocked_achievement_ids()
    
    # Henüz kazanılmamış başarımları bul
    achievements_to_check = {k: v for k, v in ACHIEVEMENTS.items() if k not in unlocked_achievements}

    if not achievements_to_check:
        return # Kontrol edilecek yeni başarım yoksa fonksiyondan çık

    # Gerekli verileri veritabanından tek seferde çekelim
    params = _get_all_required_data()

    for ach_id, details in achievements_to_check.items():
        name, description, icon, condition, _ = details
        
        try:
            if condition(params):
                database.unlock_achievement(ach_id, name, description, icon)
                logging.info(f"Başarım kazanıldı: {name}")
                _show_notification(name, description)
        except Exception as e:
            logging.error(f"Başarım kontrolü sırasında hata ({ach_id}): {e}")


def _get_all_required_data():
    """Başarım kontrolleri için gerekli tüm metrikleri hesaplayan merkezi fonksiyon."""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Toplam kullanım süresi
        cursor.execute("SELECT SUM(duration_seconds) FROM usage_log WHERE process_name != 'idle'")
        total_usage = cursor.fetchone()[0] or 0
        
        # Aktif gün sayısı
        cursor.execute("SELECT COUNT(DISTINCT date(start_time, 'unixepoch')) FROM usage_log")
        active_days = cursor.fetchone()[0] or 0

        # Verimli zaman (Office + Development)
        cursor.execute("""
            SELECT SUM(L.duration_seconds) FROM usage_log L
            LEFT JOIN app_categories C ON L.process_name = C.process_name
            WHERE C.category IN ('Office', 'Development') AND L.process_name != 'idle'
        """)
        productive_time = cursor.fetchone()[0] or 0

        # Tek bir gündeki en yüksek oyun süresi
        cursor.execute("""
            SELECT MAX(daily_total) FROM (
                SELECT SUM(L.duration_seconds) as daily_total
                FROM usage_log L
                LEFT JOIN app_categories C ON L.process_name = C.process_name
                WHERE C.category = 'Gaming' AND L.process_name != 'idle'
                GROUP BY date(L.start_time, 'unixepoch')
            )
        """)
        max_daily_gaming = cursor.fetchone()[0] or 0

        # Gece kullanımı (00:00 - 04:00)
        cursor.execute("""
            SELECT SUM(duration_seconds) FROM usage_log
            WHERE CAST(strftime('%H', start_time, 'unixepoch') AS INTEGER) >= 0
              AND CAST(strftime('%H', start_time, 'unixepoch') AS INTEGER) < 4
              AND process_name != 'idle'
        """)
        night_usage = cursor.fetchone()[0] or 0

        # Hafta sonu kullanımı (strftime'da %w: 0=Pazar, 6=Cumartesi)
        cursor.execute("""
            SELECT SUM(duration_seconds) FROM usage_log
            WHERE strftime('%w', start_time, 'unixepoch') IN ('0', '6')
            AND process_name != 'idle'
        """)
        weekend_usage = cursor.fetchone()[0] or 0

    return {
        'total_usage': total_usage,
        'active_days': active_days,
        'productive_time': productive_time,
        'max_daily_gaming': max_daily_gaming,
        'night_usage': night_usage,
        'weekend_usage': weekend_usage
    }