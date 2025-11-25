#!/usr/bin/env python
"""
Debug script to test GUI imports and basic functionality
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

print("=" * 60)
print("DEBUG: Testing GUI Components")
print("=" * 60)

# Test 1: Check Python version
print(f"\n1. Python version: {sys.version}")

# Test 2: Try importing PyQt6
try:
    from PyQt6.QtWidgets import QApplication
    print("✅ 2. PyQt6 imported successfully")
except ImportError as e:
    print(f"❌ 2. PyQt6 import failed: {e}")
    sys.exit(1)

# Test 3: Try importing qfluentwidgets
try:
    from qfluentwidgets import FluentWindow, HyperlinkButton
    print("✅ 3. qfluentwidgets imported successfully")
except ImportError as e:
    print(f"❌ 3. qfluentwidgets import failed: {e}")
    sys.exit(1)

# Test 4: Try importing scribdl.gui
try:
    from scribdl import gui
    print("✅ 4. scribdl.gui module imported successfully")
except Exception as e:
    print(f"❌ 4. scribdl.gui import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Try creating QApplication
try:
    app = QApplication(sys.argv)
    print("✅ 5. QApplication created successfully")
except Exception as e:
    print(f"❌ 5. QApplication creation failed: {e}")
    sys.exit(1)

# Test 6: Try creating GUI window
try:
    from scribdl.gui import ScribdDownloaderWindow
    window = ScribdDownloaderWindow()
    print("✅ 6. GUI window created successfully")
    print(f"   Window title: {window.windowTitle()}")
except Exception as e:
    print(f"❌ 6. GUI window creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nThe GUI should work fine. If it crashes when running,")
print("please provide the exact error message.")
