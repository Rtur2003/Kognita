# Kognita ✨

*The Art of Understanding Your Digital Footprint.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Kognita is a silent, local-first desktop activity tracker that helps you understand how you spend your time on the computer. It's not a surveillance tool, but a personal analytics engine designed for self-awareness and productivity. All your data stays on your machine.

## Features

-   🤫 **Silent Background Tracking:** Runs quietly in the background without interrupting your workflow.
-   📊 **Activity Categorization:** Automatically categorizes your applications into buckets like "Work", "Gaming", "Development", "Design", etc.
-   🧠 **Persona Analysis:** Analyzes your usage patterns to assign you a "digital persona" (e.g., "The Focused Gamer", "The Productivity Guru").
-   🔒 **Privacy First:** All data is stored locally in a SQLite database. Nothing is ever sent to the cloud.
-   💻 **Cross-Platform (WIP):** Currently focused on Windows, with plans to support macOS and Linux.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Rtur2003/Kognita.git](https://github.com/Rtur2003/Kognita.git)
    cd Kognita
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Kognita has two main components: the tracker and the reporter.

1.  **Run the Tracker:**
    This script will run in your terminal and start logging your active window usage. Let it run for a while to gather data.
    ```bash
    python kognita/tracker.py
    ```

2.  **Generate a Report:**
    Once you have some data, you can generate a report for the last 24 hours.
    ```bash
    python kognita/reporter.py
    ```

## How to Contribute

Contributions are welcome! Please read our `CONTRIBUTING.md` file to learn how you can help improve Kognita.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
