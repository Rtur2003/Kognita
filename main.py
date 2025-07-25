# main.py

import pystray
from PIL import Image
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext
import sys # YENİ
import os  # YENİ

# Kognita modüllerimizi import ediyoruz
from kognita import tracker, reporter, database

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def show_report_window():
    """Creates a simple Tkinter window to display the report."""
    report_string = reporter.get_report_as_string(days=1)

    window = tk.Tk()
    window.title("Kognita - Activity Report (Last 24 Hours)")
    window.geometry("600x450")
    window.resizable(False, False)
    
    # Pencere ikonunu ayarla
    try:
        window.iconbitmap(resource_path("icon.ico"))
    except:
        print("Could not load window icon.")


    txt_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=70, height=25, font=("Courier New", 9))
    txt_area.pack(padx=10, pady=10)
    
    txt_area.insert(tk.INSERT, report_string)
    txt_area.config(state='disabled')

    window.mainloop()

def exit_action(icon, item):
    """Stops the tracker thread and exits the application."""
    print("Exit command received. Stopping tracker...")
    tracker.stop_flag.set()
    icon.stop()
    print("Application exited.")

def run_tracker_in_background():
    """Runs the Kognita tracker in a separate, non-blocking thread."""
    print("Starting tracker in a background thread...")
    tracker_thread = Thread(target=tracker.start_tracking, daemon=True)
    tracker_thread.start()
    return tracker_thread

def setup_and_run_tray_icon():
    """Sets up and runs the system tray icon."""
    try:
        # YENİ: İkonu bulmak için resource_path fonksiyonunu kullanıyoruz
        image = Image.open(resource_path("icon.png"))
    except FileNotFoundError:
        print("Error: icon.png not found! The file must be in the same directory as main.py.")
        return

    menu = (pystray.MenuItem('Show Report', show_report_window, default=True),
            pystray.MenuItem('Exit', exit_action))

    icon = pystray.Icon("Kognita", image, "Kognita Activity Tracker", menu)
    
    print("Kognita is running in the system tray. Right-click the icon for options.")
    icon.run()

if __name__ == "__main__":
    database.initialize_database()
    run_tracker_in_background()
    setup_and_run_tray_icon()