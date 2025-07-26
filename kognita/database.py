# kognita/database.py (Güncellenmiş Hali)
import sqlite3
import os
import logging
from pathlib import Path
import csv
import datetime
import hashlib
import wmi
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import json

# Proje kök dizinini belirle
PROJECT_ROOT = Path(__file__).parent.parent
DB_FILE = PROJECT_ROOT / "kognita_data.db"

# --- YENİ: Veri Şifreleme Mantığı ---
def get_encryption_key():
    """Makineye özel ve tutarlı bir anahtar üretir."""
    try:
        c = wmi.WMI()
        processor_id = c.Win32_Processor()[0].ProcessorId.strip()
        disk_serial = c.Win32_LogicalDisk(DeviceID="C:")[0].VolumeSerialNumber.strip()
        unique_id = f"kognita-{processor_id}-{disk_serial}-stable-key"
    except Exception as e:
        logging.warning(f"WMI ile makine ID'si alınamadı, fallback kullanılıyor: {e}")
        unique_id = "kognita-default-fallback-insecure-key"
        
    return hashlib.sha256(unique_id.encode('utf-8')).digest()

ENCRYPTION_KEY = get_encryption_key()
# AES-256 (32 byte) anahtar kullanıyoruz
assert len(ENCRYPTION_KEY) == 32

def encrypt_data(data):
    """Verilen string veriyi AES ile şifreler."""
    if not isinstance(data, str):
        data = json.dumps(data) # Veri string değilse JSON'a çevir
    
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
    ciphered_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    # iv (başlatma vektörü) + şifreli veri. iv olmadan şifre çözülemez.
    return cipher.iv + ciphered_bytes

def decrypt_data(encrypted_data):
    """AES ile şifrelenmiş veriyi çözer."""
    iv = encrypted_data[:AES.block_size]
    ciphered_bytes = encrypted_data[AES.block_size:]
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv=iv)
    original_bytes = unpad(cipher.decrypt(ciphered_bytes), AES.block_size)
    return original_bytes.decode('utf-8')

# --- Veritabanı Fonksiyonları ---

def get_db_connection():
    """Standart SQLite veritabanı bağlantısı kurar."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def initialize_database():
    """Tüm tabloları oluşturur."""
    is_new_db = not DB_FILE.exists()
    try:
        with get_db_connection() as conn:
            if conn is None: return
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    encrypted_data BLOB NOT NULL 
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_categories (
                    process_name TEXT PRIMARY KEY,
                    category TEXT NOT NULL
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT, 
                    process_name TEXT, 
                    goal_type TEXT NOT NULL, 
                    time_limit_minutes INTEGER, 
                    start_time_of_day TEXT, 
                    end_time_of_day TEXT,   
                    UNIQUE(category, goal_type, process_name, start_time_of_day, end_time_of_day) -- Daha spesifik UNIQUE constraint
                )""")
            
            # Goals tablosuna sütun eklemeleri (Eğer daha önceki versiyondan geçiş yapılıyorsa)
            cursor.execute("PRAGMA table_info(goals)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'process_name' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN process_name TEXT")
            if 'start_time_of_day' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN start_time_of_day TEXT")
            if 'end_time_of_day' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN end_time_of_day TEXT")


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    icon_path TEXT,
                    unlocked_at INTEGER NOT NULL
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT,
                    is_read INTEGER DEFAULT 0
                )""")
            conn.commit()

            if is_new_db:
                logging.info("Creating Kognita database for the first time...")
                _populate_initial_categories(conn)
                logging.info("Database initialized successfully.")
    except Exception as e:
        logging.critical(f"Database initialization failed: {e}", exc_info=True)


# --- YENİ: Veri Şifreleme Fonksiyonları ---
def add_usage_log(process_name, window_title, start_time, end_time, duration):
    """Kullanım verisini şifreleyerek veritabanına ekler."""
    log_data = {
        "process_name": process_name,
        "window_title": window_title,
        "start_time": int(start_time),
        "end_time": int(end_time),
        "duration_seconds": int(duration)
    }
    encrypted_log = encrypt_data(log_data)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usage_log (encrypted_data) VALUES (?)", (encrypted_log,))
        conn.commit()

def get_all_usage_logs():
    """Tüm kullanım loglarını şifresini çözerek getirir."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT encrypted_data FROM usage_log")
        logs = []
        for (encrypted_data,) in cursor.fetchall():
            try:
                decrypted_str = decrypt_data(encrypted_data)
                logs.append(json.loads(decrypted_str))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logging.error(f"Bir log verisi çözülemedi veya parse edilemedi: {e}")
        return logs

def delete_old_usage_logs(days_to_keep):
    """Belirtilen gün sayısından daha eski kullanım loglarını siler."""
    if days_to_keep < 0: # Negatif değer, veriyi saklama anlamına gelir.
        return 0 # Silme işlemi yapma

    cutoff_timestamp = int((datetime.datetime.now() - datetime.timedelta(days=days_to_keep)).timestamp())
    
    # Tüm logları çözüp filtreleyerek silinecek olanların ID'lerini bul.
    # encryption nedeniyle SQL sorgusuyla direkt 'start_time' üzerinde WHERE koşulu uygulayamayız.
    # Bu, büyük log dosyalarında performans sorunu yaratabilir, ancak veri güvenliği önceliği nedeniyle bu yaklaşım seçildi.
    all_logs = get_all_usage_logs()
    ids_to_delete = []
    for log in all_logs:
        if log.get('start_time', 0) < cutoff_timestamp:
            # log objesinin bir 'id' alanı yok, bu bir sorun.
            # usage_log tablosunda id'yi çekmemiz gerekiyor.
            # Geçici olarak tüm logları çekip silmek yerine,
            # direkt SQL sorgusunu usage_log'daki 'id' ile yapmalıyız.
            # Ancak encrypted_data BLOB olduğu için start_time'a erişilemez.
            # BU KRİTİK BİR TASARIM TERCİHİ: Şifreleme, veritabanı seviyesinde filtrelemeyi engeller.
            # O YÜZDEN SİLME İŞLEMİ ZORLAŞIYOR.
            # Alternatif: Her encrypted_data blob'unda id veya timestamp'i de tutmak.
            # Şu anki yapıda bu imkansız.
            # Bu, şifreleme tasarımının bir limitasyonu. Eğer çok büyük veri olacaksa,
            # timestamp gibi filtreleme alanları şifrelenmeden tutulmalı.
            
            # Mevcut yapıyla yapılabilecek tek şey, tüm logları çekip Python'da filtreleyip
            # sonra tek tek ID'lerine göre silmek. Bu da çok yavaş olabilir.
            # VEYA: `usage_log` tablosuna şifrelenmemiş `timestamp` sütunu ekle!
            
            # Düzeltme: usage_log tablosuna şifrelenmemiş timestamp sütunu ekleyelim.
            # initialize_database'da güncelleme yapılmalı.
            pass # Şimdilik pas geçiyoruz, initialize_database'de düzeltme gerekecek.
            
    # initialize_database'da usage_log tablosu ALTER TABLE ile güncellenmeli:
    # ALTER TABLE usage_log ADD COLUMN timestamp INTEGER;
    # Daha sonra add_usage_log'da da bu timestamp alanı güncellenmeli.
    
    # Şimdilik, şifrelenmiş veriyi direkt kullanamadığımız için, sadece mantıksal bir yer tutucu bırakıyoruz.
    # Gerçek uygulamada bu çok önemli bir karardır.
    
    # Hızlı düzeltme için, timestamp'i log data içinde tuttuğumuz için,
    # şifrelenmiş verinin kendisini silmek için ID'ye ihtiyacımız var.
    # Logların ID'leri olmadan bu fonksiyon çalışmaz.
    # get_all_usage_logs() fonksiyonu ID döndürmüyor.
    # Database'den sadece encrypted_data çekiyoruz. ID'yi de çekmeliyiz.

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # ID'yi de çekmeliyiz
        cursor.execute("SELECT id, encrypted_data FROM usage_log")
        logs_with_id = []
        for row_id, encrypted_data in cursor.fetchall():
            try:
                decrypted_str = decrypt_data(encrypted_data)
                log_data = json.loads(decrypted_str)
                log_data['id'] = row_id # ID'yi log verisine ekle
                logs_with_id.append(log_data)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logging.error(f"Bir log verisi çözülemedi veya parse edilemedi: {e}")

        ids_to_delete = []
        for log in logs_with_id:
            if log.get('start_time', 0) < cutoff_timestamp:
                ids_to_delete.append(log['id'])
        
        if ids_to_delete:
            placeholders = ','.join('?' * len(ids_to_delete))
            cursor.execute(f"DELETE FROM usage_log WHERE id IN ({placeholders})", ids_to_delete)
            conn.commit()
            logging.info(f"{len(ids_to_delete)} adet eski kullanım logu silindi (tarih öncesi: {datetime.datetime.fromtimestamp(cutoff_timestamp).strftime('%Y-%m-%d %H:%M:%S')}).")
            return len(ids_to_delete)
        else:
            logging.info("Silinecek eski kullanım logu bulunamadı.")
            return 0


# --- Yeni Bildirim Fonksiyonları ---
def add_notification(title, message, notification_type="info"):
    """Bildirimi veritabanına kaydeder."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        timestamp = int(datetime.datetime.now().timestamp())
        cursor.execute(
            "INSERT INTO notifications (timestamp, title, message, type) VALUES (?, ?, ?, ?)",
            (timestamp, title, message, notification_type)
        )
        conn.commit()
        logging.info(f"Bildirim veritabanına eklendi: {title} - {message}")

def get_all_notifications():
    """Tüm bildirimleri veritabanından getirir."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, title, message, type, is_read FROM notifications ORDER BY timestamp DESC")
        return [{
            "id": row[0],
            "timestamp": row[1],
            "title": row[2],
            "message": row[3],
            "type": row[4],
            "is_read": bool(row[5])
        } for row in cursor.fetchall()]

def mark_notification_as_read(notification_id):
    """Belirli bir bildirimi okundu olarak işaretler."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        conn.commit()

def delete_notification(notification_id):
    """Belirli bir bildirimi siler."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        conn.commit()

def get_unread_notification_count():
    """Okunmamış bildirim sayısını döndürür."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
        return cursor.fetchone()[0]


# --- Mevcut Fonksiyonların Yeni Düzenlemelere Uyarlanması ---

def _populate_initial_categories(conn):
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
    except Exception as e:
        logging.error(f"Failed to populate categories: {e}")

def get_all_categories():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM app_categories ORDER BY category")
        return [item[0] for item in cursor.fetchall()]

def get_all_processes():
    """Tüm loglanmış (idle ve unknown olmayan) process isimlerini döner."""
    all_logs = get_all_usage_logs()
    processes = {log['process_name'] for log in all_logs if log['process_name'] not in ('idle', 'unknown')}
    return sorted(list(processes))

def get_uncategorized_apps():
    """Uygulama kullanım loglarından kategorize edilmemiş uygulamaları getirir."""
    all_logs = get_all_usage_logs()
    logged_processes = {log['process_name'] for log in all_logs if log['process_name'] not in ('idle', 'unknown')}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT process_name FROM app_categories")
        categorized_processes = {row[0] for row in cursor.fetchall()}
    
    uncategorized = sorted(list(logged_processes - categorized_processes))
    return uncategorized

def update_app_category(process_name, category):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO app_categories (process_name, category) VALUES (?, ?)",
                       (process_name, category))
        conn.commit()
        logging.info(f"Assigned category '{category}' to process '{process_name}'.")

def get_category_for_process(process_name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category FROM app_categories WHERE process_name = ?", (process_name,))
        result = cursor.fetchone()
        return result[0] if result else 'Other'


def add_goal(category=None, process_name=None, goal_type=None, time_limit_minutes=None, start_time_of_day=None, end_time_of_day=None):
    """
    Hedef ekler veya günceller. Daha esnek parametreler alır.
    category veya process_name dolu olmalı. time_limit_minutes, start_time_of_day, end_time_of_day goal_type'a göre değişir.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO goals 
            (category, process_name, goal_type, time_limit_minutes, start_time_of_day, end_time_of_day) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (category, process_name, goal_type.lower(), time_limit_minutes, start_time_of_day, end_time_of_day))
        conn.commit()
        logging.info(f"Goal added/updated: Type={goal_type}, Category={category}, Process={process_name}")

def get_goals():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, process_name, goal_type, time_limit_minutes, start_time_of_day, end_time_of_day FROM goals ORDER BY category, process_name")
        return [{
            "id": row[0],
            "category": row[1],
            "process_name": row[2],
            "goal_type": row[3],
            "time_limit_minutes": row[4],
            "start_time_of_day": row[5],
            "end_time_of_day": row[6]
        } for row in cursor.fetchall()]

def delete_goal(goal_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()
        logging.info(f"Goal with ID {goal_id} deleted.")

def get_unlocked_achievement_ids():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT achievement_id FROM achievements")
        return {item[0] for item in cursor.fetchall()}

def unlock_achievement(ach_id, name, description, icon_path):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        timestamp = int(datetime.datetime.now().timestamp())
        cursor.execute(
            "INSERT OR IGNORE INTO achievements (achievement_id, name, description, icon_path, unlocked_at) VALUES (?, ?, ?, ?, ?)",
            (ach_id, name, description, icon_path, timestamp)
        )
        conn.commit()
        add_notification(f"🏆 Yeni Başarım: {name}", description, "achievement")

def get_all_unlocked_achievements():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, icon_path, unlocked_at FROM achievements ORDER BY unlocked_at DESC")
        return cursor.fetchall()

def export_all_data_to_csv(file_path):
    """Verileri çözer ve CSV olarak dışa aktarır."""
    try:
        all_logs = get_all_usage_logs()
        if not all_logs:
            logging.info("Dışa aktarılacak log verisi bulunamadı.")
            return True, None

        headers = ["process_name", "window_title", "start_time_str", "end_time_str", "duration_seconds"]
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for log in all_logs:
                writer.writerow([
                    log.get("process_name"),
                    log.get("window_title"),
                    datetime.datetime.fromtimestamp(log.get("start_time", 0)).strftime('%Y-%m-%d %H:%M:%S') if log.get("start_time") else '',
                    datetime.datetime.fromtimestamp(log.get("end_time", 0)).strftime('%Y-%m-%d %H:%M:%S') if log.get("end_time") else '',
                    log.get("duration_seconds", 0)
                ])
        return True, None
    except Exception as e:
        logging.error(f"CSV dışa aktarma hatası: {e}")
        return False, str(e)