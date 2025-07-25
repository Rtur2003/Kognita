# main.py

import pystray
from PIL import Image
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext, messagebox, Listbox, OptionMenu, StringVar, Frame, Label, Entry, Button
import sys
import os
import json
from plyer import notification
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from kognita import tracker, reporter, database, analyzer

CATEGORIES = sorted([
    "Office", "Communication", "Development", "System", "Design",
    "Video", "Media", "Music", "Web", "Social", "Gaming", "Gaming Platform", "Other"
])
CONFIG_FILE = "config.json"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_config():
    """Loads configuration from config.json, creates it if it doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        default_config = {"settings": {"idle_threshold_seconds": 180}, "app_state": {"first_run": True}}
        save_config(default_config)
        return default_config
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Saves configuration to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def show_report_window():
    category_totals, total_duration = analyzer.get_analysis_data(days=1)
    window = tk.Tk()
    window.title("Kognita - Activity Report (Last 24 Hours)")
    window.geometry("600x650")
    window.resizable(False, False)
    try: window.iconbitmap(resource_path("icon.ico"))
    except: print("Could not load window icon.")

    if not category_totals or total_duration == 0:
        Label(window, text="\nNot enough data to generate a report.\n\nLet Kognita run for a while to collect data.", font=("Helvetica", 12)).pack(pady=20)
    else:
        fig = Figure(figsize=(6, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(category_totals.values(), labels=category_totals.keys(), autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')
        ax.set_title("Time Distribution by Category")
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        summary_text = reporter.get_report_as_string(days=1)
        Label(window, text=summary_text, font=("Courier New", 9), justify=tk.LEFT).pack(pady=10)
    window.mainloop()

def show_goals_window():
    goals_window = tk.Tk()
    goals_window.title("Manage Goals")
    goals_window.geometry("400x400")
    goals_window.resizable(False, False)
    try: goals_window.iconbitmap(resource_path("icon.ico"))
    except: print("Could not load window icon for goals.")

    Label(goals_window, text="Current Goals:", font=("Helvetica", 12, "bold")).pack(pady=(10,0))
    list_frame = Frame(goals_window); list_frame.pack(pady=5, padx=10, fill="x")
    goals_listbox = Listbox(list_frame, height=8); goals_listbox.pack(side="left", fill="x", expand=True)

    def refresh_goals_list():
        goals_listbox.delete(0, tk.END)
        for goal in database.get_goals():
            goal_id, category, goal_type, time_limit = goal
            goals_listbox.insert(tk.END, f"[{goal_id}] {category}: {goal_type.capitalize()} {time_limit} minutes/day")

    add_frame = Frame(goals_window, pady=10); add_frame.pack(pady=10, padx=10)
    Label(add_frame, text="Add New Goal:", font=("Helvetica", 12, "bold")).grid(row=0, columnspan=2, sticky="w")
    Label(add_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    category_var = StringVar(goals_window); category_var.set(CATEGORIES[0])
    OptionMenu(add_frame, category_var, *CATEGORIES).grid(row=1, column=1, sticky="ew")
    Label(add_frame, text="Type:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    type_var = StringVar(goals_window); type_var.set("Max")
    OptionMenu(add_frame, type_var, "Max", "Min").grid(row=2, column=1, sticky="ew")
    Label(add_frame, text="Time (minutes):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
    time_entry = Entry(add_frame, width=10); time_entry.grid(row=3, column=1, sticky="w")

    def add_new_goal():
        try:
            database.add_goal(category_var.get(), type_var.get().lower(), int(time_entry.get()))
            refresh_goals_list(); time_entry.delete(0, tk.END)
        except ValueError: messagebox.showerror("Invalid Input", "Please enter a valid number for time.")
    def delete_selected_goal():
        selected = goals_listbox.get(tk.ACTIVE)
        if not selected: messagebox.showwarning("No Selection", "Please select a goal to delete.")
        else:
            database.delete_goal(int(selected.split(']')[0][1:])); refresh_goals_list()

    button_frame = Frame(goals_window); button_frame.pack(pady=10)
    Button(add_frame, text="Add Goal", command=add_new_goal).grid(row=4, columnspan=2, pady=10)
    Button(button_frame, text="Delete Selected", command=delete_selected_goal).pack()
    refresh_goals_list()
    goals_window.mainloop()

def show_settings_window():
    config = load_config()
    settings_window = tk.Tk()
    settings_window.title("Settings")
    settings_window.geometry("300x200")
    try: settings_window.iconbitmap(resource_path("icon.ico"))
    except: pass

    Label(settings_window, text="Idle Threshold (seconds):", font=("Helvetica", 10)).pack(pady=(10,0))
    idle_entry = Entry(settings_window, width=10)
    idle_entry.insert(0, config['settings']['idle_threshold_seconds'])
    idle_entry.pack(pady=5)

    def save_settings_action():
        try:
            new_idle_time = int(idle_entry.get())
            config['settings']['idle_threshold_seconds'] = new_idle_time
            save_config(config)
            tracker.update_settings(config) # Update the running tracker instantly
            messagebox.showinfo("Success", "Settings saved successfully! Restart may be needed for some changes.")
            settings_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for seconds.")

    Button(settings_window, text="Save Settings", command=save_settings_action).pack(pady=20)
    settings_window.mainloop()

def goal_checker_thread():
    checked_goals_today = set()
    while not tracker.stop_flag.is_set():
        tracker.stop_flag.wait(900)
        if tracker.stop_flag.is_set(): break

        goals = database.get_goals()
        if not goals: continue

        category_totals, _ = analyzer.get_analysis_data(days=1)
        for goal_id, category, goal_type, time_limit_min in goals:
            if goal_id in checked_goals_today: continue
            
            usage_minutes = category_totals.get(category, 0) / 60
            notification_sent = False
            if goal_type == 'max' and usage_minutes > time_limit_min:
                notification.notify(title='Kognita - Goal Exceeded!', message=f'You exceeded your daily limit of {time_limit_min} mins for {category}.', app_name='Kognita', app_icon=resource_path('icon.ico'), timeout=10)
                notification_sent = True
            elif goal_type == 'min' and usage_minutes >= time_limit_min:
                notification.notify(title='Kognita - Goal Achieved!', message=f'Congrats! You reached your daily goal of {time_limit_min} mins for {category}.', app_name='Kognita', app_icon=resource_path('icon.ico'), timeout=10)
                notification_sent = True
            
            if notification_sent:
                checked_goals_today.add(goal_id)

def exit_action(icon, item):
    tracker.stop_flag.set()
    icon.stop()

def run_background_threads():
    Thread(target=tracker.start_tracking, daemon=True).start()
    Thread(target=goal_checker_thread, daemon=True).start()
    print("Background threads (Tracker, Goal Checker) started.")

def setup_and_run_tray_icon(config):
    try: image = Image.open(resource_path("icon.png"))
    except FileNotFoundError: messagebox.showerror("Error", "icon.png not found!")
    else:
        menu = (pystray.MenuItem('Show Report', show_report_window, default=True),
                pystray.MenuItem('Manage Goals', show_goals_window),
                pystray.MenuItem('Settings', show_settings_window),
                pystray.MenuItem('Exit', exit_action))
        icon = pystray.Icon("Kognita", image, "Kognita Activity Tracker", menu)
        
        if config['app_state']['first_run']:
            def show_welcome():
                icon.notify("Welcome to Kognita! I'm now tracking your activity silently.", "Kognita")
                config['app_state']['first_run'] = False
                save_config(config)
            # Run welcome message in a separate thread to not block the icon
            Thread(target=show_welcome).start()

        icon.run()

if __name__ == "__main__":
    config = load_config()
    database.initialize_database()
    tracker.update_settings(config)
    run_background_threads()
    setup_and_run_tray_icon(config)