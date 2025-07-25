# Kognita ✨

*The Art of Understanding Your Digital Footprint.*

[](https://opensource.org/licenses/MIT)
[](https://www.microsoft.com/windows/)
[](https://www.python.org/)

Kognita is a silent, local-first desktop activity tracker that helps you understand how you spend your time on your computer. It's not a surveillance tool, but a personal analytics engine designed for self-awareness and productivity. **All of your data is stored locally on your machine and is never shared with anyone.**

*(Hint: You can create a GIF like this by recording your screen, placing the file in an `assets` folder, and updating the link.)*

## ✨ Features

  * 🤫 **Silent Background Tracking:** Runs quietly in the background without requiring a persistent terminal window.
  * 🖱️ **Smart Idle Detection:** Intelligently detects when you're away from your keyboard and mouse, pausing the timer to ensure only active usage is logged.
  * **System Tray Integration:** Lives in the Windows System Tray for minimal intrusion.
  * 📊 **Simple GUI Reporting:** A clean, user-friendly window displays your activity report with a single click.
  * 🧠 **Digital Persona Analysis:** Analyzes your usage patterns to assign you a fun "digital persona" like "Productivity Guru" or "Focused Gamer".
  * 🔒 **Privacy-First:** All data is stored in a local SQLite database file (`kognita_data.db`) within the project folder. Nothing ever leaves your computer.

## 🚀 Installation

### For End-Users (Recommended)

You do not need Python or any other tools to run the application.

1.  Go to the project's [**Releases Page**](https://www.google.com/search?q=https://github.com/Rtur2003/Kognita/releases).
2.  Download the `Kognita.exe` file from the latest release's "Assets" section.
3.  Run the downloaded executable file. That's it\!

### For Developers

If you want to run the project from the source code or contribute to its development:

1.  Clone the repository:
    ```bash
    git clone https://github.com/Rtur2003/Kognita.git
    cd Kognita
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the application in development mode:
    ```bash
    python main.py
    ```

## 🖥️ Usage

1.  Run `Kognita.exe` (for users) or `python main.py` (for developers).
2.  The Kognita icon will appear in your system tray (the area in the bottom-right corner of your screen).
3.  The application will automatically begin tracking your activity in the background.
4.  Right-click the icon to open the context menu:
      * **Show Report:** Opens a window displaying your activity analysis for the last 24 hours.
      * **Exit:** Safely closes the application and logs your final session.

## 🛠️ Tech Stack

  * **Python 3:** The core programming language.
  * **Tkinter:** Python's standard library for creating the simple GUI report window.
  * **Pystray:** For creating and managing the system tray icon and menu.
  * **Psutil:** To get information about active system processes, like the application name.
  * **Pynput:** For listening to global mouse and keyboard events to detect user activity.
  * **PyInstaller:** To package the entire project into a standalone `.exe` file.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  **Report Bugs or Suggest Features:** Please open an issue using the [Issues](https://www.google.com/search?q=https://github.com/Rtur2003/Kognita/issues) tab.
2.  **Submit Code Changes:**
    1.  Fork the Project.
    2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
    3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
    4.  Push to the Branch (`git push origin feature/AmazingFeature`).
    5.  Open a Pull Request.

## 📝 License

This project is licensed under the MIT License. See the [`LICENSE`](https://www.google.com/search?q=LICENSE) file for more details.
