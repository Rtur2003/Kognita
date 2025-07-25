# main.py

import pystray
from PIL import Image
from threading import Thread, Event
import tkinter as tk
from tkinter import scrolledtext, messagebox, Listbox, OptionMenu, StringVar, Frame, Label, Entry, Button
import sys
import os
import time
from plyer import notification
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from kognita import tracker, reporter, database, analyzer

CATEGORIES = sorted([
    "Office", "Communication", "Development", "System", "Design",
    "Video", "Media", "Music", "Web", "Social", "Gaming", "Gaming Platform", "Other"
])

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def show_report_window():
    """Creates a Tkinter window with a graphical report (pie chart)."""
    category_totals, total_duration = analyzer.get_analysis_data(days=1)
    
    window = tk.Tk()
    window.title("Kognita - Activity Report (Last 24 Hours)")
    window.geometry("600x650")
    window.resizable(False, False)
    try: window.iconbitmap(resource_path("icon.ico"))
    except: print("Could not load window icon.")

    if not category_totals or total_duration == 0:
        Label(window, text="\nNot enough data to generate a report.\n\nLet Kognita run for a while to collect data.", font=("Helvetica", 12)).pack(pady=20)
        window.mainloop()
        return

    # Matplotlib Figure
    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)
    
    labels = category_totals.keys()
    sizes = category_totals.values()
    
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title("Time Distribution by Category")

    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Summary Text
    summary_text = reporter.get_report_as_string(days=1)
    summary_label = Label(window, text=summary_text, font=("Courier New", 9), justify=tk.LEFT)
    summary_label.pack(pady=10)

    window.mainloop()

def show_goals_window():
    # Bu fonksiyon önceki haliyle aynı, bir değişiklik yok
    goals_window = tk.Tk()
    goals_window.title("Manage Goals")
    goals_window.geometry("400x400")
    goals_window.resizable(False, False)
    try: goals_window.iconbitmap(resource_path("icon.ico"))
    except: print("Could not load window icon for goals.")

    Label(goals_window, text="Current Goals:", font=("Helvetica", 12, "bold")).pack(pady=(10,0))
    list_frame = Frame(goals_window)
    list_frame.pack(pady=5, padx=10, fill="x")
    goals_listbox = Listbox(list_frame, height=8)
    goals_listbox.pack(side="left", fill="x", expand=True)

    def refresh_goals_list():
        goals_listbox.delete(0, tk.END)
        goals = database.get_goals()
        for goal in goals:
            goal_id, category, goal_type, time_limit = goal
            goal_text = f"[{goal_id}] {category}: {goal_type.capitalize()} {time_limit} minutes/day"
            goals_listbox.insert(tk.END, goal_text)

    add_frame = Frame(goals_window, pady=10)
    add_frame.pack(pady=10, padx=10)
    Label(add_frame, text="Add New Goal:", font=("Helvetica", 12, "bold")).grid(row=0, columnspan=2, sticky="w")
    Label(add_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    category_var = StringVar(goals_window); category_var.set(CATEGORIES[0])
    OptionMenu(add_frame, category_var, *CATEGORIES).grid(row=1, column=1, sticky="ew")
    Label(add_frame, text="Type:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    type_var = StringVar(goals_window); type_var.set("Max")
    OptionMenu(add_frame, type_var, "Max", "Min").grid(row=2, column=1, sticky="ew")
    Label(add_frame, text="Time (minutes):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
    time_entry = Entry(add_frame, width=10)
    time_entry.grid(row=3, column=1, sticky="w")

    def add_new_goal():
        try:
            database.add_goal(category_var.get(), type_var.get().lower(), int(time_entry.get()))
            refresh_goals_list()
            time_entry.delete(0, tk.END)
        except ValueError: messagebox.showerror("Invalid Input", "Please enter a valid number for time.")
    def delete_selected_goal():
        selected = goals_listbox.get(tk.ACTIVE)
        if not selected: messagebox.showwarning("No Selection", "Please select a goal to delete.")
        else:
            goal_id = int(selected.split(']')[0][1:])
            database.delete_goal(goal_id)
            refresh_goals_list()

    button_frame = Frame(goals_window); button_frame.pack(pady=10)
    Button(add_frame, text="Add Goal", command=add_new_goal).grid(row=4, columnspan=2, pady=10)
    Button(button_frame, text="Delete Selected", command=delete_selected_goal).pack()
    refresh_goals_list()
    goals_window.mainloop()

def goal_checker_thread():
    """Periodically checks if any goals have been met or exceeded."""
    checked_goals_today = set()
    while not tracker.stop_flag.is_set():
        goals = database.get_goals()
        if not goals:
            tracker.stop_flag.wait(3600) # Check once an hour if no goals are set
            continue

        category_totals, _ = analyzer.get_analysis_data(days=1)
        
        for goal_id, category, goal_type, time_limit_min in goals:
            if goal_id in checked_goals_today:
                continue

            usage_seconds = category_totals.get(category, 0)
            usage_minutes = usage_seconds / 60

            if goal_type == 'max' and usage_minutes > time_limit_min:
                notification.notify(
                    title='Kognita - Goal Exceeded',
                    message=f'You have exceeded your daily limit of {time_limit_min} minutes for {category}.',
                    app_name='Kognita',
                    app_icon=resource_path('icon.ico')
                )
                checked_goals_today.add(goal_id)
            elif goal_type == 'min' and usage_minutes >= time_limit_min:
                notification.notify(
                    title='Kognita - Goal Achieved!',
                    message=f'Congratulations! You have reached your daily goal of {time_limit_min} minutes for {category}.',
                    app_name='Kognita',
                    app_icon=resource_path('icon.ico')
                )
                checked_goals_today.add(goal_id)

        # Check every 15 minutes
        tracker.stop_flag.wait(900)

def exit_action(icon, item):
    tracker.stop_flag.set()
    icon.stop()

def run_background_threads():
    tracker_thread = Thread(target=tracker.start_tracking, daemon=True)
    tracker_thread.start()

    goal_checker = Thread(target=goal_checker_thread, daemon=True)
    goal_checker.start()

def setup_and_run_tray_icon():
    try: image = Image.open(resource_path("icon.png"))
    except FileNotFoundError: messagebox.showerror("Error", "icon.png not found!")
    else:
        menu = (pystray.MenuItem('Show Report', show_report_window, default=True),
                pystray.MenuItem('Manage Goals', show_goals_window),
                pystray.MenuItem('Exit', exit_action))
        icon = pystray.Icon("Kognita", image, "Kognita Activity Tracker", menu)
        icon.run()

if __name__ == "__main__":
    database.initialize_database()
    run_background_threads()
    setup_and_run_tray_icon()