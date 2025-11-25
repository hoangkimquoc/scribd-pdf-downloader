# 📖 Scribd PDF Downloader - Installation Guide

> Complete step-by-step installation guide for beginners with no programming experience required.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Step 1: Install Python](#step-1-install-python)
3. [Step 2: Enable Long Path Support (Windows)](#step-2-enable-long-path-support-windows)
4. [Step 3: Download the Code](#step-3-download-the-code)
5. [Step 4: Install Dependencies](#step-4-install-dependencies)
6. [Step 5: Run the Program](#step-5-run-the-program)
7. [How to Use](#how-to-use)
8. [Troubleshooting](#troubleshooting)

---

## ✅ System Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Internet Connection:** Required for downloading Python and libraries
- **Web Browser:** Google Chrome (will be used automatically by Selenium)

---

## 🐍 Step 1: Install Python

### Windows

1. **Download Python:**
   - Visit: https://www.python.org/downloads/
   - Click the **"Download Python 3.x.x"** button (latest version)

2. **Install Python:**
   - Open the downloaded file (e.g., `python-3.12.0-amd64.exe`)
   - ⚠️ **IMPORTANT:** Check the box **"Add Python to PATH"** on the first screen
   - Click **"Install Now"**
   - Wait for the installation to complete
   - Click **"Close"**

3. **Verify installation:**
   - Open **Command Prompt** (press `Win + R`, type `cmd`, press Enter)
   - Type the following command and press Enter:
     ```bash
     python --version
     ```
   - If it shows `Python 3.x.x`, installation was successful ✅

### macOS

1. **Download Python:**
   - Visit: https://www.python.org/downloads/
   - Download the macOS installer

2. **Install:**
   - Open the downloaded `.pkg` file
   - Follow the on-screen instructions
   - Enter your password when prompted

3. **Verify:**
   - Open **Terminal** (Cmd + Space, type "Terminal")
   - Type: `python3 --version`

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip
python3 --version
```

---

## 🔧 Step 2: Enable Long Path Support (Windows)

> ⚠️ **Windows only.** This step prevents errors when installing PyQt6.

### Method 1: Using PowerShell (Recommended)

1. **Open PowerShell as Administrator:**
   - Press `Win + X`
   - Select **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**
   - Click **"Yes"** when prompted

2. **Run the following command:**
   ```powershell
   reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
   ```

3. **Restart your computer**

### Method 2: Using Group Policy Editor

1. Press `Win + R`, type `gpedit.msc`, press Enter
2. Navigate to: **Computer Configuration** → **Administrative Templates** → **System** → **Filesystem**
3. Find **"Enable Win32 long paths"**
4. Double-click, select **"Enabled"**, click **OK**
5. Restart your computer

---

## 📥 Step 3: Download the Code

### If you have Git:

```bash
git clone https://github.com/ritiek/scribd-downloader.git
cd scribd-downloader
```

### If you don't have Git:

1. Download the ZIP file from GitHub
2. Extract it to your desired location (e.g., `C:\scribd-downloader`)
3. Open **Command Prompt** or **Terminal**
4. Navigate to the folder:
   ```bash
   cd C:\scribd-downloader
   ```
   *(Replace `C:\scribd-downloader` with your actual path)*

---

## 📦 Step 4: Install Dependencies

### Install all dependencies at once:

**Windows:**
```bash
pip install BeautifulSoup4 requests PyQt6 PyQt6-Fluent-Widgets selenium webdriver-manager PyPDF2 Pillow reportlab
```

**macOS/Linux:**
```bash
pip3 install BeautifulSoup4 requests PyQt6 PyQt6-Fluent-Widgets selenium webdriver-manager PyPDF2 Pillow reportlab
```

### Or install from requirements files:

```bash
pip install -r requirements.txt
pip install -r requirements_selenium.txt
pip install PyQt6 PyQt6-Fluent-Widgets
```

> 💡 **Note:** Installation may take 5-10 minutes depending on your internet speed.

---

## 🚀 Step 5: Run the Program

1. **Make sure you're in the `scribd-downloader` directory**

2. **Run the command:**

   **Windows:**
   ```bash
   python launch_gui.py
   ```

   **macOS/Linux:**
   ```bash
   python3 launch_gui.py
   ```

3. **The GUI window will appear** 🎉

---

## 🎯 How to Use

### Program Interface

When you open the program, you'll see:

```
┌─────────────────────────────────────────┐
│   Scribd PDF Downloader                 │
├─────────────────────────────────────────┤
│ [Enter Scribd Document URL]             │
│ [Select Output Directory] [Browse...]   │
│                                          │
│ [Download]  [Stop]  ○ Status             │
│                                          │
│ ┌─────────────────────────────────────┐ │
│ │ Log Output Area                     │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                                          │
│      ☕ Support this project on Ko-fi   │
└─────────────────────────────────────────┘
```

### Steps to Download PDF:

1. **Enter URL:**
   - Copy the Scribd document link (e.g., `https://www.scribd.com/document/123456789/example`)
   - Paste it into the **"Enter Scribd Document URL"** field

2. **Select save location (optional):**
   - Click the **"Browse"** button
   - Choose the folder where you want to save the PDF
   - If not selected, the file will be saved in the current directory

3. **Start download:**
   - Click the **"Download"** button
   - Wait for the program to download (may take a few minutes)
   - Watch the progress in the **Log Output** area

4. **Complete:**
   - When you see **"Download completed successfully!"**
   - The PDF file has been saved to your selected folder

### Features:

- ✅ **Auto-scroll:** Selenium automatically scrolls to load all content
- ✅ **High-quality PDF:** Combines all pages into one PDF file
- ✅ **Stop anytime:** Click the **"Stop"** button to cancel
- ✅ **Dark Mode:** Beautiful dark interface

---

## ⚠️ Troubleshooting

### Error 1: `python is not recognized`

**Cause:** Python not added to PATH

**Solution:**
1. Uninstall Python
2. Reinstall and remember to check **"Add Python to PATH"**

### Error 2: `No module named 'PyQt6'`

**Cause:** PyQt6 not installed

**Solution:**
```bash
pip install PyQt6 PyQt6-Fluent-Widgets
```

### Error 3: `OSError: [Errno 2] No such file or directory` (Windows)

**Cause:** Long Path Support not enabled

**Solution:**
- Follow [Step 2](#step-2-enable-long-path-support-windows)
- Restart your computer
- Reinstall PyQt6

### Error 4: `ChromeDriver not found`

**Cause:** Chrome or ChromeDriver not installed

**Solution:**
1. Install Google Chrome: https://www.google.com/chrome/
2. ChromeDriver will auto-download on first run

### Error 5: GUI doesn't appear

**Solution:**
1. Check if all libraries are installed:
   ```bash
   pip list | findstr PyQt6
   ```
2. Try running the debug file:
   ```bash
   python debug_gui.py
   ```
3. Check the console for errors and Google for solutions

### Error 6: "Access Denied" when downloading

**Cause:** Document is locked or requires login

**Solution:**
- Some Scribd documents require a Premium account
- This tool only works with publicly accessible documents

---

## 💡 Tips

1. **Download speed:**
   - PDF downloads take 2-5 minutes depending on document length
   - Don't close the program while downloading

2. **PDF quality:**
   - PDFs are created from screenshots
   - Quality depends on the original document

3. **Multiple uses:**
   - No need to reinstall libraries
   - Just run `python launch_gui.py` each time you use it

4. **Updates:**
   - To get the latest code:
     ```bash
     git pull
     ```

---

## 🆘 Support

If you encounter issues:

1. **Re-read the guide** from the beginning
2. **Check the Troubleshooting section** above
3. **Google the error** with keywords: `scribd downloader [error name]`
4. **Create an Issue** on the GitHub repository

---

## ☕ Support the Project

If you find this tool useful, please support the author:

👉 **[Support on Ko-fi](https://ko-fi.com/solveproblem)**

---

## 📝 Notes

- This tool is for educational and research purposes only
- Respect the copyright of document authors
- Do not use for commercial purposes

---

**Happy downloading! 🎉**
