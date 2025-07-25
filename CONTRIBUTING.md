
-----

# Kognita - Developer & Contribution Guide

First off, thank you for considering contributing to Kognita\! This guide details the project's structure, explains how to set up your development environment, and provides instructions for common development tasks and troubleshooting.

## Project Philosophy

Kognita is built on a few core principles:

  * **Modularity:** Each component has a single, well-defined responsibility.
  * **Privacy-First:** All user data must remain local. No network calls should be introduced that transmit user activity.
  * **Low Overhead:** The application must be lightweight and have a minimal impact on system performance.

## Code Architecture Overview

To contribute effectively, it's important to understand the role of each key file in the project.

  * **`main.py` - The Orchestrator**

      * **What it does:** This is the application's entry point. It's responsible for starting background threads, building the system tray icon and menu (`pystray`), and launching the GUI windows (`tkinter`).
      * **When to look here:** If you want to change the system tray menu, modify how windows are launched, or manage the main application threads.

  * **`kognita/tracker.py` - The Data Collector**

      * **What it does:** This module is the heart of the data collection process. It runs in a background thread, uses `pynput` for idle detection, and `win32gui`/`psutil` to identify the active application. It writes raw data to the database.
      * **When to look here:** If you want to improve the accuracy of activity tracking, change the idle detection logic, or add more detail to the logged data (e.g., tracking window titles more intelligently).

  * **`kognita/database.py` - The Data Layer**

      * **What it does:** Manages all interactions with the `kognita_data.db` SQLite database. It defines the table schemas and provides functions for creating, reading, and deleting records (`usage_log`, `goals`, etc.).
      * **When to look here:** If you need to add a new table to the database, store a new type of data, or write a new query to retrieve specific information.

  * **`kognita/analyzer.py` - The Brains**

      * **What it does:** This is a pure logic module. It takes raw data from the database, processes it into meaningful information (e.g., time per category), checks usage against user-defined goals, and determines the "Digital Persona." It has no UI or system dependencies.
      * **When to look here:** If you want to change the rules for the Digital Persona, add new types of analysis, or implement the logic for checking goals and triggering notifications.

  * **`kognita/reporter.py` - The Presentation Layer**

      * **What it does:** Formats the analyzed data from `analyzer.py` into a human-readable string for display in the GUI or console.
      * **When to look here:** If you want to change the text format of the report that appears in the `tkinter` window.

## Setting up the Development Environment

1.  **Fork & Clone:** Fork the repository on GitHub and then clone your fork locally.
    ```bash
    git clone https://github.com/YOUR_USERNAME/Kognita.git
    cd Kognita
    ```
2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the App:**
    ```bash
    python main.py
    ```

## How to Add or Modify Features

Here are guides for common modification scenarios.

### Scenario 1: Adding a New Application to a Category

This is the easiest way to contribute. If Kognita is categorizing an application as "Other" and you know its category, you can add it.

1.  **Find the Process Name:** You can find the process name from the Kognita report window or by using the Task Manager in Windows. It must end with `.exe`.
2.  **Edit `database.py`:** Open `kognita/database.py`.
3.  **Add to Dictionary:** Find the `_populate_initial_categories` function and add a new entry to the `categories` dictionary. For example, to add a new design tool:
    ```python
    categories = {
        # ... existing entries
        "figma.exe": "Design",
        "adobexd.exe": "Design", # <-- Add your new line here
        "vlc.exe": "Media",
        # ... other entries
    }
    ```
4.  **Test:** Delete your local `kognita_data.db` file and run `python main.py` to ensure the database initializes correctly with your new entry.

### Scenario 2: Modifying the Goal Checking Logic

Let's say you want to change the goal checking frequency from 15 minutes to 30 minutes.

1.  **Locate the Logic:** The goal checking loop is managed by a background thread. This thread is defined and started in `main.py`.
2.  **Edit `main.py`:** Open `main.py` and find the `goal_checker_thread` function.
3.  **Change the Value:** At the end of the function, find the line `tracker.stop_flag.wait(900)`. The number `900` is the wait time in seconds (15 minutes). Change it to `1800` for 30 minutes.
    ```python
    # Check every 30 minutes
    tracker.stop_flag.wait(1800)
    ```

## Troubleshooting Common Issues

  * **Problem:** The `.exe` created by `PyInstaller` crashes on startup or fails with a "silent crash."

      * **Where to look:** This is almost always a "hidden import" or a pathing issue.
      * **Solution:**
        1.  Ensure you are using the `resource_path` function in `main.py` to access all asset files (like `icon.png` and `icon.ico`).
        2.  Re-build the `.exe` *without* the `--windowed` flag. This will open a console window when the `.exe` runs.
        3.  Run the console-based `.exe`. The error message that appears in the console before it closes is the key to debugging.
        4.  If the error is a `ModuleNotFoundError` for a library that should be included (especially a part of `pynput`, `pywin32`, etc.), add it to the `pyinstaller` command using the `--hidden-import=modulename` flag.

  * **Problem:** The tracker is not logging any activity or logs everything as "Unknown."

      * **Where to look:** The issue is likely in the `get_active_process_info` function within `kognita/tracker.py`.
      * **Solution:**
        1.  This can be a permissions issue. Try running your development environment (e.g., your terminal or VS Code) as an Administrator to see if it resolves the problem.
        2.  Add `print()` statements inside the `try...except` block in `get_active_process_info` to see what kind of exception is being caught. This will help diagnose if it's a `psutil.AccessDenied` error or something else.

  * **Problem:** I've added a new table to `database.py`, but the application isn't seeing it.

      * **Where to look:** The `initialize_database` function in `kognita/database.py` is designed to not overwrite an existing database.
      * **Solution:** During development, the easiest solution is to **delete your local `kognita_data.db` file**. The next time you run `python main.py`, the `initialize_database` function will run completely, creating a fresh database with your new table schema.