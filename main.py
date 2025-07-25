# main.py

import datetime
import pystray
from PIL import Image
from threading import Thread, Event
import tkinter as tk
import sys
import logging
from plyer import notification
import time

# kognita modüllerini içe aktar
from kognita import tracker, database, analyzer, ui
from kognita.config_manager import ConfigManager
from kognita import achievement_checker
from kognita.utils import resource_path # DEĞİŞTİ

class KognitaApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Ana Tkinter penceresini gizle

        self.setup_logging()
        self.config_manager = ConfigManager()
        
        # Olayları (Events) başlat
        self.stop_event = Event()

        # Modül örneklerini oluştur
        self.tracker_instance = tracker.ActivityTracker(self.config_manager.get('settings'), self.stop_event)
        self.icon = None

    def setup_logging(self):
        """Uygulama genelinde merkezi loglama sistemini kurar."""
        log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)

    def start_background_threads(self):
        """Arka plan iş parçacıklarını başlatır."""
        Thread(target=self.tracker_instance.start_tracking, daemon=True).start()
        Thread(target=self.goal_checker_loop, daemon=True).start()
        Thread(target=self.achievement_checker_loop, daemon=True).start()
        logging.info("Arka plan iş parçacıkları (Tracker, Goal Checker, Achievement Checker) başlatıldı.")

    def achievement_checker_loop(self):
        """Periyodik olarak başarımları kontrol eder."""
        # Uygulama açıldıktan kısa bir süre sonra ilk kontrolü yap
        self.stop_event.wait(60) 
        while not self.stop_event.is_set():
            logging.info("Başarım kontrolü yapılıyor...")
            try:
                achievement_checker.check_all_achievements()
            except Exception as e:
                logging.error(f"Başarım kontrol döngüsünde beklenmedik hata: {e}")
            # Başarım kontrolünü çok sık yapmaya gerek yok, saatte bir yeterli.
            self.stop_event.wait(3600) 

    def goal_checker_loop(self):
        """Periyodik olarak hedefleri kontrol eder ve bildirim gönderir."""
        checked_goals_today = set()
        while not self.stop_event.is_set():
            now = time.localtime()
            # Her gün başında kontrol edilen hedefleri sıfırla
            if now.tm_hour == 0 and now.tm_min < 15:
                checked_goals_today.clear()

            goals = database.get_goals()
            if not goals:
                self.stop_event.wait(1800) # Hedef yoksa 30 dakika bekle
                continue

            start_of_day = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            category_totals, _ = analyzer.get_analysis_data(start_of_day, datetime.datetime.now())

            for goal_id, category, goal_type, time_limit_min in goals:
                if goal_id in checked_goals_today:
                    continue
                
                usage_minutes = category_totals.get(category, 0) / 60
                notification_sent = False
                
                try:
                    icon_path = resource_path('icon.ico') # DEĞİŞTİ
                    if goal_type == 'max' and usage_minutes > time_limit_min:
                        notification.notify(title='Kognita - Hedef Aşıldı!', message=f"'{category}' için günlük {time_limit_min} dk limitinizi aştınız.", app_name='Kognita', app_icon=icon_path, timeout=10)
                        notification_sent = True
                    elif goal_type == 'min' and usage_minutes >= time_limit_min:
                        notification.notify(title='Kognita - Hedef Tamamlandı!', message=f"Tebrikler! '{category}' için günlük {time_limit_min} dk hedefinize ulaştınız.", app_name='Kognita', app_icon=icon_path, timeout=10)
                        notification_sent = True
                except Exception as e:
                    logging.error(f"Bildirim gönderilemedi: {e}")

                if notification_sent:
                    checked_goals_today.add(goal_id)
            
            self.stop_event.wait(900) # 15 dakikada bir kontrol et

    def setup_tray_icon(self):
        """Sistem tepsisi ikonunu ve menüsünü ayarlar."""
        try:
            image = Image.open(resource_path("icon.png")) # DEĞİŞTİ
        except FileNotFoundError:
            logging.error("'assets/icon.png' bulunamadı! İkon görüntülenemeyecek.")
            image = None
        
        menu = pystray.Menu(
            pystray.MenuItem('Raporu Göster', lambda: ui.ReportWindow(master=self.root), default=True),
            pystray.MenuItem('Hedefleri Yönet', lambda: ui.GoalsWindow(master=self.root)),
            pystray.MenuItem('Ayarlar', lambda: ui.SettingsWindow(master=self.root, app_instance=self)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Çıkış', self.exit_action)
        )
        self.icon = pystray.Icon("Kognita", image, "Kognita Aktivite Takipçisi", menu)
        return self.icon

    def run_tray_icon(self):
        """Sistem tepsisi ikonunu ayrı bir thread'de çalıştırır."""
        self.icon.run()

    def exit_action(self):
        """Uygulamadan çıkış işlemlerini yönetir."""
        logging.info("Çıkış işlemi başlatıldı...")
        self.stop_event.set() # Tüm döngülere durma sinyali gönder
        if self.icon:
            self.icon.stop()
        self.root.quit() # Tkinter ana döngüsünü sonlandır

    def on_welcome_closed(self):
        """'first_run' bayrağını günceller ve yapılandırmayı kaydeder."""
        logging.info("İlk kullanım tamamlandı olarak işaretleniyor.")
        self.config_manager.set('app_state.first_run', False)
        self.root.quit()

    def run(self):
        """Uygulamanın ana döngüsünü başlatır ve yönetir."""
        logging.info("Uygulama başlatılıyor...")
        database.initialize_database()

        if self.config_manager.get('app_state', {}).get('first_run', True):
            ui.WelcomeWindow(master=self.root, on_close_callback=self.on_welcome_closed)
            self.root.mainloop()

        if not self.stop_event.is_set():
            self.start_background_threads()
            icon = self.setup_tray_icon()
            
            tray_thread = Thread(target=self.run_tray_icon, daemon=True)
            tray_thread.start()

            self.root.mainloop()
        
        logging.info("Uygulama sonlandırıldı.")

if __name__ == "__main__":
    app = KognitaApp()
    app.run()