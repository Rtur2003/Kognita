# kognita/tracker.py

import psutil
import time
import win32process
import win32gui
from threading import Thread, Event
from pynput import mouse, keyboard
from .database import get_db_connection

# Bu global değişken, main.py tarafından kontrol edilecek
stop_flag = Event()

POLL_INTERVAL = 3
IDLE_THRESHOLD_SECONDS = 180
last_activity_time = time.time()

def on_activity():
    """Updates the last activity time whenever mouse or keyboard is used."""
    global last_activity_time
    last_activity_time = time.time()

def on_move(x, y): on_activity()
def on_click(x, y, button, pressed): on_activity()
def on_scroll(x, y, dx, dy): on_activity()
def on_press(key): on_activity()

def start_listeners():
    """Starts mouse and keyboard listeners in separate threads."""
    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener.daemon = True
    keyboard_listener.daemon = True
    mouse_listener.start()
    keyboard_listener.start()
    print("Activity listeners started.")

def get_active_process_info():
    """Gets the process name and window title of the currently active window."""
    if time.time() - last_activity_time > IDLE_THRESHOLD_SECONDS:
        return 'idle', 'User is Idle'
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd: return 'idle', 'No active window'
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == 0: return 'unknown', 'Unknown'
        process = psutil.Process(pid)
        return process.name().lower(), win32gui.GetWindowText(hwnd)
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return 'unknown', 'Unknown'

def log_activity(conn, process_name, title, start_time, end_time):
    """Logs the concluded activity session to the database."""
    duration = int(end_time - start_time)
    if duration < POLL_INTERVAL or process_name in ['idle', 'unknown']:
        return
            
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usage_log (process_name, window_title, start_time, end_time, duration_seconds) VALUES (?, ?, ?, ?, ?)",
        (process_name, title, int(start_time), int(end_time), duration)
    )
    conn.commit()
    print(f"Logged: {process_name} - {duration}s - {title[:30]}")

def start_tracking():
    """Starts the main activity tracking loop."""
    start_listeners()
    print("Kognita Tracker is active.")
    
    last_process_name, last_window_title = get_active_process_info()
    session_start_time = time.time()

    try:
        while not stop_flag.is_set():
            current_process_name, current_window_title = get_active_process_info()
            
            if current_process_name != last_process_name or current_window_title != last_window_title:
                session_end_time = time.time()
                with get_db_connection() as conn:
                    if conn:
                        log_activity(conn, last_process_name, last_window_title, session_start_time, session_end_time)
                
                session_start_time = time.time()
                # --- DÜZELTİLEN KISIM BURASI ---
                last_process_name = current_process_name
                last_window_title = current_window_title
            
            stop_flag.wait(POLL_INTERVAL)
            
    finally:
        print("\nStopping Kognita Tracker...")
        if last_process_name is not None:
            final_end_time = time.time()
            with get_db_connection() as conn:
                if conn:
                    log_activity(conn, last_process_name, last_window_title, session_start_time, final_end_time)
        print("Tracker thread stopped gracefully.")