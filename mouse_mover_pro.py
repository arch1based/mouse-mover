import tkinter as tk
from tkinter import messagebox
import threading
import time
import random
import subprocess
import sys
import os
import json

# Auto-install
for pkg in ["pyautogui", "keyboard"]:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import pyautogui
import keyboard

pyautogui.FAILSAFE = True

# ── Config αρχείο ──────────────────────────────────────────
# Σωστό path για EXE (PyInstaller) και για .py script
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(app_dir, "mover_config.json")

DEFAULT_CONFIG = {
    "MENU_X": 0, "MENU_Y_MIN": 0, "MENU_Y_MAX": 0,
    "NEXT_X": 0, "NEXT_Y": 0,
    "PLAY_X": 0, "PLAY_Y": 0,
    "REFRESH_X": 0, "REFRESH_Y": 0,
    "PROFILE_X": 0, "PROFILE_Y": 0,
    "LOGOUT_X": 0, "LOGOUT_Y": 0,
    "WAIT_MIN": 120, "WAIT_MAX": 300,
    "MENU_MIN": 600, "MENU_MAX": 1200,
    "REFRESH_MIN": 2700, "REFRESH_MAX": 3300,
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

cfg = load_config()

# ── State ───────────────────────────────────────────────────
running      = False
skip_next    = False
skip_menu    = False
skip_refresh = False
shutdown_at  = None

# ── Actions ─────────────────────────────────────────────────
def force_next():
    global skip_next
    if running: skip_next = True

def force_menu():
    global skip_menu
    if running: skip_menu = True

def force_refresh():
    global skip_refresh
    if running: skip_refresh = True

def do_logout():
    time.sleep(1)
    pyautogui.moveTo(cfg["PROFILE_X"] + random.randint(-3,3),
                     cfg["PROFILE_Y"] + random.randint(-3,3),
                     duration=random.uniform(0.5, 0.9))
    time.sleep(random.uniform(0.5, 1.0))
    pyautogui.click()
    time.sleep(random.uniform(1.0, 1.5))
    pyautogui.moveTo(cfg["LOGOUT_X"] + random.randint(-3,3),
                     cfg["LOGOUT_Y"] + random.randint(-3,3),
                     duration=random.uniform(0.5, 0.9))
    time.sleep(random.uniform(0.3, 0.6))
    pyautogui.click()

def do_menu_activity():
    new_x = cfg["MENU_X"] + random.randint(-5, 5)
    new_y = random.randint(cfg["MENU_Y_MIN"], cfg["MENU_Y_MAX"])
    pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.5, 1.0))
    time.sleep(random.uniform(0.2, 0.3))
    pyautogui.click()
    if random.random() < 0.5:
        time.sleep(random.uniform(0.3, 0.6))
        pyautogui.scroll(random.choice([1,-1]) * random.randint(3, 7))

def do_refresh():
    pyautogui.moveTo(cfg["REFRESH_X"] + random.randint(-2,2),
                     cfg["REFRESH_Y"] + random.randint(-2,2),
                     duration=random.uniform(0.4, 0.7))
    time.sleep(0.2)
    pyautogui.click()
    time.sleep(4)
    pyautogui.moveTo(cfg["PLAY_X"] + random.randint(-8,8),
                     cfg["PLAY_Y"] + random.randint(-8,8),
                     duration=random.uniform(0.4, 0.8))
    time.sleep(random.uniform(0.3, 0.6))
    pyautogui.click()

def test_next():
    pyautogui.moveTo(cfg["NEXT_X"] + random.randint(-3,3),
                     cfg["NEXT_Y"] + random.randint(-3,3),
                     duration=random.uniform(0.5, 1.0))
    time.sleep(random.uniform(0.2, 0.4))
    pyautogui.click()

def test_top():
    pyautogui.moveTo(cfg["MENU_X"], cfg["MENU_Y_MIN"], duration=0.5)
    pyautogui.click()

def test_bottom():
    pyautogui.moveTo(cfg["MENU_X"], cfg["MENU_Y_MAX"], duration=0.5)
    pyautogui.click()

def shutdown_timer():
    logged_out = False
    while running and shutdown_at:
        remaining = int(shutdown_at - time.time())
        if remaining <= 0:
            os.system("shutdown /s /t 30")
            shutdown_label.config(text="⚠ Κλείσιμο σε 30 δευτ!", fg="#e74c3c")
            break
        if remaining <= 180 and not logged_out:
            logged_out = True
            shutdown_label.config(text="⚠ Αποσύνδεση...", fg="#e74c3c")
            do_logout()
        h = remaining // 3600
        m = (remaining % 3600) // 60
        s = remaining % 60
        shutdown_label.config(text=f"⏻ Shutdown σε: {h}:{m:02d}:{s:02d}", fg="#e67e22")
        time.sleep(1)

def move_and_click():
    global skip_next, skip_menu, skip_refresh
    menu_end    = time.time() + random.uniform(cfg["MENU_MIN"], cfg["MENU_MAX"])
    refresh_end = time.time() + random.uniform(cfg["REFRESH_MIN"], cfg["REFRESH_MAX"])

    if shutdown_at:
        threading.Thread(target=shutdown_timer, daemon=True).start()

    while running:
        pyautogui.moveTo(cfg["NEXT_X"] + random.randint(-3,3),
                         cfg["NEXT_Y"] + random.randint(-3,3),
                         duration=random.uniform(0.5, 1.0))
        time.sleep(random.uniform(0.2, 0.4))
        pyautogui.click()

        skip_next = False
        next_end   = time.time() + random.uniform(cfg["WAIT_MIN"], cfg["WAIT_MAX"])
        last_micro = time.time()

        while running and time.time() < next_end and not skip_next:
            now = time.time()
            nr = int(next_end - now)
            mr = int(menu_end - now)
            rr = int(refresh_end - now)
            countdown_label.config(text=f"▶ NEXT σε: {nr//60}:{nr%60:02d}")
            menu_label.config(text=f"☰ Λίστα σε: {max(0,mr)//60}:{max(0,mr)%60:02d}" if mr > 0 else "☰ Λίστα σε: ΤΩΡΑ")
            refresh_label.config(text=f"↻ Refresh σε: {max(0,rr)//60}:{max(0,rr)%60:02d}" if rr > 0 else "↻ Refresh σε: ΤΩΡΑ")

            if now >= menu_end or skip_menu:
                do_menu_activity()
                skip_menu = False
                menu_end = time.time() + random.uniform(cfg["MENU_MIN"], cfg["MENU_MAX"])

            if now >= refresh_end or skip_refresh:
                skip_refresh = False
                do_refresh()
                refresh_end = time.time() + random.uniform(cfg["REFRESH_MIN"], cfg["REFRESH_MAX"])

            if now - last_micro >= 30:
                cx, cy = pyautogui.position()
                pyautogui.moveTo(cx + random.randint(-3,3), cy + random.randint(-3,3), duration=0.3)
                last_micro = time.time()

            time.sleep(1)
        skip_next = False

    countdown_label.config(text="")
    menu_label.config(text="")
    refresh_label.config(text="")

def toggle():
    global running, shutdown_at
    if cfg["MENU_X"] == 0:
        messagebox.showerror("Σφάλμα", "Πρώτα ρύθμισε τις συντεταγμένες\nαπό το κουμπί ⚙ Ρυθμίσεις!")
        return
    if not running:
        try:
            hours = float(hours_entry.get())
            if hours <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Σφάλμα", "Βάλε έγκυρο αριθμό ωρών (π.χ. 5.5)")
            return
        shutdown_at = time.time() + hours * 3600
        running = True
        btn.config(text="STOP", bg="#e74c3c")
        status_label.config(text="Κατάσταση: Ενεργό", fg="#2ecc71")
        hours_entry.config(state="disabled")
        keyboard.add_hotkey("f9", force_next)
        keyboard.add_hotkey("f8", force_menu)
        keyboard.add_hotkey("f7", force_refresh)
        threading.Thread(target=move_and_click, daemon=True).start()
    else:
        running = False
        shutdown_at = None
        try:
            keyboard.remove_hotkey("f9")
            keyboard.remove_hotkey("f8")
            keyboard.remove_hotkey("f7")
        except: pass
        btn.config(text="START", bg="#2ecc71")
        status_label.config(text="Κατάσταση: Σταματημένο", fg="#e74c3c")
        countdown_label.config(text="")
        menu_label.config(text="")
        refresh_label.config(text="")
        shutdown_label.config(text="")
        hours_entry.config(state="normal")
        os.system("shutdown /a 2>nul")

# ── Παράθυρο Ρυθμίσεων ─────────────────────────────────────
def open_settings():
    win = tk.Toplevel(root)
    win.title("Ρυθμίσεις Συντεταγμένων")
    win.geometry("420x500")
    win.resizable(False, False)
    win.configure(bg="#2c2c2c")
    win.attributes("-topmost", True)

    # Ζεύγη: (label, key_x, key_y) — None για μονό Y
    point_fields = [
        ("MENU Κορυφή",  "MENU_X",     "MENU_Y_MIN"),
        ("MENU Πάτος",   None,          "MENU_Y_MAX"),
        ("NEXT",         "NEXT_X",      "NEXT_Y"),
        ("PLAY",         "PLAY_X",      "PLAY_Y"),
        ("REFRESH",      "REFRESH_X",   "REFRESH_Y"),
        ("PROFILE",      "PROFILE_X",   "PROFILE_Y"),
        ("LOGOUT",       "LOGOUT_X",    "LOGOUT_Y"),
    ]

    entries = {}
    tk.Label(win, text="⚙ Συντεταγμένες", font=("Arial", 13, "bold"),
             bg="#2c2c2c", fg="white").pack(pady=8)
    tk.Label(win, text="Πάτα 'Καταγραφή' και βάλε το ποντίκι\nστο σημείο μέσα σε 5 δευτερόλεπτα",
             font=("Arial", 9), bg="#2c2c2c", fg="#aaa", justify="center").pack(pady=2)

    grid = tk.Frame(win, bg="#2c2c2c")
    grid.pack(padx=10, pady=5)

    capturing_label = tk.Label(win, text="", font=("Arial", 10, "bold"),
                                bg="#2c2c2c", fg="#f39c12")
    capturing_label.pack()

    # Headers
    for col, txt in enumerate(["Σημείο", "X", "Y", ""]):
        tk.Label(grid, text=txt, font=("Arial", 9, "bold"), bg="#2c2c2c",
                 fg="#aaa").grid(row=0, column=col, padx=4, pady=2)

    def capture_point(label, key_x, key_y, ex, ey):
        def run():
            for i in range(5, 0, -1):
                capturing_label.config(text=f"Καταγραφή '{label}' σε {i}...")
                time.sleep(1)
            x, y = pyautogui.position()
            if ex:
                ex.delete(0, tk.END)
                ex.insert(0, str(x))
            if ey:
                ey.delete(0, tk.END)
                ey.insert(0, str(y))
            capturing_label.config(text=f"✓ {label}: ({x}, {y})")
        threading.Thread(target=run, daemon=True).start()

    for i, (label, key_x, key_y) in enumerate(point_fields):
        row = i + 1
        tk.Label(grid, text=label, font=("Arial", 9), bg="#2c2c2c", fg="#ccc",
                 width=12, anchor="w").grid(row=row, column=0, padx=4, pady=4)

        if key_x:
            ex = tk.Entry(grid, width=6, font=("Arial", 9), bg="#444", fg="white",
                          insertbackground="white", justify="center", relief="flat")
            ex.insert(0, str(cfg.get(key_x, 0)))
            ex.grid(row=row, column=1, padx=3)
            entries[key_x] = ex
        else:
            ex = None
            tk.Label(grid, text="—", bg="#2c2c2c", fg="#555", width=6).grid(row=row, column=1)

        ey = tk.Entry(grid, width=6, font=("Arial", 9), bg="#444", fg="white",
                      insertbackground="white", justify="center", relief="flat")
        ey.insert(0, str(cfg.get(key_y, 0)))
        ey.grid(row=row, column=2, padx=3)
        entries[key_y] = ey

        tk.Button(grid, text="Καταγραφή", font=("Arial", 8),
                  bg="#e67e22", fg="white", relief="flat", cursor="hand2",
                  command=lambda lb=label, kx=key_x, ky=key_y, exx=ex, eyy=ey:
                      capture_point(lb, kx, ky, exx, eyy)
                  ).grid(row=row, column=3, padx=4)

    def save():
        try:
            for key, entry in entries.items():
                cfg[key] = int(entry.get())
            save_config(cfg)
            messagebox.showinfo("Αποθήκευση", "Οι ρυθμίσεις αποθηκεύτηκαν!")
            win.destroy()
        except ValueError:
            messagebox.showerror("Σφάλμα", "Βάλε μόνο αριθμούς!")

    tk.Button(win, text="💾 Αποθήκευση", font=("Arial", 12, "bold"),
              bg="#2ecc71", fg="white", relief="flat", cursor="hand2",
              command=save).pack(pady=10)

# ── Κύριο GUI ───────────────────────────────────────────────
root = tk.Tk()
root.title("Mouse Mover Pro")
root.geometry("310x460")
root.resizable(False, False)
root.configure(bg="#2c2c2c")
root.attributes("-topmost", True)

tk.Label(root, text="Mouse Mover Pro", font=("Arial", 16, "bold"),
         bg="#2c2c2c", fg="white").pack(pady=6)

tk.Button(root, text="⚙ Ρυθμίσεις Συντεταγμένων", font=("Arial", 10),
          bg="#e67e22", fg="white", relief="flat", cursor="hand2",
          command=open_settings).pack(pady=4)

frame = tk.Frame(root, bg="#2c2c2c")
frame.pack(pady=4)
tk.Label(frame, text="Shutdown σε (ώρες):", font=("Arial", 10),
         bg="#2c2c2c", fg="#aaa").pack(side="left", padx=4)
hours_entry = tk.Entry(frame, width=6, font=("Arial", 11), bg="#444",
                        fg="white", insertbackground="white", justify="center", relief="flat")
hours_entry.insert(0, "5.5")
hours_entry.pack(side="left")

status_label = tk.Label(root, text="Κατάσταση: Σταματημένο",
                        font=("Arial", 10), bg="#2c2c2c", fg="#e74c3c")
status_label.pack()

countdown_label = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#f39c12")
countdown_label.pack(pady=1)
menu_label     = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#3498db")
menu_label.pack(pady=1)
refresh_label  = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#2ecc71")
refresh_label.pack(pady=1)
shutdown_label = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#e67e22")
shutdown_label.pack(pady=1)

btn = tk.Button(root, text="START", font=("Arial", 14, "bold"),
                bg="#2ecc71", fg="white", width=12, relief="flat",
                cursor="hand2", command=toggle)
btn.pack(pady=8)

tk.Label(root, text="F9=NEXT  F8=Λίστα  F7=Refresh  |  Γωνία=stop",
         font=("Arial", 8), bg="#2c2c2c", fg="#888").pack()

btn_frame = tk.Frame(root, bg="#2c2c2c")
btn_frame.pack(pady=3)
tk.Button(btn_frame, text="Test Next",    font=("Arial", 9), bg="#e74c3c", fg="white",
          relief="flat", cursor="hand2",
          command=lambda: threading.Thread(target=test_next, daemon=True).start()
          ).pack(side="left", padx=2)
tk.Button(btn_frame, text="Test Λίστα",  font=("Arial", 9), bg="#2980b9", fg="white",
          relief="flat", cursor="hand2",
          command=lambda: threading.Thread(target=do_menu_activity, daemon=True).start()
          ).pack(side="left", padx=2)
tk.Button(btn_frame, text="Test Refresh", font=("Arial", 9), bg="#16a085", fg="white",
          relief="flat", cursor="hand2",
          command=lambda: threading.Thread(target=do_refresh, daemon=True).start()
          ).pack(side="left", padx=2)
tk.Button(btn_frame, text="Test Logout",  font=("Arial", 9), bg="#8e44ad", fg="white",
          relief="flat", cursor="hand2",
          command=lambda: threading.Thread(target=do_logout, daemon=True).start()
          ).pack(side="left", padx=2)

btn_frame2 = tk.Frame(root, bg="#2c2c2c")
btn_frame2.pack(pady=3)
tk.Button(btn_frame2, text="▲ Αρχή Λίστας", font=("Arial", 9), bg="#27ae60", fg="white",
          relief="flat", cursor="hand2",
          command=lambda: threading.Thread(target=test_top, daemon=True).start()
          ).pack(side="left", padx=3)
tk.Button(btn_frame2, text="▼ Τέλος Λίστας", font=("Arial", 9), bg="#e67e22", fg="white",
          relief="flat", cursor="hand2",
          command=lambda: threading.Thread(target=test_bottom, daemon=True).start()
          ).pack(side="left", padx=3)

root.mainloop()
