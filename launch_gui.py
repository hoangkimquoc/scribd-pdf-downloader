#!/usr/bin/env python
import sys
import subprocess
import os
import importlib.util

def check_and_install_dependencies():
    """Check for required packages and install them if missing."""
    required_packages = [
        ("PyQt6", "PyQt6"),
        ("qfluentwidgets", "PyQt6-Fluent-Widgets"),
        ("selenium", "selenium"),
        ("webdriver_manager", "webdriver-manager"),
        ("PIL", "Pillow"),
        ("reportlab", "reportlab"),
        ("PyPDF2", "PyPDF2"),
        ("requests", "requests"),
        ("bs4", "beautifulsoup4"),
    ]

    missing_packages = []
    print("Checking dependencies...")
    
    for import_name, package_name in required_packages:
        if importlib.util.find_spec(import_name) is None:
            print(f"  [x] Missing: {package_name}")
            missing_packages.append(package_name)
        else:
            print(f"  [v] Found: {package_name}")

    if missing_packages:
        print(f"\nInstalling {len(missing_packages)} missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("\nAll dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"\nError installing dependencies: {e}")
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        print("\nAll dependencies are already installed.")

def main():
    # 1. Install dependencies
    check_and_install_dependencies()
    
    # 2. Setup path to include src
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # 3. Launch GUI
    print("\nLaunching Scribd Downloader...")
    try:
        from scribdl.gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"Error launching application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
