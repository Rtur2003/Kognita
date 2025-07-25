# main.py

import pystray
from PIL import Image
from threading import Thread
import tkinter as tk
from tkinter import messagebox
import sys
import os
import json
import logging
from plyer import notification
from datetime import datetime, time

# Yerel modülleri içe aktar
from kognita.tracker import Tracker
from kognita import database, analyzer, ui

CONFIG_FILE = "config.json"

def resource_path(relative_path):
    """ PyInstaller tarafından oluşturulan geçici dizindeki dosyalara erişim sağlar. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_logging():
    """Uygulama genelinde kullanılacak merkezi logging yapılandırması."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler("kognita_app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Application starting...")

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.config = self.load_config()
        self.tracker_instance = Tracker(self.config)
        self.background_threads = []
        self.icon = None

    def load_config(self):
        """Yapılandırmayı config.json'dan yükler, yoksa oluşturur."""
        if not os.path.exists(CONFIG_FILE):
            logging.warning(f"{CONFIG_FILE} not found, creating a default one.")
            default_config = {"settings": {"idle_threshold_seconds": 180}, "app_state": {"first_run": True}}
            self.save_config(default_config)
            return default_config
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Error decoding {CONFIG_FILE}. Reverting to default.")
            return {"settings": {"idle_threshold_seconds": 180}, "app_state": {"first_run": True}}

    def save_config(self, config_data=None):
        """Yapılandırmayı config.json'a kaydeder."""
        if config_data is None:
            config_data = self.config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        logging.info("Configuration saved.")

    def goal_checker_loop(self):
        """Hedefleri periyodik olarak kontrol eden ve bildirim gönderen döngü."""
        checked_goals_today = set()
        while not self.tracker_instance.stop_flag.is_set():
            now = datetime.now()
            if now.time() >= time(0, 0) and now.time() <= time(0, 15):
                checked_goals_today.clear()
            goals = database.get_goals()
            if not goals:
                self.tracker_instance.stop_flag.wait(1800)
                continue
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            category_totals, _ = analyzer.get_analysis_data(start_of_day, now)
            for goal_id, category, goal_type, time_limit_min in goals:
                if goal_id in checked_goals_today:
                    continue
                usage_minutes = category_totals.get(category, 0) / 60
                notification_sent = False
                message = ""
                if goal_type == 'max' and usage_minutes > time_limit_min:
                    message = f"'{category}' için günlük limitinizi ({time_limit_min} dk) aştınız."
                    notification_sent = True
                elif goal_type == 'min' and usage_minutes >= time_limit_min:
                    message = f"Tebrikler! '{category}' için günlük hedefinize ({time_limit_min} dk) ulaştınız."
                    notification_sent = True
                if notification_sent:
                    logging.info(f"Sending goal notification: {message}")
                    notification.notify(
                        title='Kognita - Hedef Durumu',
                        message=message,
                        app_name='Kognita',
                        app_icon=resource_path('icon.ico') if 'icon.ico' in os.listdir() else None,
                        timeout=15
                    )
                    checked_goals_today.add(goal_id)
            self.tracker_instance.stop_flag.wait(900)

    def run_background_threads(self):
        """Arka plan iş parçacıklarını başlatır ve listeye ekler."""
        tracker_thread = Thread(target=self.tracker_instance.start_tracking, daemon=True)
        goal_checker_thread = Thread(target=self.goal_checker_loop, daemon=True)
        self.background_threads.extend([tracker_thread, goal_checker_thread])
        for t in self.background_threads:
            t.start()
        logging.info("Background threads (Tracker, Goal Checker) started.")

    def exit_action(self, icon=None, item=None):
        """Uygulamadan temiz bir çıkış için hazırlık yapar."""
        logging.info("Exit action initiated by user.")
        self.tracker_instance.stop_flag.set()
        if self.icon:
            self.icon.stop()
        self.root.quit()

    def run(self):
        """Uygulamayı başlatır ve sistem tepsisi ikonunu çalıştırır."""
        database.initialize_database()
        self.run_background_threads()

        try:
            image = Image.open(resource_path("icon.png"))
        except FileNotFoundError:
            logging.error("icon.png not found!")
            messagebox.showerror("Hata", "Gerekli icon.png dosyası bulunamadı. Uygulama sonlandırılıyor.")
            self.exit_action()
            return
            
        menu = (
            pystray.MenuItem('Raporu Göster', lambda: ui.ReportWindow(master=self.root), default=True),
            pystray.MenuItem('Hedefleri Yönet', lambda: ui.GoalsWindow(master=self.root)),
            pystray.MenuItem('Ayarlar', lambda: ui.SettingsWindow(master=self.root, app_instance=self)),
            pystray.MenuItem('Çıkış', self.exit_action)
        )
        self.icon = pystray.Icon("Kognita", image, "Kognita Aktivite Takipçisi", menu)

        # pystray'i kendi thread'inde çalıştır
        pystray_thread = Thread(target=self.icon.run, daemon=True)
        pystray_thread.start()

        if self.config.get('app_state', {}).get('first_run', True):
            def show_welcome():
                logging.info("First run, showing welcome notification.")
                self.icon.notify("Kognita'ya hoş geldiniz!", "Aktiviteleriniz artık arka planda sessizce takip ediliyor.")
                self.config['app_state']['first_run'] = False
                self.save_config()
            self.root.after(2000, show_welcome) # 2 saniye sonra göster

        # Tkinter'in ana döngüsünü başlat. Bu, programın ana thread'i olacak.
        self.root.mainloop()

        # mainloop sonlandığında (exit_action'da root.quit() çağrılınca), temiz çıkış yap
        logging.info("Tkinter mainloop finished. Cleaning up.")
        # Arka plan thread'lerinin sonlanmasını bekle (opsiyonel ama iyi bir pratik)
        for t in self.background_threads:
            if t.is_alive():
                t.join(timeout=1) # 1 saniye bekle
        logging.info("Application exited gracefully.")


if __name__ == "__main__":
    setup_logging()
    app = App()
    app.run()
