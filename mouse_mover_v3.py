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

# ── Config ─────────────────────────────────────────────────
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
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            return {**DEFAULT_CONFIG, **data}
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    # Atomic write — δεν καταστρέφεται το αρχείο αν κλείσει απότομα
    tmp = CONFIG_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, CONFIG_FILE)
    except Exception as e:
        messagebox.showerror("Σφάλμα", f"Δεν αποθηκεύτηκε: {e}")

cfg = load_config()

# ── Bezier κίνηση ──────────────────────────────────────────
def bezier_move(x1, y1, x2, y2, steps=30, duration=0.8):
    """Κίνηση με καμπύλη Bezier — φαίνεται σαν ανθρώπινο χέρι"""
    # Τυχαίο σημείο ελέγχου για την καμπύλη
    cx = random.randint(min(x1,x2) - 80, max(x1,x2) + 80)
    cy = random.randint(min(y1,y2) - 80, max(y1,y2) + 80)

    delay = duration / steps
    for i in range(steps + 1):
        t = i / steps
        # Τετραγωνική Bezier: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
        bx = int((1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2)
        by = int((1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2)
        # Μικρό τυχαίο jitter για ακόμα πιο φυσική κίνηση
        jx = bx + random.randint(-1, 1)
        jy = by + random.randint(-1, 1)
        pyautogui.moveTo(jx, jy)
        # Μη γραμμική ταχύτητα (πιο αργά στην αρχή και στο τέλος)
        ease = 0.5 - 0.5 * (1 - 2*t if t < 0.5 else 2*t - 1)
        time.sleep(delay * (0.8 + ease * 0.4))

def human_click(x, y, offset=5):
    """Κλικ με καμπύλη κίνηση και τυχαίο offset"""
    cx, cy = pyautogui.position()
    tx = x + random.randint(-offset, offset)
    ty = y + random.randint(-offset, offset)
    bezier_move(cx, cy, tx, ty, steps=random.randint(20, 35),
                duration=random.uniform(0.6, 1.1))
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click()

# ── State ───────────────────────────────────────────────────
running      = False
skip_next    = False
skip_menu    = False
skip_refresh = False
shutdown_at  = None

def force_next():
    global skip_next
    if running: skip_next = True

def force_menu():
    global skip_menu
    if running: skip_menu = True

def force_refresh():
    global skip_refresh
    if running: skip_refresh = True

# ── Actions ─────────────────────────────────────────────────
def do_logout():
    try:
        time.sleep(random.uniform(0.8, 1.2))
        human_click(cfg["PROFILE_X"], cfg["PROFILE_Y"])
        time.sleep(random.uniform(1.0, 1.5))
        human_click(cfg["LOGOUT_X"], cfg["LOGOUT_Y"])
    except Exception as e:
        print(f"Logout error: {e}")

def do_menu_activity():
    try:
        new_x = cfg["MENU_X"] + random.randint(-5, 5)
        new_y = random.randint(cfg["MENU_Y_MIN"], cfg["MENU_Y_MAX"])
        human_click(new_x, new_y)
        if random.random() < 0.5:
            time.sleep(random.uniform(0.3, 0.6))
            pyautogui.scroll(random.choice([1,-1]) * random.randint(3, 7))
    except Exception as e:
        print(f"Menu error: {e}")

def do_refresh():
    try:
        human_click(cfg["REFRESH_X"], cfg["REFRESH_Y"], offset=3)
        time.sleep(random.uniform(3.5, 5.0))
        human_click(cfg["PLAY_X"], cfg["PLAY_Y"], offset=8)
    except Exception as e:
        print(f"Refresh error: {e}")

def do_micro_move():
    """Ελάχιστη κίνηση και επιστροφή — κρατάει session ζωντανό"""
    try:
        cx, cy = pyautogui.position()
        dx = random.randint(-2, 2)
        dy = random.randint(-2, 2)
        pyautogui.moveTo(cx + dx, cy + dy, duration=0.2)
        time.sleep(0.1)
        pyautogui.moveTo(cx, cy, duration=0.2)
    except Exception as e:
        print(f"Micro move error: {e}")

def test_next():
    try:
        human_click(cfg["NEXT_X"], cfg["NEXT_Y"])
    except Exception as e:
        print(f"Next error: {e}")

def test_top():
    try:
        human_click(cfg["MENU_X"], cfg["MENU_Y_MIN"])
    except Exception as e:
        print(f"Top error: {e}")

def test_bottom():
    try:
        human_click(cfg["MENU_X"], cfg["MENU_Y_MAX"])
    except Exception as e:
        print(f"Bottom error: {e}")

def shutdown_timer():
    logged_out = False
    while running and shutdown_at:
        try:
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
        except Exception as e:
            print(f"Shutdown timer error: {e}")
        time.sleep(1)

def move_and_click():
    global skip_next, skip_menu, skip_refresh
    try:
        menu_end    = time.time() + random.uniform(cfg["MENU_MIN"], cfg["MENU_MAX"])
        refresh_end = time.time() + random.uniform(cfg["REFRESH_MIN"], cfg["REFRESH_MAX"])

        if shutdown_at:
            threading.Thread(target=shutdown_timer, daemon=True).start()

        while running:
            try:
                human_click(cfg["NEXT_X"], cfg["NEXT_Y"])
            except Exception as e:
                print(f"Next click error: {e}")

            skip_next  = False
            next_end   = time.time() + random.uniform(cfg["WAIT_MIN"], cfg["WAIT_MAX"])
            last_micro = time.time()

            while running and time.time() < next_end and not skip_next:
                try:
                    now = time.time()
                    nr  = int(next_end - now)
                    mr  = int(menu_end - now)
                    rr  = int(refresh_end - now)

                    countdown_label.config(text=f"▶ NEXT σε: {nr//60}:{nr%60:02d}")
                    menu_label.config(text=f"☰ Λίστα σε: {max(0,mr)//60}:{max(0,mr)%60:02d}" if mr > 0 else "☰ Λίστα: ΤΩΡΑ")
                    refresh_label.config(text=f"↻ Refresh σε: {max(0,rr)//60}:{max(0,rr)%60:02d}" if rr > 0 else "↻ Refresh: ΤΩΡΑ")

                    if now >= menu_end or skip_menu:
                        skip_menu = False
                        do_menu_activity()
                        menu_end = time.time() + random.uniform(cfg["MENU_MIN"], cfg["MENU_MAX"])

                    if now >= refresh_end or skip_refresh:
                        skip_refresh = False
                        do_refresh()
                        refresh_end = time.time() + random.uniform(cfg["REFRESH_MIN"], cfg["REFRESH_MAX"])

                    if now - last_micro >= 30:
                        do_micro_move()
                        last_micro = time.time()

                except Exception as e:
                    print(f"Loop error: {e}")

                time.sleep(1)
            skip_next = False

    except Exception as e:
        print(f"Main thread error: {e}")
    finally:
        try:
            countdown_label.config(text="")
            menu_label.config(text="")
            refresh_label.config(text="")
        except: pass

def toggle():
    global running, shutdown_at
    # Έλεγχος συντεταγμένων
    if cfg["NEXT_X"] == 0 or cfg["MENU_X"] == 0:
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
        try:
            keyboard.add_hotkey("f9", force_next)
            keyboard.add_hotkey("f8", force_menu)
            keyboard.add_hotkey("f7", force_refresh)
        except: pass
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
        try: os.system("shutdown /a 2>nul")
        except: pass

# ── Παράθυρο Ρυθμίσεων ─────────────────────────────────────
def open_settings():
    win = tk.Toplevel(root)
    win.title("⚙ Ρυθμίσεις")
    win.geometry("420x500")
    win.resizable(False, False)
    win.configure(bg="#2c2c2c")
    win.attributes("-topmost", True)

    point_fields = [
        ("MENU Κορυφή",  "MENU_X",   "MENU_Y_MIN"),
        ("MENU Πάτος",   None,        "MENU_Y_MAX"),
        ("NEXT",         "NEXT_X",    "NEXT_Y"),
        ("PLAY",         "PLAY_X",    "PLAY_Y"),
        ("REFRESH",      "REFRESH_X", "REFRESH_Y"),
        ("PROFILE",      "PROFILE_X", "PROFILE_Y"),
        ("LOGOUT",       "LOGOUT_X",  "LOGOUT_Y"),
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

    for col, txt in enumerate(["Σημείο", "X", "Y", ""]):
        tk.Label(grid, text=txt, font=("Arial", 9, "bold"), bg="#2c2c2c",
                 fg="#aaa").grid(row=0, column=col, padx=4, pady=2)

    def capture_point(label, key_x, key_y, ex, ey):
        def run():
            try:
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
                capturing_label.config(text=f"✓ {label}: ({x}, {y})", fg="#2ecc71")
            except Exception as e:
                capturing_label.config(text=f"Σφάλμα: {e}", fg="#e74c3c")
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

        tk.Button(grid, text="🎯 Καταγραφή", font=("Arial", 8),
                  bg="#e67e22", fg="white", relief="flat", cursor="hand2",
                  command=lambda lb=label, kx=key_x, ky=key_y, exx=ex, eyy=ey:
                      capture_point(lb, kx, ky, exx, eyy)
                  ).grid(row=row, column=3, padx=4)

    def save():
        try:
            for key, entry in entries.items():
                val = int(entry.get())
                cfg[key] = val
            save_config(cfg)
            messagebox.showinfo("✓ Αποθήκευση", "Οι ρυθμίσεις αποθηκεύτηκαν!")
            win.destroy()
        except ValueError:
            messagebox.showerror("Σφάλμα", "Βάλε μόνο αριθμούς!")
        except Exception as e:
            messagebox.showerror("Σφάλμα", str(e))

    tk.Button(win, text="💾 Αποθήκευση", font=("Arial", 12, "bold"),
              bg="#2ecc71", fg="white", relief="flat", cursor="hand2",
              command=save).pack(pady=10)

# ── GUI ─────────────────────────────────────────────────────
root = tk.Tk()
root.title("Mouse Mover v3")
root.geometry("310x470")
root.resizable(False, False)
root.configure(bg="#2c2c2c")
root.attributes("-topmost", True)

tk.Label(root, text="Mouse Mover v3", font=("Arial", 16, "bold"),
         bg="#2c2c2c", fg="white").pack(pady=6)
tk.Label(root, text="✦ Bezier Movement  ✦ Anti-Bot",
         font=("Arial", 9), bg="#2c2c2c", fg="#888").pack()

tk.Button(root, text="⚙ Ρυθμίσεις Συντεταγμένων", font=("Arial", 10),
          bg="#e67e22", fg="white", relief="flat", cursor="hand2",
          command=open_settings).pack(pady=6)

frame = tk.Frame(root, bg="#2c2c2c")
frame.pack(pady=2)
tk.Label(frame, text="Shutdown σε (ώρες):", font=("Arial", 10),
         bg="#2c2c2c", fg="#aaa").pack(side="left", padx=4)
hours_entry = tk.Entry(frame, width=6, font=("Arial", 11), bg="#444",
                        fg="white", insertbackground="white", justify="center", relief="flat")
hours_entry.insert(0, "5.5")
hours_entry.pack(side="left")

status_label = tk.Label(root, text="Κατάσταση: Σταματημένο",
                        font=("Arial", 10), bg="#2c2c2c", fg="#e74c3c")
status_label.pack(pady=2)

countdown_label = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#f39c12")
countdown_label.pack(pady=1)
menu_label      = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#3498db")
menu_label.pack(pady=1)
refresh_label   = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#2ecc71")
refresh_label.pack(pady=1)
shutdown_label  = tk.Label(root, text="", font=("Arial", 10), bg="#2c2c2c", fg="#e67e22")
shutdown_label.pack(pady=1)

btn = tk.Button(root, text="START", font=("Arial", 14, "bold"),
                bg="#2ecc71", fg="white", width=12, relief="flat",
                cursor="hand2", command=toggle)
btn.pack(pady=6)

tk.Label(root, text="F9=NEXT  F8=Λίστα  F7=Refresh  |  Γωνία=stop",
         font=("Arial", 8), bg="#2c2c2c", fg="#888").pack()

btn_frame = tk.Frame(root, bg="#2c2c2c")
btn_frame.pack(pady=3)
for txt, color, func in [
    ("Test Next",    "#e74c3c", test_next),
    ("Test Λίστα",  "#2980b9", do_menu_activity),
    ("Test Refresh", "#16a085", do_refresh),
    ("Test Logout",  "#8e44ad", do_logout),
]:
    tk.Button(btn_frame, text=txt, font=("Arial", 9), bg=color, fg="white",
              relief="flat", cursor="hand2",
              command=lambda f=func: threading.Thread(target=f, daemon=True).start()
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
