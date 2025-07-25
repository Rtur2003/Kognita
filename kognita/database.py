# kognita/database.py
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
DB_FILE = PROJECT_ROOT / "kognita_data.db" # Tekrar standart .db dosyasına dönüyoruz

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
    """Tüm tabloları oluşturur. Artık şifreleme katmanı burada değil."""
    is_new_db = not DB_FILE.exists()
    try:
        with get_db_connection() as conn:
            if conn is None: return
            cursor = conn.cursor()
            # Şifrelenmiş veriyi saklamak için TEXT yerine BLOB kullanacağız.
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
            # Diğer tablolar şifreleme gerektirmediği için aynı kalabilir.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    goal_type TEXT NOT NULL,
                    time_limit_minutes INTEGER NOT NULL,
                    UNIQUE(category, goal_type)
                )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    icon_path TEXT,
                    unlocked_at INTEGER NOT NULL
                )""")
            conn.commit()

            if is_new_db:
                logging.info("Creating Kognita database for the first time...")
                _populate_initial_categories(conn)
                logging.info("Database initialized successfully.")
    except Exception as e:
        logging.critical(f"Database initialization failed: {e}", exc_info=True)


# --- YENİ: ŞİFRELİ VERİ İŞLEME FONKSİYONLARI ---
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

# --- Mevcut Fonksiyonların Yeni Şifreleme Düzenine Uyarlanması ---

def _populate_initial_categories(conn):
    # Bu fonksiyonun mantığı aynı kalır.
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

def get_uncategorized_apps():
    """Bu fonksiyon artık logları çözerek çalışmalı."""
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

def get_goals():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, goal_type, time_limit_minutes FROM goals ORDER BY category")
        return cursor.fetchall()

def add_goal(category, goal_type, time_limit):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO goals (category, goal_type, time_limit_minutes) VALUES (?, ?, ?)",
                       (category, goal_type.lower(), time_limit))
        conn.commit()
        logging.info(f"Goal added/updated for category '{category}'.")

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
            return True, None # Dışa aktarılacak veri yok

        headers = ["process_name", "window_title", "start_time_str", "end_time_str", "duration_seconds"]
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for log in all_logs:
                writer.writerow([
                    log.get("process_name"),
                    log.get("window_title"),
                    datetime.datetime.fromtimestamp(log.get("start_time")).strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.datetime.fromtimestamp(log.get("end_time")).strftime('%Y-%m-%d %H:%M:%S'),
                    log.get("duration_seconds")
                ])
        return True, None
    except Exception as e:
        logging.error(f"CSV dışa aktarma hatası: {e}")
        return False, str(e)