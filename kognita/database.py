# kognita/database.py (Hata Düzeltmeleri Yapılmış Hali)
import sqlite3
import os
import logging
from pathlib import Path
import csv
import datetime
import hashlib
import json

# Şifreleme kütüphanelerini güvenli şekilde import et
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    logging.warning("WMI modülü bulunamadı. Fallback anahtar kullanılacak.")
    WMI_AVAILABLE = False

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    logging.warning("PyCryptodome modülü bulunamadı. Şifreleme devre dışı.")
    CRYPTO_AVAILABLE = False

# Proje kök dizinini belirle
PROJECT_ROOT = Path(__file__).parent.parent
DB_FILE = PROJECT_ROOT / "kognita_data.db"

# --- Veri Şifreleme Mantığı ---
def get_encryption_key():
    """Makineye özel ve tutarlı bir anahtar üretir."""
    if not WMI_AVAILABLE:
        # Fallback: Basit makine tabanlı anahtar
        try:
            import platform
            machine_info = f"kognita-{platform.node()}-{platform.system()}-fallback"
        except:
            machine_info = "kognita-default-fallback-insecure-key"
        return hashlib.sha256(machine_info.encode('utf-8')).digest()
    
    try:
        c = wmi.WMI()
        processor_id = c.Win32_Processor()[0].ProcessorId.strip()
        disk_serial = c.Win32_LogicalDisk(DeviceID="C:")[0].VolumeSerialNumber.strip()
        unique_id = f"kognita-{processor_id}-{disk_serial}-stable-key"
    except Exception as e:
        logging.warning(f"WMI ile makine ID'si alınamadı, fallback kullanılıyor: {e}")
        unique_id = "kognita-default-fallback-insecure-key"
        
    return hashlib.sha256(unique_id.encode('utf-8')).digest()

# Şifreleme anahtarını güvenli şekilde al
ENCRYPTION_KEY = None
if CRYPTO_AVAILABLE:
    ENCRYPTION_KEY = get_encryption_key()
    assert len(ENCRYPTION_KEY) == 32, "Encryption key must be 32 bytes for AES-256"

def encrypt_data(data):
    """Verilen string veriyi AES ile şifreler."""
    if not CRYPTO_AVAILABLE:
        # Şifreleme yoksa veriyi JSON olarak döndür
        if not isinstance(data, str):
            return json.dumps(data)
        return data
    
    if not isinstance(data, str):
        data = json.dumps(data)
    
    try:
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
        ciphered_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        return cipher.iv + ciphered_bytes
    except Exception as e:
        logging.error(f"Şifreleme hatası: {e}")
        return data  # Şifreleme başarısızsa plain text döndür

def decrypt_data(encrypted_data):
    """AES ile şifrelenmiş veriyi çözer."""
    if not CRYPTO_AVAILABLE:
        # Şifreleme yoksa veriyi string olarak döndür
        if isinstance(encrypted_data, bytes):
            return encrypted_data.decode('utf-8')
        return str(encrypted_data)
    
    try:
        if isinstance(encrypted_data, str):
            # Eğer şifrelenmemiş string ise direkt döndür
            return encrypted_data
            
        iv = encrypted_data[:AES.block_size]
        ciphered_bytes = encrypted_data[AES.block_size:]
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv=iv)
        original_bytes = unpad(cipher.decrypt(ciphered_bytes), AES.block_size)
        return original_bytes.decode('utf-8')
    except Exception as e:
        logging.error(f"Şifre çözme hatası: {e}")
        # Fallback: Veriyi string olarak döndürmeye çalış
        if isinstance(encrypted_data, bytes):
            try:
                return encrypted_data.decode('utf-8')
            except:
                return str(encrypted_data)
        return str(encrypted_data)

# --- Veritabanı Fonksiyonları ---

def get_db_connection():
    """Standart SQLite veritabanı bağlantısı kurar."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        conn.execute("PRAGMA foreign_keys = ON")  # Foreign key constraints etkinleştir
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def initialize_database():
    """Tüm tabloları oluşturur."""
    is_new_db = not DB_FILE.exists()
    try:
        with get_db_connection() as conn:
            if conn is None: 
                logging.error("Veritabanı bağlantısı kurulamadı!")
                return False
                
            cursor = conn.cursor()
            
            # Usage logs tablosu - timestamp alanı eklendi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    window_title TEXT,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL,
                    encrypted_data BLOB
                )""")
            
            # Eski usage_log tablosu varsa migrate et
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_log'")
            if cursor.fetchone():
                logging.info("Eski usage_log tablosu bulundu, migration yapılıyor...")
                try:
                    # Eski verileri yeni tabloya taşı
                    cursor.execute("SELECT encrypted_data FROM usage_log")
                    old_data = cursor.fetchall()
                    
                    for (encrypted_data,) in old_data:
                        try:
                            decrypted_str = decrypt_data(encrypted_data)
                            log_data = json.loads(decrypted_str)
                            
                            cursor.execute("""
                                INSERT INTO usage_logs 
                                (process_name, window_title, start_time, end_time, duration_seconds, timestamp, encrypted_data) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (log_data.get('process_name', 'unknown'),
                                 log_data.get('window_title', ''),
                                 log_data.get('start_time', 0),
                                 log_data.get('end_time', 0),
                                 log_data.get('duration_seconds', 0),
                                 log_data.get('start_time', 0),  # timestamp olarak start_time kullan
                                 encrypted_data))
                        except Exception as e:
                            logging.error(f"Migration sırasında veri hatası: {e}")
                    
                    # Eski tabloyu sil
                    cursor.execute("DROP TABLE usage_log")
                    conn.commit()
                    logging.info("Migration tamamlandı.")
                except Exception as e:
                    logging.error(f"Migration hatası: {e}")
            
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
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(category, goal_type, process_name, start_time_of_day, end_time_of_day)
                )""")
            
            # Goals tablosuna sütun eklemeleri
            cursor.execute("PRAGMA table_info(goals)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'process_name' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN process_name TEXT")
            if 'start_time_of_day' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN start_time_of_day TEXT")
            if 'end_time_of_day' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN end_time_of_day TEXT")
            if 'created_at' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN created_at INTEGER DEFAULT (strftime('%s', 'now'))")

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
                    type TEXT DEFAULT 'info',
                    is_read INTEGER DEFAULT 0
                )""")
            
            # İndeksler oluştur (performans için)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_process ON usage_logs(process_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)")
            
            conn.commit()

            if is_new_db:
                logging.info("Creating Kognita database for the first time...")
                _populate_initial_categories(conn)
                logging.info("Database initialized successfully.")
            
            return True
    except Exception as e:
        logging.critical(f"Database initialization failed: {e}", exc_info=True)
        return False

# --- Kullanım Log Fonksiyonları ---
def add_usage_log(process_name, window_title, start_time, end_time, duration):
    """Kullanım verisini veritabanına ekler."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                logging.error("Veritabanı bağlantısı kurulamadı!")
                return False
                
            cursor = conn.cursor()
            
            # Şifrelenmiş veri de sakla (geriye uyumluluk için)
            log_data = {
                "process_name": process_name,
                "window_title": window_title,
                "start_time": int(start_time),
                "end_time": int(end_time),
                "duration_seconds": int(duration)
            }
            encrypted_log = encrypt_data(log_data) if CRYPTO_AVAILABLE else json.dumps(log_data)
            
            cursor.execute("""
                INSERT INTO usage_logs 
                (process_name, window_title, start_time, end_time, duration_seconds, timestamp, encrypted_data) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (process_name, window_title, int(start_time), int(end_time), int(duration), int(start_time), encrypted_log))
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Usage log ekleme hatası: {e}")
        return False

def get_all_usage_logs():
    """Tüm kullanım loglarını getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, process_name, window_title, start_time, end_time, duration_seconds 
                FROM usage_logs ORDER BY start_time DESC
            """)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'id': row[0],
                    'process_name': row[1],
                    'window_title': row[2],
                    'start_time': row[3],
                    'end_time': row[4],
                    'duration_seconds': row[5]
                })
            return logs
    except Exception as e:
        logging.error(f"Usage logs getirme hatası: {e}")
        return []

def get_recent_usage_logs(limit=50):
    """Son kullanım loglarını getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT process_name, window_title, start_time, end_time, duration_seconds 
                FROM usage_logs 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'process_name': row[0],
                    'window_title': row[1],
                    'start_time': row[2],
                    'end_time': row[3],
                    'duration_seconds': row[4]
                })
            return logs
    except Exception as e:
        logging.error(f"Recent usage logs getirme hatası: {e}")
        return []

def delete_old_usage_logs(days_to_keep):
    """Belirtilen gün sayısından daha eski kullanım loglarını siler."""
    if days_to_keep < 0:
        return 0
    
    try:
        cutoff_timestamp = int((datetime.datetime.now() - datetime.timedelta(days=days_to_keep)).timestamp())
        
        with get_db_connection() as conn:
            if conn is None:
                return 0
                
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usage_logs WHERE timestamp < ?", (cutoff_timestamp,))
            count_to_delete = cursor.fetchone()[0]
            
            if count_to_delete > 0:
                cursor.execute("DELETE FROM usage_logs WHERE timestamp < ?", (cutoff_timestamp,))
                conn.commit()
                logging.info(f"{count_to_delete} adet eski kullanım logu silindi.")
            
            return count_to_delete
    except Exception as e:
        logging.error(f"Eski log silme hatası: {e}")
        return 0

# --- Bildirim Fonksiyonları ---
def add_notification(title, message, notification_type="info"):
    """Bildirimi veritabanına kaydeder."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            timestamp = int(datetime.datetime.now().timestamp())
            cursor.execute(
                "INSERT INTO notifications (timestamp, title, message, type) VALUES (?, ?, ?, ?)",
                (timestamp, title, message, notification_type)
            )
            conn.commit()
            logging.info(f"Bildirim veritabanına eklendi: {title}")
            return True
    except Exception as e:
        logging.error(f"Bildirim ekleme hatası: {e}")
        return False

def get_all_notifications():
    """Tüm bildirimleri veritabanından getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
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
    except Exception as e:
        logging.error(f"Bildirimleri getirme hatası: {e}")
        return []

def mark_notification_as_read(notification_id):
    """Belirli bir bildirimi okundu olarak işaretler."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Bildirim okuma işaretleme hatası: {e}")
        return False

def delete_notification(notification_id):
    """Belirli bir bildirimi siler."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Bildirim silme hatası: {e}")
        return False

def get_unread_notification_count():
    """Okunmamış bildirim sayısını döndürür."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return 0
                
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
            return cursor.fetchone()[0]
    except Exception as e:
        logging.error(f"Okunmamış bildirim sayısı getirme hatası: {e}")
        return 0

# --- Kategori Fonksiyonları ---
def _populate_initial_categories(conn):
    """İlk kategorileri doldurur."""
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
    """Tüm kategorileri getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM app_categories ORDER BY category")
            return [item[0] for item in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Kategorileri getirme hatası: {e}")
        return []

def get_all_processes():
    """Tüm loglanmış process isimlerini döner."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT process_name 
                FROM usage_logs 
                WHERE process_name NOT IN ('idle', 'unknown')
                ORDER BY process_name
            """)
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Process listesi getirme hatası: {e}")
        return []

def get_uncategorized_apps():
    """Kategorize edilmemiş uygulamaları getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT ul.process_name 
                FROM usage_logs ul
                LEFT JOIN app_categories ac ON ul.process_name = ac.process_name
                WHERE ac.process_name IS NULL 
                AND ul.process_name NOT IN ('idle', 'unknown')
                ORDER BY ul.process_name
            """)
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Kategorize edilmemiş uygulamaları getirme hatası: {e}")
        return []

def update_app_category(process_name, category):
    """Uygulama kategorisini günceller."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO app_categories (process_name, category) VALUES (?, ?)",
                           (process_name, category))
            conn.commit()
            logging.info(f"Assigned category '{category}' to process '{process_name}'.")
            return True
    except Exception as e:
        logging.error(f"Kategori güncelleme hatası: {e}")
        return False

def get_category_for_process(process_name):
    """Process için kategorisini getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return 'Other'
                
            cursor = conn.cursor()
            cursor.execute("SELECT category FROM app_categories WHERE process_name = ?", (process_name,))
            result = cursor.fetchone()
            return result[0] if result else 'Other'
    except Exception as e:
        logging.error(f"Kategori getirme hatası: {e}")
        return 'Other'

# --- Hedef Fonksiyonları ---
def add_goal(category=None, process_name=None, goal_type=None, time_limit_minutes=None, start_time_of_day=None, end_time_of_day=None):
    """Hedef ekler veya günceller."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO goals 
                (category, process_name, goal_type, time_limit_minutes, start_time_of_day, end_time_of_day) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (category, process_name, goal_type.lower() if goal_type else None, time_limit_minutes, start_time_of_day, end_time_of_day))
            conn.commit()
            logging.info(f"Goal added/updated: Type={goal_type}, Category={category}, Process={process_name}")
            return True
    except Exception as e:
        logging.error(f"Hedef ekleme hatası: {e}")
        return False

def get_goals():
    """Tüm hedefleri getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
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
    except Exception as e:
        logging.error(f"Hedefleri getirme hatası: {e}")
        return []

def delete_goal(goal_id):
    """Hedef siler."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            conn.commit()
            logging.info(f"Goal with ID {goal_id} deleted.")
            return True
    except Exception as e:
        logging.error(f"Hedef silme hatası: {e}")
        return False

# --- Başarım Fonksiyonları ---
def get_unlocked_achievement_ids():
    """Açılmış başarım ID'lerini getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return set()
                
            cursor = conn.cursor()
            cursor.execute("SELECT achievement_id FROM achievements")
            return {item[0] for item in cursor.fetchall()}
    except Exception as e:
        logging.error(f"Başarım ID'leri getirme hatası: {e}")
        return set()

def unlock_achievement(ach_id, name, description, icon_path):
    """Başarım açar."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False
                
            cursor = conn.cursor()
            timestamp = int(datetime.datetime.now().timestamp())
            cursor.execute(
                "INSERT OR IGNORE INTO achievements (achievement_id, name, description, icon_path, unlocked_at) VALUES (?, ?, ?, ?, ?)",
                (ach_id, name, description, icon_path, timestamp)
            )
            conn.commit()
            add_notification(f"🏆 Yeni Başarım: {name}", description, "achievement")
            return True
    except Exception as e:
        logging.error(f"Başarım açma hatası: {e}")
        return False

def get_all_unlocked_achievements():
    """Tüm açılmış başarımları getirir."""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
                
            cursor = conn.cursor()
            cursor.execute("SELECT name, description, icon_path, unlocked_at FROM achievements ORDER BY unlocked_at DESC")
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Başarımları getirme hatası: {e}")
        return []

# --- Dışa Aktarma Fonksiyonları ---
def export_all_data_to_csv(file_path):
    """Verileri CSV olarak dışa aktarır."""
    try:
        all_logs = get_all_usage_logs()
        if not all_logs:
            logging.info("Dışa aktarılacak log verisi bulunamadı.")
            return True, None

        headers = ["id", "process_name", "window_title", "start_time_str", "end_time_str", "duration_seconds"]
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for log in all_logs:
                writer.writerow([
                    log.get("id", ""),
                    log.get("process_name", ""),
                    log.get("window_title", ""),
                    datetime.datetime.fromtimestamp(log.get("start_time", 0)).strftime('%Y-%m-%d %H:%M:%S') if log.get("start_time") else '',
                    datetime.datetime.fromtimestamp(log.get("end_time", 0)).strftime('%Y-%m-%d %H:%M:%S') if log.get("end_time") else '',
                    log.get("duration_seconds", 0)
                ])
        return True, None
    except Exception as e:
        logging.error(f"CSV dışa aktarma hatası: {e}")
        return False, str(e)