# main.py

import datetime
import pystray
from PIL import Image
from threading import Thread, Event
import tkinter as tk
import sys
import logging
import time
import os 
import winreg 
import sentry_sdk
from pathlib import Path
from logging.handlers import RotatingFileHandler

# YENİ: Dil yöneticisi en başta import edilmeli
from kognita.localization import loc
from kognita import tracker, database, analyzer, ui, achievement_checker
from kognita.config_manager import ConfigManager
from kognita.utils import resource_path

APP_VERSION = "1.0.0"

class KognitaApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.app_version = APP_VERSION
        self.log_file_path = None
        self.setup_logging()
        self.config_manager = ConfigManager()
        self._install_exception_hook()
        self._setup_sentry() 
        
        self.stop_event = Event()
        self.focus_session_active = False
        self.dashboard_window = None
        self.last_block_notification_times = {}

        # Veritabanını ilk başlatma
        try:
            database.initialize_database()
            logging.info("Veritabanı başarıyla başlatıldı.")
        except Exception as e:
            logging.error(f"Veritabanı başlatılırken hata: {e}")
            # Hata durumunda da devam etsin ama güvenli mod
            
        self.tracker_instance = tracker.ActivityTracker(self.config_manager.get('settings'), self.stop_event)
        self.icon = None

    def setup_logging(self):
        """Uygulama genelinde merkezi loglama sistemini kurar."""
        log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        level_name = os.environ.get('KOGNITA_LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, level_name, logging.INFO)
        handlers = [logging.StreamHandler(sys.stdout)]

        try:
            logs_dir = Path(os.environ.get('APPDATA', Path.home())) / 'Kognita' / 'logs'
            logs_dir.mkdir(parents=True, exist_ok=True)
            self.log_file_path = logs_dir / 'kognita.log'
            handlers.append(RotatingFileHandler(self.log_file_path, maxBytes=1_000_000, backupCount=3, encoding='utf-8'))
        except Exception as log_error:
            self.log_file_path = None
            logging.basicConfig(level=log_level, format=log_format, stream=sys.stdout)
            logging.warning(f"Log dosyasi olusturulamadi, yalnizca stdout kullanilacak: {log_error}")
            return

        logging.basicConfig(level=log_level, format=log_format, handlers=handlers)
        if self.log_file_path:
            logging.info(f"Loglar '{self.log_file_path}' konumuna yaziliyor.")

    def _setup_sentry(self):
        """Sentry hata raporlama entegrasyonunu kurar."""
        if not self.config_manager.get('settings.enable_sentry_reporting', False):
            logging.info("Sentry hata raporlama devre disi (config ayari).")
            return

        sentry_dsn = os.environ.get('SENTRY_DSN')
        if not sentry_dsn:
            logging.info("SENTRY_DSN ortam degiskeni ayarlanmamis. Hata raporlama atlanacak.")
            return

        try:
            traces_rate = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.05'))
            profiles_rate = float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.0'))
        except ValueError:
            traces_rate, profiles_rate = 0.05, 0.0

        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=traces_rate,
                profiles_sample_rate=profiles_rate,
                release=f"kognita@{APP_VERSION}",
                environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),
            )
            logging.info("Sentry hata raporlama etkinlestirildi.")
        except Exception as e:
            logging.error(f"Sentry baslatilirken hata olustu: {e}")

    def _install_exception_hook(self):
        """Yakalanmayan hatalari log dosyasina yazmak icin kancayi kurar."""
        def _handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logging.critical("Yakalanmayan hata olustu", exc_info=(exc_type, exc_value, exc_traceback))
            if self.config_manager.get('settings.enable_sentry_reporting', False):
                try:
                    sentry_sdk.capture_exception(exc_value)
                except Exception:
                    pass

        sys.excepthook = _handle_exception

    def show_dashboard(self):
        """Ana dashboard penceresini gösterir."""
        try:
            if self.dashboard_window and self.dashboard_window.winfo_exists():
                # Override-redirect hatası önlemi
                try:
                    self.dashboard_window.deiconify()
                except tk.TclError:
                    # Pencere zaten görünür durumda
                    pass
                self.dashboard_window.lift()
                self.dashboard_window.focus_force()
            else:
                self.dashboard_window = ui.MainDashboardWindow(master=self.root, app_instance=self)
        except Exception as e:
            logging.error(f"Dashboard gösterilirken hata: {e}")
            # Fallback: basit bir mesaj penceresi
            try:
                tk.messagebox.showinfo("Bilgi", "Dashboard açılamadı, lütfen tekrar deneyin.")
            except:
                pass

    def _set_run_on_startup(self, enable):
        """Uygulamanın Windows başlangıcında çalışıp çalışmamasını ayarlar."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "Kognita"
        app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                if enable:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
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
        try:
            Thread(target=self.tracker_instance.start_tracking, daemon=True).start()
            Thread(target=self.goal_checker_loop, daemon=True).start()
            Thread(target=self.achievement_checker_loop, daemon=True).start()
            Thread(target=self.data_retention_loop, daemon=True).start() 
            logging.info("Arka plan iş parçacıkları başlatıldı.")
        except Exception as e:
            logging.error(f"Arka plan iş parçacıkları başlatılırken hata: {e}")

    def data_retention_loop(self):
        """Belirlenen sıklıkta eski kullanım loglarını temizler."""
        self.stop_event.wait(300) # Uygulama başlatıldıktan 5 dakika sonra başlasın
        while not self.stop_event.is_set():
            try:
                logging.info("Veri saklama politikası kontrolü yapılıyor...")
                days_to_keep = self.config_manager.get('settings.data_retention_days', 365)
                if days_to_keep >= 0: # 0, sonsuz sakla anlamına gelir
                    # Database fonksiyonunu güvenli çağır
                    if hasattr(database, 'delete_old_usage_logs'):
                        deleted_count = database.delete_old_usage_logs(days_to_keep)
                        if deleted_count > 0:
                            logging.info(f"{deleted_count} adet eski veri başarıyla temizlendi.")
                    else:
                        logging.warning("delete_old_usage_logs fonksiyonu bulunamadı.")
            except Exception as e:
                logging.error(f"Veri temizleme döngüsünde hata: {e}")
                if 'sentry_sdk' in globals():
                    sentry_sdk.capture_exception(e)
            
            self.stop_event.wait(24 * 3600) # Her 24 saatte bir kontrol et

    def achievement_checker_loop(self):
        """Periyodik olarak başarımları kontrol eder."""
        self.stop_event.wait(60) 
        while not self.stop_event.is_set():
            try:
                logging.info("Başarım kontrolü yapılıyor...")
                if hasattr(achievement_checker, 'check_all_achievements'):
                    achievement_checker.check_all_achievements() 
                else:
                    logging.warning("check_all_achievements fonksiyonu bulunamadı.")
            except Exception as e:
                logging.error(f"Başarım kontrol döngüsünde hata: {e}")
                if 'sentry_sdk' in globals():
                    sentry_sdk.capture_exception(e) 
            
            self.stop_event.wait(3600) 

    def goal_checker_loop(self):
        """Periyodik olarak hedefleri kontrol eder."""
        checked_goals_today = set()
        while not self.stop_event.is_set():
            try:
                notification_settings = self.config_manager.get('settings.notification_settings', {})
                if not notification_settings.get('enable_goal_notifications', True):
                    self.stop_event.wait(900)
                    continue

                now = datetime.datetime.now()
                if now.hour == 0 and now.minute < 5:
                    checked_goals_today.clear()

                # Database fonksiyonunu güvenli çağır
                if not hasattr(database, 'get_goals'):
                    logging.warning("get_goals fonksiyonu bulunamadı.")
                    self.stop_event.wait(900)
                    continue
                    
                goals = database.get_goals()
                if not goals:
                    self.stop_event.wait(900)
                    continue
                
                start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Analyzer fonksiyonunu güvenli çağır
                if hasattr(analyzer, 'get_analysis_data'):
                    category_totals_today, _ = analyzer.get_analysis_data(start_of_day, now)
                else:
                    logging.warning("get_analysis_data fonksiyonu bulunamadı.")
                    category_totals_today = {}
                
                current_process_name, _ = self.tracker_instance._get_active_process_info()
                
                for goal in goals:
                    goal_id = goal.get('id')
                    if goal_id in checked_goals_today and goal.get('goal_type') not in ('block', 'time_window_max'):
                        continue
                    
                    goal_type = goal.get('goal_type')
                    category = goal.get('category')
                    process_name_target = goal.get('process_name')
                    time_limit_min = goal.get('time_limit_minutes')
                    start_time_str = goal.get('start_time_of_day')
                    end_time_str = goal.get('end_time_of_day')

                    if goal_type == 'max_usage' and category and time_limit_min is not None:
                        usage_minutes = category_totals_today.get(category, 0) / 60
                        if usage_minutes > time_limit_min:
                            self.show_notification(
                                loc.get('goal_exceeded_title'), 
                                loc.get('goal_exceeded_message', category=category, limit=time_limit_min),
                                notification_type="goal_exceeded"
                            )
                            checked_goals_today.add(goal_id)
                    
                    elif goal_type == 'min_usage' and category and time_limit_min is not None:
                         usage_minutes = category_totals_today.get(category, 0) / 60
                         if usage_minutes >= time_limit_min:
                            self.show_notification(
                                loc.get('goal_achieved_title'), 
                                loc.get('goal_achieved_message', category=category, limit=time_limit_min), 
                                notification_type="goal_completed"
                            )
                            checked_goals_today.add(goal_id)

                    elif goal_type == 'time_window_max' and category and time_limit_min is not None and start_time_str and end_time_str:
                        try:
                            start_hour, start_minute = [int(x) for x in start_time_str.split(":")]
                            end_hour, end_minute = [int(x) for x in end_time_str.split(":")]
                            window_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                            window_end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

                            if window_start <= now <= window_end:
                                window_totals, _ = analyzer.get_analysis_data(window_start, now)
                                usage_minutes = window_totals.get(category, 0) / 60
                                if usage_minutes > time_limit_min:
                                    self.show_notification(
                                        loc.get('goal_exceeded_title'), 
                                        loc.get('goal_exceeded_message', category=category, limit=time_limit_min),
                                        notification_type="goal_exceeded"
                                    )
                                    checked_goals_today.add(goal_id)
                        except Exception as inner_error:
                            logging.error(f"Zaman aralığı hedefi kontrolünde hata: {inner_error}")

                    elif goal_type == 'block' and process_name_target:
                        if current_process_name and current_process_name.lower() == process_name_target.lower():
                            now_ts = time.time()
                            last_sent = self.last_block_notification_times.get(process_name_target.lower(), 0)
                            if now_ts - last_sent >= 300:
                                self.show_notification(
                                    loc.get('blocked_app_title'), 
                                    loc.get('blocked_app_message', app=process_name_target), 
                                    timeout=5, 
                                    notification_type="goal_block"
                                )
                                self.last_block_notification_times[process_name_target.lower()] = now_ts

            except Exception as e:
                logging.error(f"Hedef kontrol döngüsünde hata: {e}")
                if 'sentry_sdk' in globals():
                    sentry_sdk.capture_exception(e)
            
            self.stop_event.wait(900)

    def start_focus_session_flow(self):
        """Odaklanma oturumu ayar penceresini açar."""
        try:
            if self.focus_session_active:
                if hasattr(ui, 'messagebox'):
                    ui.messagebox.showinfo(loc.get("focus_active_title"), loc.get("focus_active_message"))
                else:
                    tk.messagebox.showinfo(loc.get("focus_active_title"), loc.get("focus_active_message"))
                return
            
            if hasattr(ui, 'FocusSetupWindow'):
                ui.FocusSetupWindow(master=self.root, on_start_callback=self.start_focus_session)
            else:
                logging.error("FocusSetupWindow sınıfı bulunamadı.")
        except Exception as e:
            logging.error(f"Odaklanma oturumu penceresi açılırken hata: {e}")

    def start_focus_session(self, duration_minutes, allowed_categories):
        """Verilen parametrelerle odaklanma oturumunu bir thread'de başlatır."""
        try:
            if not self.focus_session_active:
                logging.info(f"{duration_minutes} dakikalık odaklanma oturumu başlatıldı. İzin verilen kategoriler: {allowed_categories}")
                self.focus_session_active = True
                self.update_tray_icon()
                Thread(target=self._focus_session_loop, args=(duration_minutes, allowed_categories), daemon=True).start()
        except Exception as e:
            logging.error(f"Odaklanma oturumu başlatılırken hata: {e}")

    def _focus_session_loop(self, duration_minutes, allowed_categories):
        """Odaklanma oturumunun arka plan döngüsü."""
        try:
            end_time = time.time() + duration_minutes * 60
            notification_settings = self.config_manager.get('settings.notification_settings', {})
            enable_focus_notifications = notification_settings.get('enable_focus_notifications', True)
            focus_notification_frequency = notification_settings.get('focus_notification_frequency_seconds', 300)
            last_focus_notification_time = time.time() - focus_notification_frequency 

            self.show_notification(
                loc.get("focus_started_title"), 
                loc.get("focus_started_message", duration=duration_minutes), 
                notification_type="focus_start"
            )

            while time.time() < end_time and not self.stop_event.is_set():
                try:
                    if enable_focus_notifications:
                        current_time = time.time()
                        process_name, _ = self.tracker_instance._get_active_process_info()
                        
                        if process_name not in ('idle', 'unknown'):
                            # Database fonksiyonunu güvenli çağır
                            if hasattr(database, 'get_category_for_process'):
                                category = database.get_category_for_process(process_name)
                                if category not in allowed_categories:
                                    if (current_time - last_focus_notification_time) >= focus_notification_frequency:
                                        self.show_notification(
                                            loc.get("focus_distraction_title"), 
                                            loc.get("focus_distraction_message", app=process_name), 
                                            timeout=5, 
                                            notification_type="focus_distraction"
                                        )
                                        last_focus_notification_time = current_time
                except Exception as e:
                    logging.error(f"Odaklanma döngüsünde hata: {e}")
                
                self.stop_event.wait(10) 

            if not self.stop_event.is_set():
                self.show_notification(
                    loc.get("focus_ended_title"), 
                    loc.get("focus_ended_message", duration=duration_minutes), 
                    notification_type="focus_end"
                )
        except Exception as e:
            logging.error(f"Odaklanma oturumu döngüsünde hata: {e}")
        finally:
            self.focus_session_active = False
            self.update_tray_icon()

    def show_notification(self, title, message, timeout=10, notification_type="info"):
        """Merkezi bildirim fonksiyonu. Ayarları okur ve geçmişe kaydeder."""
        try:
            from plyer import notification
            
            notification_settings = self.config_manager.get('settings.notification_settings', {})
            
            if notification_type == "achievement" and not notification_settings.get('show_achievement_notifications', True): 
                return
            if notification_type.startswith("goal_") and not notification_settings.get('enable_goal_notifications', True): 
                return
            if notification_type.startswith("focus_") and not notification_settings.get('enable_focus_notifications', True): 
                return

            # Database fonksiyonunu güvenli çağır
            if hasattr(database, 'add_notification'):
                database.add_notification(title, message, notification_type)
            
            icon_path = resource_path('icon.ico')
            if not os.path.exists(icon_path):
                icon_path = None  # Icon yoksa None olarak gönder
                
            notification.notify(
                title=title, 
                message=message, 
                app_name=loc.get('app_title'), 
                app_icon=icon_path, 
                timeout=timeout
            )
        except Exception as e:
            logging.error(f"Bildirim gönderilemedi: {e}")

    def update_tray_icon(self):
        """Sistem tepsisi menüsünü günceller."""
        try:
            if self.icon:
                self.icon.menu = self.setup_tray_menu()
        except Exception as e:
            logging.error(f"Tray icon güncelleme hatası: {e}")

    def setup_tray_menu(self):
        """Sistem tepsisi menüsünü oluşturur."""
        try:
            focus_text = loc.get("tray_stop_focus") if self.focus_session_active else loc.get("tray_start_focus")
            
            # Database fonksiyonunu güvenli çağır
            notification_count = 0
            if hasattr(database, 'get_unread_notification_count'):
                try:
                    notification_count = database.get_unread_notification_count()
                except:
                    notification_count = 0
            
            notification_text = f"{loc.get('tray_notifications')} ({notification_count})" if notification_count > 0 else loc.get('tray_notifications')
            
            menu_items = [
                pystray.MenuItem(loc.get("tray_show_dashboard"), self.show_dashboard, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(focus_text, self.start_focus_session_flow),
                pystray.Menu.SEPARATOR,
            ]
            
            # UI sınıflarının varlığını kontrol et ve menüye ekle
            if hasattr(ui, 'ReportWindow'):
                menu_items.append(pystray.MenuItem(loc.get("tray_reports"), lambda: ui.ReportWindow(master=self.root)))
            if hasattr(ui, 'GoalsWindow'):
                menu_items.append(pystray.MenuItem(loc.get("tray_goals"), lambda: ui.GoalsWindow(master=self.root)))
            if hasattr(ui, 'CategoryManagementWindow'):
                menu_items.append(pystray.MenuItem(loc.get("tray_categories"), lambda: ui.CategoryManagementWindow(master=self.root)))
            if hasattr(ui, 'NotificationHistoryWindow'):
                menu_items.append(pystray.MenuItem(notification_text, lambda: ui.NotificationHistoryWindow(master=self.root, app_instance=self)))
            if hasattr(ui, 'AchievementWindow'):
                menu_items.append(pystray.MenuItem(loc.get("tray_achievements"), lambda: ui.AchievementWindow(master=self.root)))
            if hasattr(ui, 'SettingsWindow'):
                menu_items.append(pystray.MenuItem(loc.get("tray_settings"), lambda: ui.SettingsWindow(master=self.root, app_instance=self)))
            
            menu_items.extend([
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(loc.get("tray_exit"), self.exit_action)
            ])
            
            return pystray.Menu(*menu_items)
        except Exception as e:
            logging.error(f"Tray menü oluşturma hatası: {e}")
            # Minimal menü döndür
            return pystray.Menu(
                pystray.MenuItem(loc.get("tray_show_dashboard"), self.show_dashboard, default=True),
                pystray.MenuItem(loc.get("tray_exit"), self.exit_action)
            )

    def run_tray_icon(self):
        """Sistem tepsisi ikonunu çalıştırır."""
        try:
            icon_path = resource_path("icon.png")
            if not os.path.exists(icon_path):
                # Fallback: Basit bir icon oluştur
                from PIL import Image, ImageDraw
                image = Image.new('RGB', (64, 64), color='blue')
                draw = ImageDraw.Draw(image)
                draw.text((16, 16), "K", fill='white')
            else:
                image = Image.open(icon_path)
                
            self.icon = pystray.Icon("Kognita", image, loc.get("app_title"), self.setup_tray_menu())
            self.icon.run()
        except Exception as e:
            logging.error(f"Tray icon çalıştırılırken hata: {e}")

    def exit_action(self):
        """Uygulamadan güvenli çıkış yapar."""
        try:
            logging.info("Çıkış işlemi başlatıldı...")
            self.stop_event.set()
            if self.icon: 
                self.icon.stop()
            if self.dashboard_window:
                try:
                    self.dashboard_window.destroy()
                except:
                    pass
            self.root.quit()
        except Exception as e:
            logging.error(f"Çıkış işleminde hata: {e}")
            # Force exit
            sys.exit(0)

    def on_welcome_closed(self):
        """'first_run' bayrağını günceller."""
        try:
            self.config_manager.set('app_state.first_run', False)
        except Exception as e:
            logging.error(f"Welcome kapatma ayarı güncelleme hatası: {e}")

    def run(self):
        """Uygulamanın ana döngüsünü başlatır."""
        try:
            logging.info("Uygulama başlatılıyor...")
            
            # Veritabanı zaten constructor'da başlatıldı, tekrar kontrol et
            try:
                database.initialize_database()
            except Exception as e:
                logging.error(f"Veritabanı tekrar başlatma hatası: {e}")

            # First run kontrolü
            try:
                if self.config_manager.get('app_state.first_run', True):
                    if hasattr(ui, 'WelcomeWindow'):
                        welcome = ui.WelcomeWindow(master=self.root, on_close_callback=self.on_welcome_closed)
                        self.root.wait_window(welcome)
                    else:
                        logging.warning("WelcomeWindow sınıfı bulunamadı.")
                        self.on_welcome_closed()  # İlk çalıştırma bayrağını yine de güncelle
            except Exception as e:
                logging.error(f"Welcome window hatası: {e}")
                self.on_welcome_closed()
            
            if not self.stop_event.is_set(): 
                # UI stillerini uygula
                try:
                    if hasattr(ui, 'apply_global_styles'):
                        ui.apply_global_styles()
                except Exception as e:
                    logging.error(f"UI stili uygulama hatası: {e}")
                
                self.start_background_threads()
                
                tray_thread = Thread(target=self.run_tray_icon, daemon=True)
                tray_thread.start()

                self.show_dashboard()
                self.root.mainloop()
            
            logging.info("Uygulama sonlandırıldı.")
            
        except Exception as e:
            logging.error(f"Ana çalıştırma döngüsünde kritik hata: {e}")
            if 'sentry_sdk' in globals():
                sentry_sdk.capture_exception(e)
            # Fallback: Minimal çalışma modu
            try:
                self.root.mainloop()
            except:
                sys.exit(1)

if __name__ == "__main__":
    try:
        app = KognitaApp()
        app.run()
    except Exception as e:
        logging.error(f"Uygulama başlatılırken kritik hata: {e}")
        print(f"KRITIK HATA: {e}")
        input("Devam etmek için Enter tuşuna basın...")
        sys.exit(1)
