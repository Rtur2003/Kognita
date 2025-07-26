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
import os 
import winreg 
import sentry_sdk 

# kognita modüllerini içe aktar
from kognita import tracker, database, analyzer, ui
from kognita.config_manager import ConfigManager
from kognita import achievement_checker
from kognita.utils import resource_path

class KognitaApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Ana Tkinter penceresini gizle

        self.setup_logging()
        self.config_manager = ConfigManager()
        self._setup_sentry() 
        
        self.stop_event = Event()
        self.focus_session_active = False
        self.dashboard_window = None

        self.tracker_instance = tracker.ActivityTracker(self.config_manager.get('settings'), self.stop_event)
        self.icon = None

    def setup_logging(self):
        """Uygulama genelinde merkezi loglama sistemini kurar."""
        log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)

    def _setup_sentry(self):
        """Sentry hata raporlama entegrasyonunu kurar."""
        if self.config_manager.get('settings.enable_sentry_reporting', True):
            sentry_dsn = os.environ.get("SENTRY_DSN") 
            if not sentry_dsn:
                logging.warning("SENTRY_DSN ortam değişkeni ayarlanmamış. Hata raporlama etkinleştirilemedi.")
                return

            try:
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    traces_sample_rate=1.0,
                    release="kognita@1.0.0", 
                    environment="production", 
                )
                logging.info("Sentry hata raporlama etkinleştirildi.")
            except Exception as e:
                logging.error(f"Sentry başlatılırken hata oluştu: {e}")
        else:
            logging.info("Sentry hata raporlama devre dışı bırakıldı.")

    def show_dashboard(self):
        """Ana dashboard penceresini gösterir."""
        if self.dashboard_window and self.dashboard_window.winfo_exists():
            self.dashboard_window.lift()
            self.dashboard_window.focus_force()
        else:
            self.dashboard_window = ui.MainDashboardWindow(master=self.root, app_instance=self)

    def _set_run_on_startup(self, enable):
        """Uygulamanın Windows başlangıcında çalışıp çalışmamasını ayarlar."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "Kognita"
        app_path = os.path.abspath(sys.argv[0]) 

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                if enable:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                    logging.info(f"Kognita, Windows başlangıcında çalışacak şekilde ayarlandı: {app_path}")
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                        logging.info("Kognita, Windows başlangıcından kaldırıldı.")
                    except FileNotFoundError:
                        logging.info("Kognita başlangıçta zaten ayarlı değil.")
        except Exception as e:
            logging.error(f"Windows başlangıç ayarı değiştirilirken hata oluştu: {e}")

    def start_background_threads(self):
        """Arka plan iş parçacıklarını başlatır."""
        Thread(target=self.tracker_instance.start_tracking, daemon=True).start()
        Thread(target=self.goal_checker_loop, daemon=True).start()
        Thread(target=self.achievement_checker_loop, daemon=True).start()
        Thread(target=self.data_retention_loop, daemon=True).start() 
        logging.info("Arka plan iş parçacıkları (Tracker, Goal Checker, Achievement Checker, Data Retention) başlatıldı.")

    def data_retention_loop(self):
        """Belirlenen sıklıkta eski kullanım loglarını temizler."""
        self.stop_event.wait(300) # Uygulama başlatıldıktan 5 dakika sonra başlasın
        while not self.stop_event.is_set():
            logging.info("Veri saklama politikası kontrolü yapılıyor...")
            try:
                days_to_keep = self.config_manager.get('settings.data_retention_days', 365)
                if days_to_keep > 0: # 0, sonsuz sakla anlamına gelir
                    deleted_count = database.delete_old_usage_logs(days_to_keep)
                    if deleted_count > 0:
                        logging.info(f"{deleted_count} adet eski veri başarıyla temizlendi.")
                else: # days_to_keep 0 ise veya negatif ise temizleme yapma
                    logging.info("Veri saklama süresi sınırsız olarak ayarlanmış (0 veya negatif), temizleme yapılmıyor.")
            except Exception as e:
                logging.error(f"Veri temizleme döngüsünde hata: {e}", exc_info=True)
                sentry_sdk.capture_exception(e)
            self.stop_event.wait(24 * 3600) # Her 24 saatte bir kontrol et

    def achievement_checker_loop(self):
        """Periyodik olarak başarımları kontrol eder."""
        self.stop_event.wait(60) 
        while not self.stop_event.is_set():
            logging.info("Başarım kontrolü yapılıyor...")
            try:
                achievement_checker.check_all_achievements() 
            except Exception as e:
                logging.error(f"Başarım kontrol döngüsünde beklenmedik hata: {e}", exc_info=True)
                sentry_sdk.capture_exception(e) 
            self.stop_event.wait(3600) 

    def goal_checker_loop(self):
        """Periyodik olarak hedefleri kontrol eder ve bildirim gönderir."""
        checked_goals_today = set()
        notification_settings = self.config_manager.get('settings.notification_settings', {})
        enable_goal_notifications = notification_settings.get('enable_goal_notifications', True)

        while not self.stop_event.is_set():
            now = datetime.datetime.now() 
            if now.hour == 0 and now.minute < 5: 
                checked_goals_today.clear()

            goals = database.get_goals() 
            if not goals:
                self.stop_event.wait(900) 
                continue

            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # get_analysis_data'yı çağırırken end_date'i kapsayıcı olarak verelim
            category_totals_today, _ = analyzer.get_analysis_data(start_of_day, now.replace(hour=23, minute=59, second=59, microsecond=999999))
            
            all_logs_for_day = database.get_all_usage_logs() # Tüm logları çek
            # Bugünün loglarını Python'da filtrele
            logs_today_filtered = [
                log for log in all_logs_for_day 
                if start_of_day.timestamp() <= log.get('start_time', 0) <= now.timestamp() and log.get('process_name') != 'idle'
            ]

            current_process_name, _ = self.tracker_instance._get_active_process_info()

            for goal in goals:
                goal_id = goal['id']
                category = goal['category']
                process_name_target = goal['process_name']
                goal_type = goal['goal_type']
                time_limit_min = goal['time_limit_minutes']
                start_time_of_day_str = goal['start_time_of_day']
                end_time_of_day_str = goal['end_time_of_day']

                if not enable_goal_notifications:
                    continue

                # 'block' ve 'time_window_max' dışındaki hedefleri sadece bir kere işaretle
                if goal_id in checked_goals_today and goal_type not in ('block', 'time_window_max'): 
                    continue
                
                try:
                    if goal_type == 'max_usage':
                        usage_minutes = category_totals_today.get(category, 0) / 60
                        if usage_minutes > time_limit_min:
                            self.show_notification('Kognita - Hedef Aşıldı!', f"'{category}' kategorisi için günlük {time_limit_min} dk limitinizi aştınız.", notification_type="goal_exceeded")
                            checked_goals_today.add(goal_id) 
                    
                    elif goal_type == 'min_usage':
                        usage_minutes = category_totals_today.get(category, 0) / 60
                        if usage_minutes >= time_limit_min:
                            self.show_notification('Kognita - Hedef Tamamlandı!', f"Tebrikler! '{category}' kategorisi için günlük {time_limit_min} dk hedefinize ulaştınız.", notification_type="goal_completed")
                            checked_goals_today.add(goal_id) 

                    elif goal_type == 'block' and process_name_target:
                        if current_process_name.lower() == process_name_target.lower(): 
                            self.show_notification('Kognita - Engellenen Uygulama!', f"'{process_name_target}' uygulamasını kullanıyorsunuz. Bu, engellediğiniz bir uygulamadır.", timeout=5, notification_type="goal_block")

                    elif goal_type == 'time_window_max' and category and start_time_of_day_str and end_time_of_day_str:
                        start_hour, start_min = map(int, start_time_of_day_str.split(':'))
                        end_hour, end_min = map(int, end_time_of_day_str.split(':'))

                        current_time_in_minutes = now.hour * 60 + now.minute
                        window_start_time_in_minutes = start_hour * 60 + start_min
                        window_end_time_in_minutes = end_hour * 60 + end_min

                        # Sadece hedef zaman penceresi içindeyken kontrol et
                        if window_start_time_in_minutes <= current_time_in_minutes < window_end_time_in_minutes:
                            category_time_in_window = 0
                            for log in logs_today_filtered: # Bugünün filtrelenmiş loglarını kullan
                                log_dt = datetime.datetime.fromtimestamp(log['start_time'])
                                log_category = database.get_category_for_process(log['process_name'])
                                
                                # Logun zaman aralığı ile hedef zaman aralığının kesişimini bul
                                log_start_min_of_day = log_dt.hour * 60 + log_dt.minute
                                log_end_min_of_day = (log_dt + datetime.timedelta(seconds=log['duration_seconds'])).hour * 60 + \
                                                    (log_dt + datetime.timedelta(seconds=log['duration_seconds'])).minute
                                
                                # Eğer log bir sonraki güne sarkıyorsa veya sadece gün içinde kalıyorsa
                                if log_end_min_of_day < log_start_min_of_day: # Gece yarısını geçti
                                    log_end_min_of_day = 24 * 60 # O günün sonu olarak al

                                overlap_start = max(window_start_time_in_minutes, log_start_min_of_day)
                                overlap_end = min(window_end_time_in_minutes, log_end_min_of_day)
                                
                                if overlap_start < overlap_end and log_category == category:
                                    category_time_in_window += (overlap_end - overlap_start) * 60 # Kesişen süreyi saniyeye çevir

                            usage_minutes_in_window = category_time_in_window / 60
                            if usage_minutes_in_window > time_limit_min:
                                self.show_notification('Kognita - Zaman Aralığı Hedefi Aşıldı!', f"'{category}' kategorisi için {start_time_of_day_str}-{end_time_of_day_str} arasındaki {time_limit_min} dk limitinizi aştınız.", notification_type="goal_time_window_exceeded")
                                checked_goals_today.add(goal_id) 
                except Exception as e:
                    logging.error(f"Hedef kontrolü sırasında hata ({goal_id}): {e}", exc_info=True)
                    sentry_sdk.capture_exception(e) 
            
            self.stop_event.wait(900) 

    def start_focus_session_flow(self):
        """Odaklanma oturumu ayar penceresini açar."""
        if self.focus_session_active:
            ui.messagebox.showinfo("Devam Eden Oturum", "Zaten aktif bir odaklanma oturumu var.")
            return
        
        ui.FocusSetupWindow(master=self.root, on_start_callback=self.start_focus_session)

    def start_focus_session(self, duration_minutes, allowed_categories):
        """Verilen parametrelerle odaklanma oturumunu bir thread'de başlatır."""
        if not self.focus_session_active:
            logging.info(f"{duration_minutes} dakikalık odaklanma oturumu başlatıldı. İzin verilen kategoriler: {allowed_categories}")
            self.focus_session_active = True
            self.update_tray_icon() 
            
            Thread(target=self._focus_session_loop, args=(duration_minutes, allowed_categories), daemon=True).start()

    def _focus_session_loop(self, duration_minutes, allowed_categories):
        """Odaklanma oturumunun arka plan döngüsü."""
        end_time = time.time() + duration_minutes * 60
        notified_apps = set()
        notification_settings = self.config_manager.get('settings.notification_settings', {})
        enable_focus_notifications = notification_settings.get('enable_focus_notifications', True)
        focus_notification_frequency = notification_settings.get('focus_notification_frequency_seconds', 300)
        last_focus_notification_time = time.time() - focus_notification_frequency 

        self.show_notification("Odaklanma Başladı!", f"{duration_minutes} dakika boyunca odaklanma zamanı.", notification_type="focus_start")

        while time.time() < end_time and not self.stop_event.is_set():
            current_time = time.time()
            process_name, _ = self.tracker_instance._get_active_process_info()
            
            if enable_focus_notifications and process_name not in ('idle', 'unknown'):
                category = database.get_category_for_process(process_name)
                if category not in allowed_categories:
                    if (current_time - last_focus_notification_time) >= focus_notification_frequency:
                        self.show_notification("Dikkat Dağıldı!", f"'{process_name}' uygulaması odaklanma kategorilerinde değil. İstersen işine dönebilirsin.", timeout=5, notification_type="focus_distraction")
                        last_focus_notification_time = current_time
                    if process_name not in notified_apps:
                        notified_apps.add(process_name)
                else:
                    if process_name in notified_apps:
                        notified_apps.clear() 
            
            self.stop_event.wait(10) 

        if not self.stop_event.is_set():
            self.show_notification("Oturum Tamamlandı!", f"Tebrikler! {duration_minutes} dakikalık odaklanma oturumunu tamamladın.", notification_type="focus_end")
        
        self.focus_session_active = False
        self.update_tray_icon()

    def show_notification(self, title, message, timeout=10, notification_type="info"):
        """Merkezi bildirim fonksiyonu. Ayarları okur ve geçmişe kaydeder."""
        try:
            notification_settings = self.config_manager.get('settings.notification_settings', {})
            
            if notification_type == "achievement": 
                if not notification_settings.get('show_achievement_notifications', True):
                    return
            else: 
                if notification_type.startswith("goal_") and not notification_settings.get('enable_goal_notifications', True):
                    return
                if notification_type.startswith("focus_") and not notification_settings.get('enable_focus_notifications', True):
                    return

            database.add_notification(title, message, notification_type) 

            icon_path = resource_path('icon.ico')
            notification.notify(
                title=title, message=message, app_name='Kognita', app_icon=icon_path, timeout=timeout
            )
        except Exception as e:
            logging.error(f"Bildirim gönderilemedi veya kaydedilemedi: {e}", exc_info=True)
            sentry_sdk.capture_exception(e) 

    def update_tray_icon(self):
        """Sistem tepsisi menüsünü günceller (Odaklanma modu için)."""
        if self.icon:
            self.icon.menu = self.setup_tray_menu()

    def setup_tray_menu(self):
        """Sistem tepsisi menüsünü oluşturur."""
        focus_item = pystray.MenuItem(
            'Odaklanma Oturumu Başlat', 
            self.start_focus_session_flow, 
            enabled=not self.focus_session_active
        )

        notification_count = database.get_unread_notification_count()
        notification_menu_text = f"Bildirimler ({notification_count})" if notification_count > 0 else "Bildirimler"
        
        return pystray.Menu(
            pystray.MenuItem('Ana Panel', self.show_dashboard),
            pystray.Menu.SEPARATOR,
            focus_item,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Raporu Göster', lambda: ui.ReportWindow(master=self.root)),
            pystray.MenuItem('Hedefleri Yönet', lambda: ui.GoalsWindow(master=self.root)),
            pystray.MenuItem('Kategorileri Yönet', lambda: ui.CategoryManagementWindow(master=self.root)),
            pystray.MenuItem(notification_menu_text, lambda: ui.NotificationHistoryWindow(master=self.root, app_instance=self)), 
            pystray.MenuItem('Başarımlar', lambda: ui.AchievementWindow(master=self.root)), 
            pystray.MenuItem('Ayarlar', lambda: ui.SettingsWindow(master=self.root, app_instance=self)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Çıkış', self.exit_action)
        )

    def setup_tray_icon(self):
        """Sistem tepsisi ikonunu ve menüsünü ayarlar."""
        try:
            image = Image.open(resource_path("icon.png"))
        except FileNotFoundError:
            logging.error("'assets/icon.png' bulunamadı! İkon görüntülenemeyecek.", exc_info=True)
            image = None
        
        self.icon = pystray.Icon("Kognita", image, "Kognita Aktivite Takipçisi", self.setup_tray_menu())
        return self.icon

    def run_tray_icon(self):
        """Sistem tepsisi ikonunu ayrı bir thread'de çalıştırır."""
        self.icon.run()

    def exit_action(self):
        """Uygulamadan çıkış işlemlerini yönetir."""
        logging.info("Çıkış işlemi başlatıldı...")
        self.stop_event.set()
        if self.icon:
            self.icon.stop()
        self.root.quit()

    def on_welcome_closed(self):
        """'first_run' bayrağını günceller ve yapılandırmayı kaydeder."""
        logging.info("İlk kullanım tamamlandı olarak işaretleniyor.")
        self.config_manager.set('app_state.first_run', False)

    def run(self):
        """Uygulamanın ana döngüsünü başlatır ve yönetir."""
        logging.info("Uygulama başlatılıyor...")
        database.initialize_database()

        if self.config_manager.get('app_state', {}).get('first_run', True):
            # WelcomeWindow'u modal olarak göster
            welcome_window = ui.WelcomeWindow(master=self.root, on_close_callback=self.on_welcome_closed)
            self.root.wait_window(welcome_window) # WelcomeWindow kapanana kadar ana döngüyü bloke et
            
        # Eğer welcome_window kapatıldıysa ve uygulama hala çalışıyorsa devam et
        if not self.stop_event.is_set(): 
            ui.apply_global_styles() 
            self.start_background_threads()
            icon = self.setup_tray_icon()
            
            tray_thread = Thread(target=self.run_tray_icon, daemon=True)
            tray_thread.start()

            # Ana panel penceresini göster
            self.show_dashboard()

            self.root.mainloop() # Ana Tkinter döngüsünü başlat
        
        logging.info("Uygulama sonlandırıldı.")

if __name__ == "__main__":
    app = KognitaApp()
    app.run()