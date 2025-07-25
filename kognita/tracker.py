# kognita/tracker.py
import psutil
import time
import win32process
import win32gui
import logging
from threading import Event
from pynput import mouse, keyboard
from .database import get_db_connection

class Tracker:
    """
    Handles tracking of active window, user activity (mouse/keyboard),
    and logs the data to the database.
    """
    def __init__(self, config):
        self.stop_flag = Event()
        self.config = config
        self.poll_interval = 3  # seconds
        self.idle_threshold_seconds = 180
        self.last_activity_time = time.time()
        
        self.update_settings(config)

    def update_settings(self, config):
        """Updates tracker settings from the config object."""
        self.config = config
        self.idle_threshold_seconds = self.config.get('settings', {}).get('idle_threshold_seconds', 180)
        logging.info(f"Tracker settings updated: Idle threshold set to {self.idle_threshold_seconds}s")

    def _on_activity(self):
        """Callback function for any user activity."""
        self.last_activity_time = time.time()

    def _start_listeners(self):
        """Starts mouse and keyboard listeners in daemon threads."""
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
        logging.info("Activity listeners started.")

    def _get_active_process_info(self):
        """
        Gets the process name and window title of the foreground window.
        Returns 'idle' if the user is idle.
        """
        if time.time() - self.last_activity_time > self.idle_threshold_seconds:
            return 'idle', 'User is Idle'
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return 'idle', 'No active window'
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == 0:
                # This can happen for some system processes
                return 'unknown', 'Unknown Process'

            process = psutil.Process(pid)
            process_name = process.name().lower()
            window_title = win32gui.GetWindowText(hwnd)
            
            return process_name, window_title
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process might have closed between getting pid and querying it
            return 'unknown', 'Unknown'
        except Exception as e:
            logging.error(f"Error getting active process info: {e}", exc_info=True)
            return 'unknown', 'Error'

    def _log_activity(self, conn, process_name, title, start_time, end_time):
        """Logs a single activity session to the database."""
        duration = int(end_time - start_time)
        if duration < self.poll_interval or process_name in ['idle', 'unknown']:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usage_log (process_name, window_title, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?, ?)",
                (process_name, title, int(start_time), int(end_time), duration)
            )
            conn.commit()
            logging.info(f"Logged: {process_name} - {duration}s - {title[:30]}")
        except Exception as e:
            logging.error(f"Failed to log activity to DB: {e}")

    def start_tracking(self):
        """Main tracking loop."""
        self._start_listeners()
        logging.info("Kognita Tracker is now active.")
        
        last_process_name, last_window_title = self._get_active_process_info()
        session_start_time = time.time()
        
        try:
            while not self.stop_flag.is_set():
                current_process_name, current_window_title = self._get_active_process_info()
                
                if current_process_name != last_process_name or current_window_title != last_window_title:
                    session_end_time = time.time()
                    with get_db_connection() as conn:
                        if conn:
                            self._log_activity(conn, last_process_name, last_window_title, session_start_time, session_end_time)
                    
                    session_start_time = time.time()
                    last_process_name = current_process_name
                    last_window_title = current_window_title
                
                self.stop_flag.wait(self.poll_interval)
        finally:
            logging.info("Stopping Kognita Tracker...")
            # Log the final session before exiting
            if last_process_name is not None:
                final_end_time = time.time()
                with get_db_connection() as conn:
                    if conn:
                        self._log_activity(conn, last_process_name, last_window_title, session_start_time, final_end_time)
            logging.info("Tracker thread stopped gracefully.")

