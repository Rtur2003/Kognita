# kognita/tracker.py

import psutil
import time
import win32process
import win32gui
import logging
from threading import Event
from pynput import mouse, keyboard
from .database import get_db_connection

class ActivityTracker:
    def __init__(self, config, stop_event):
        self.config = config
        self.stop_event = stop_event
        self.last_activity_time = time.time()
        self.idle_threshold_seconds = 180  # Varsayılan değer
        self.update_settings(config)

    def update_settings(self, config):
        """Yapılandırma dosyasından izleyici ayarlarını günceller."""
        self.config = config
        self.idle_threshold_seconds = self.config.get('settings', {}).get('idle_threshold_seconds', 180)
        logging.info(f"İzleyici ayarları güncellendi: Boşta kalma eşiği {self.idle_threshold_seconds}sn olarak ayarlandı")

    def _on_activity(self):
        """Kullanıcı aktivitesi algılandığında son aktivite zamanını günceller."""
        self.last_activity_time = time.time()

    def _start_listeners(self):
        """Klavye ve fare hareketlerini dinleyen pynput dinleyicilerini başlatır."""
        # pynput dinleyicilerini doğrudan kendi metodlarımıza bağlayalım
        mouse_listener = mouse.Listener(
            on_move=lambda x, y: self._on_activity(),
            on_click=lambda x, y, button, pressed: self._on_activity(),
            on_scroll=lambda x, y, dx, dy: self._on_activity()
        )
        keyboard_listener = keyboard.Listener(
            on_press=lambda key: self._on_activity()
        )
        
        mouse_listener.daemon = True
        keyboard_listener.daemon = True
        mouse_listener.start()
        keyboard_listener.start()
        logging.info("Aktivite dinleyicileri başlatıldı.")

    def _get_active_process_info(self):
        """Aktif pencereye ait işlem adını ve pencere başlığını döndürür."""
        if time.time() - self.last_activity_time > self.idle_threshold_seconds:
            return 'idle', 'Kullanıcı Boşta'
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return 'idle', 'Aktif pencere yok'
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == 0:
                return 'unknown', 'Bilinmeyen'
            process = psutil.Process(pid)
            return process.name().lower(), win32gui.GetWindowText(hwnd)
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            # Hataları loglayalım ama programı çökertmeyelim
            logging.debug(f"Aktif işlem bilgisi alınırken hata: {e}")
            return 'unknown', 'Bilinmeyen'

    def _log_activity(self, conn, process_name, title, start_time, end_time):
        """Aktiviteyi veritabanına kaydeder."""
        duration = int(end_time - start_time)
        # Çok kısa süreli veya anlamsız kayıtları filtrele
        if duration < 2 or process_name in ['idle', 'unknown']:
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usage_log (process_name, window_title, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?, ?)",
                (process_name, title, int(start_time), int(end_time), duration)
            )
            conn.commit()
            logging.info(f"Loglandı: {process_name} - {duration}s - {title[:40]}")
        except Exception as e:
            logging.error(f"Veritabanına loglama sırasında hata: {e}")

    def start_tracking(self):
        """Ana takip döngüsünü başlatır."""
        self._start_listeners()
        logging.info("Kognita Tracker aktif.")
        
        last_process_name, last_window_title = self._get_active_process_info()
        session_start_time = time.time()

        try:
            while not self.stop_event.is_set():
                current_process_name, current_window_title = self._get_active_process_info()
                
                if current_process_name != last_process_name or current_window_title != last_window_title:
                    session_end_time = time.time()
                    with get_db_connection() as conn:
                        if conn:
                            self._log_activity(conn, last_process_name, last_window_title, session_start_time, session_end_time)
                    
                    session_start_time = time.time()
                    last_process_name = current_process_name
                    last_window_title = current_window_title

                # stop_event.wait() kullanımı, döngünün daha verimli çalışmasını sağlar.
                self.stop_event.wait(3) # 3 saniyede bir kontrol et
        finally:
            logging.info("Kognita Tracker durduruluyor...")
            # Kapanışta son aktiviteyi de kaydet
            final_end_time = time.time()
            with get_db_connection() as conn:
                if conn:
                    self._log_activity(conn, last_process_name, last_window_title, session_start_time, final_end_time)
            logging.info("Tracker thread'i düzgün bir şekilde sonlandırıldı.")
