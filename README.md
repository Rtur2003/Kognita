# Kognita ✨

*The Art of Understanding Your Digital Footprint.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)](https://www.microsoft.com/windows/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)

Kognita is a silent, local-first, and privacy-focused desktop activity tracker that helps you understand how you spend your time on your computer. It's not a surveillance tool, but a personal analytics engine designed for self-awareness and productivity.

**All of your data is stored locally on your machine, encrypted with AES-256, and is never shared with anyone**.

![Kognita Dashboard](assets/main_dashboard_screenshot.png)

## ✨ Features

- 🤫 **Silent Background Tracking:** Runs quietly in the background without requiring a persistent terminal window.
- 🖱️ **Smart Idle Detection:** Intelligently detects when you're away from your keyboard and mouse, pausing the timer to ensure only active usage is logged.
- 🔒 **Privacy-First & Encryption:** All data is stored in a local SQLite database. The data is encrypted using **AES-256** with a machine-specific key, meaning the database file cannot be read on another computer.
- 📊 **Advanced Dashboard & Reporting:**
    - A modern **Dashboard** provides a daily summary, key metrics, and recent activities at a glance.
    - Generate detailed reports with custom date ranges (`Today`, `Last 7 Days`, `This Month`, etc.).
    - Visualize your data with interactive **pie charts, bar charts, and trend graphs**.
    - Export your raw data to **CSV** or generate a comprehensive analysis **PDF** report.
- 🎯 **Goal Management:** Set goals to improve your habits.
    - Set **maximum usage** limits for distracting categories (e.g., "Gaming < 2 hours").
    - Set **minimum usage** targets for productive categories (e.g., "Development > 3 hours").
    - **Block** specific applications entirely.
- 🚀 **Focus Mode:** Start a timed session where only applications in your chosen "allowed categories" can be used without triggering a notification, helping you stay on task.
- 🏆 **Achievements & Gamification:** Unlock achievements like "Productivity Guru" or "Weekend Warrior" based on your usage milestones to stay motivated.
- 🧠 **Digital Persona Analysis:** Kognita analyzes your usage patterns to assign you a fun "digital persona".
- 🌐 **Multi-Language Support:** The interface is available in both English and Turkish.
- 🧩 **System Tray Integration:** Lives in the Windows System Tray for minimal intrusion. A right-click menu provides quick access to all features.

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running.

### For End-Users (Recommended)

You do not need Python or any other tools to run the application.

1.  Go to the project's [**Releases Page**](https://github.com/Rtur2003/Kognita/releases).
2.  Download the `Kognita.exe` file from the latest release's "Assets" section.
3.  Run the downloaded executable file. That's it!

### For Developers

If you want to run the project from the source code or contribute to its development:

1.  **Prerequisites:**
    * [Python 3.10+](https://www.python.org/downloads/)
    * [Git](https://git-scm.com/downloads)

2.  **Installation & Setup:**
    ```bash
    # Clone the repository
    git clone [https://github.com/Rtur2003/Kognita.git](https://github.com/Rtur2003/Kognita.git)
    cd Kognita

    # Create and activate a virtual environment
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate

    # Install the required dependencies
    pip install -r requirements.txt
    ```

## 🖥️ Usage

1.  Run `Kognita.exe` (for users) or `python main.py` (for developers).
2.  The Kognita icon will appear in your system tray (the area in the bottom-right corner of your screen). The application will immediately start tracking your activity in the background.
3.  **Right-click** the tray icon to open the context menu and access all features:
    * **Show Dashboard:** Opens the main window with your daily summary, quick actions, and recent activity.
    * **Start Focus Session:** Opens the setup window to begin a timed focus session.
    * **Reports:** Opens the detailed reporting and analysis window with charts and export options.
    * **Manage Goals:** Opens the window to create, view, and delete your usage goals.
    * **Manage Categories:** Allows you to assign applications to different categories for more accurate reporting.
    * **Achievements:** View all the badges you've unlocked.
    * **Settings:** Configure application settings like language, idle time, and notifications.
    * **Exit:** Safely closes the application and logs your final session.

## 🖼️ UI Showcase

<table>
  <tr>
    <td><img src="assets/reports_screenshot.png" alt="Reports Screen" width="400"></td>
    <td><img src="assets/goals_screenshot.png" alt="Goals Screen" width="400"></td>
  </tr>
  <tr>
    <td align="center"><em>Detailed Reports and Charts</em></td>
    <td align="center"><em>Goal Management Window</em></td>
  </tr>
</table>

## 🛠️ Built With

* **Python 3:** The core programming language.
* **Tkinter:** For creating the modern, custom-themed graphical user interface.
* **Pystray:** For creating and managing the system tray icon and menu.
* **Psutil & Pywin32:** To get information about active system processes and manage windows.
* **Pynput:** For listening to global mouse and keyboard events to detect user activity/idleness.
* **Pillow:** For processing and displaying images and icons in the UI.
* **Matplotlib:** For rendering the pie, bar, and trend charts in the reports window.
* **ReportLab:** For exporting detailed reports to PDF files.
* **PyCryptodomeX:** For AES-256 encryption of the local database.
* **Plyer:** For sending cross-platform desktop notifications for goals, achievements, etc..
* **Sentry-SDK:** For optional, anonymous error reporting.
* **WMI:** Used to generate a consistent, machine-specific ID for the data encryption key.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  **Report Bugs or Suggest Features:** Please open an issue using the [Issues](https://github.com/Rtur2003/Kognita/issues) tab.
2.  **Submit Code Changes:**
    1.  Fork the Project.
    2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
    3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
    4.  Push to the Branch (`git push origin feature/AmazingFeature`).
    5.  Open a Pull Request.

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
