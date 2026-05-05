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

CONFIG_FILE = os.path.join(app_dir, "mover_config_v4.json")

DEFAULT_CONFIG = {
    "NEXT_X": 0,      "NEXT_Y": 0,
    "PLAY_X": 0,      "PLAY_Y": 0,
    "LIST_X": 0,      "LIST_Y": 0,
    "SLIDE_X": 0,     "SLIDE_Y_MIN": 0,  "SLIDE_Y_MAX": 0,
    "REFRESH_X": 0,   "REFRESH_Y": 0,
    "PROFILE_X": 0,   "PROFILE_Y": 0,
    "LOGOUT_X": 0,    "LOGOUT_Y": 0,
    "WAIT_MIN": 120,  "WAIT_MAX": 300,
    "REFRESH_MIN": 2700, "REFRESH_MAX": 3300,
    "USE_NEXT":    True,
    "USE_LIST":    True,
    "USE_REFRESH": True,
    "USE_PLAY":    True,
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
    cx = random.randint(min(x1, x2) - 80, max(x1, x2) + 80)
    cy = random.randint(min(y1, y2) - 80, max(y1, y2) + 80)
    delay = duration / steps
    for i in range(steps + 1):
        t = i / steps
        bx = int((1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2)
        by = int((1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2)
        pyautogui.moveTo(bx + random.randint(-1, 1), by + random.randint(-1, 1))
        ease = 0.5 - 0.5 * (1 - 2*t if t < 0.5 else 2*t - 1)
        time.sleep(delay * (0.8 + ease * 0.4))

def human_click(x, y, offset=5):
    cx, cy = pyautogui.position()
    tx = x + random.randint(-offset, offset)
    ty = y + random.randint(-offset, offset)
    bezier_move(cx, cy, tx, ty,
                steps=random.randint(20, 35),
                duration=random.uniform(0.6, 1.1))
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.click()

# ── State ───────────────────────────────────────────────────
running      = False
skip_next    = False
skip_refresh = False
shutdown_at  = None

def force_next():
    global skip_next
    if running: skip_next = True

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

def do_list_click():
    """Ανοίγει ≡ → κλικ τυχαίο slide → κλείνει ≡"""
    try:
        if not (cfg["USE_LIST"] and cfg["LIST_X"] > 0):
            return
        # 1. Άνοιγμα λίστας
        human_click(cfg["LIST_X"], cfg["LIST_Y"], offset=4)
        time.sleep(random.uniform(0.8, 1.5))
        # 2. Κλικ σε τυχαίο slide (αν έχουν ρυθμιστεί οι συντεταγμένες)
        if cfg.get("SLIDE_X", 0) > 0 and cfg.get("SLIDE_Y_MAX", 0) > cfg.get("SLIDE_Y_MIN", 0):
            slide_y = random.randint(cfg["SLIDE_Y_MIN"], cfg["SLIDE_Y_MAX"])
            human_click(cfg["SLIDE_X"], slide_y, offset=4)
            time.sleep(random.uniform(0.8, 1.5))
        # 3. Κλείσιμο λίστας
        human_click(cfg["LIST_X"], cfg["LIST_Y"], offset=4)
        time.sleep(random.uniform(0.3, 0.6))
    except Exception as e:
        print(f"List error: {e}")

def do_refresh():
    try:
        if not (cfg["USE_REFRESH"] and cfg["REFRESH_X"] > 0):
            return
        human_click(cfg["REFRESH_X"], cfg["REFRESH_Y"], offset=3)
        time.sleep(random.uniform(3.5, 5.0))
        if cfg["USE_PLAY"] and cfg["PLAY_X"] > 0:
            human_click(cfg["PLAY_X"], cfg["PLAY_Y"], offset=8)
    except Exception as e:
        print(f"Refresh error: {e}")

def do_micro_move():
    try:
        cx, cy = pyautogui.position()
        pyautogui.moveTo(cx + random.randint(-2, 2),
                         cy + random.randint(-2, 2), duration=0.2)
        time.sleep(0.1)
        pyautogui.moveTo(cx, cy, duration=0.2)
    except Exception as e:
        print(f"Micro move error: {e}")

# ── Test helpers ────────────────────────────────────────────
def test_next():
    try: human_click(cfg["NEXT_X"], cfg["NEXT_Y"])
    except Exception as e: print(f"Next error: {e}")

def test_list():
    try: do_list_click()
    except Exception as e: print(f"List error: {e}")

# ── Shutdown timer ──────────────────────────────────────────
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
            shutdown_label.config(text=f"⏻ Shutdown σε: {h}:{m:02d}:{s:02d}",
                                  fg="#e67e22")
        except Exception as e:
            print(f"Shutdown error: {e}")
        time.sleep(1)

# ── Κύριος βρόχος ───────────────────────────────────────────
def move_and_click():
    global skip_next, skip_refresh
    try:
        refresh_end = time.time() + random.uniform(cfg["REFRESH_MIN"], cfg["REFRESH_MAX"])
        list_end    = time.time() + random.uniform(600, 1200)
        next_end    = time.time()       # κάνε NEXT αμέσως στην εκκίνηση
        last_micro  = time.time()

        if shutdown_at:
            threading.Thread(target=shutdown_timer, daemon=True).start()

        while running:
            try:
                now = time.time()

                # ── NEXT ───────────────────────────────────
                if cfg["USE_NEXT"] and cfg["NEXT_X"] > 0 and (now >= next_end or skip_next):
                    human_click(cfg["NEXT_X"], cfg["NEXT_Y"])
                    skip_next = False
                    next_end = time.time() + random.uniform(cfg["WAIT_MIN"], cfg["WAIT_MAX"])

                # ── LIST ───────────────────────────────────
                if cfg["USE_LIST"] and now >= list_end:
                    do_list_click()
                    list_end = time.time() + random.uniform(600, 1200)

                # ── REFRESH ────────────────────────────────
                if cfg["USE_REFRESH"] and (now >= refresh_end or skip_refresh):
                    skip_refresh = False
                    do_refresh()
                    refresh_end = time.time() + random.uniform(
                        cfg["REFRESH_MIN"], cfg["REFRESH_MAX"])

                # ── Micro-κίνηση κάθε 30 δευτ ──────────────
                if now - last_micro >= 30:
                    do_micro_move()
                    last_micro = time.time()

                # ── Ενημέρωση labels ───────────────────────
                now = time.time()

                if cfg["USE_NEXT"]:
                    nr = max(0, int(next_end - now))
                    countdown_label.config(text=f"▶ NEXT σε:    {nr//60}:{nr%60:02d}")
                else:
                    countdown_label.config(text="▶ NEXT:         Ανενεργό", fg="#888")

                if cfg["USE_LIST"]:
                    lr = max(0, int(list_end - now))
                    list_label.config(
                        text=f"☰ Λίστα σε:  {lr//60}:{lr%60:02d}", fg="#3498db")
                else:
                    list_label.config(text="☰ Λίστα:        Ανενεργή", fg="#888")

                if cfg["USE_REFRESH"]:
                    rr = max(0, int(refresh_end - now))
                    refresh_label.config(
                        text=f"↻ Refresh σε: {rr//60}:{rr%60:02d}", fg="#2ecc71")
                else:
                    refresh_label.config(text="↻ Refresh:     Ανενεργό", fg="#888")

            except Exception as e:
                print(f"Loop error: {e}")

            time.sleep(1)

    except Exception as e:
        print(f"Main error: {e}")
    finally:
        try:
            countdown_label.config(text="")
            list_label.config(text="")
            refresh_label.config(text="")
        except:
            pass

# ── Start / Stop ────────────────────────────────────────────
def toggle():
    global running, shutdown_at
    if cfg["NEXT_X"] == 0:
        messagebox.showerror("Σφάλμα",
                             "Πρώτα ρύθμισε τις συντεταγμένες\nαπό το κουμπί ⚙ Ρυθμίσεις!")
        return
    if not running:
        try:
            hours = float(hours_entry.get())
            if hours <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Σφάλμα", "Βάλε έγκυρο αριθμό ωρών (π.χ. 5.5)")
            return

        # Αποθήκευσε τιμές checkboxes στο cfg
        cfg["USE_NEXT"]    = next_var.get()
        cfg["USE_LIST"]    = list_var.get()
        cfg["USE_REFRESH"] = refresh_var.get()
        cfg["USE_PLAY"]    = play_var.get()
        save_config(cfg)

        shutdown_at = time.time() + hours * 3600
        running = True
        btn.config(text="STOP", bg="#e74c3c")
        status_label.config(text="Κατάσταση: Ενεργό", fg="#2ecc71")
        hours_entry.config(state="disabled")
        try:
            keyboard.add_hotkey("f9", force_next)
            keyboard.add_hotkey("f7", force_refresh)
        except:
            pass
        threading.Thread(target=move_and_click, daemon=True).start()
    else:
        running = False
        shutdown_at = None
        try:
            keyboard.remove_hotkey("f9")
            keyboard.remove_hotkey("f7")
        except:
            pass
        btn.config(text="START", bg="#2ecc71")
        status_label.config(text="Κατάσταση: Σταματημένο", fg="#e74c3c")
        countdown_label.config(text="")
        list_label.config(text="")
        refresh_label.config(text="")
        shutdown_label.config(text="")
        hours_entry.config(state="normal")
        try:
            os.system("shutdown /a 2>nul")
        except:
            pass

# ── Παράθυρο Ρυθμίσεων ─────────────────────────────────────
def open_settings():
    win = tk.Toplevel(root)
    win.title("⚙ Ρυθμίσεις V4")
    win.geometry("430x570")
    win.resizable(False, False)
    win.configure(bg="#2c2c2c")
    win.attributes("-topmost", True)

    # (label, key_x, key_y)
    # key_x = None → δεν εμφανίζεται X, δεν αποθηκεύεται X
    point_fields = [
        ("NEXT",            "NEXT_X",    "NEXT_Y"),
        ("PLAY",            "PLAY_X",    "PLAY_Y"),
        ("LIST (≡)",        "LIST_X",    "LIST_Y"),
        ("SLIDE Πάνω  ─┐",  "SLIDE_X",  "SLIDE_Y_MIN"),
        ("SLIDE Κάτω  ─┘",  None,        "SLIDE_Y_MAX"),
        ("REFRESH",         "REFRESH_X", "REFRESH_Y"),
        ("PROFILE",         "PROFILE_X", "PROFILE_Y"),
        ("LOGOUT",          "LOGOUT_X",  "LOGOUT_Y"),
    ]

    # all_entries: list of (cfg_key, widget) — duplicates OK
    all_entries = []

    tk.Label(win, text="⚙ Ρυθμίσεις V4.1", font=("Arial", 13, "bold"),
             bg="#2c2c2c", fg="white").pack(pady=8)
    tk.Label(win,
             text="Πάτα '🎯 Καταγραφή' και βάλε το ποντίκι στο σημείο μέσα σε 5 δευτ.\n"
                  "SLIDE Πάνω/Κάτω = πρώτο/τελευταίο slide μέσα στη λίστα (≡)",
             font=("Arial", 8), bg="#2c2c2c", fg="#aaa", justify="center").pack(pady=2)

    grid = tk.Frame(win, bg="#2c2c2c")
    grid.pack(padx=10, pady=4)

    capturing_label = tk.Label(win, text="", font=("Arial", 10, "bold"),
                                bg="#2c2c2c", fg="#f39c12")
    capturing_label.pack()

    for col, txt in enumerate(["Σημείο", "X", "Y", ""]):
        tk.Label(grid, text=txt, font=("Arial", 9, "bold"), bg="#2c2c2c",
                 fg="#aaa").grid(row=0, column=col, padx=4, pady=2)

    # SLIDE_X shared entry — stored when "SLIDE Πάνω" row is created
    slide_x_entry_ref = [None]

    def capture_point(label, key_x, key_y, ex, ey):
        def run():
            try:
                for i in range(5, 0, -1):
                    capturing_label.config(
                        text=f"Καταγραφή '{label}' σε {i}...", fg="#f39c12")
                    time.sleep(1)
                x, y = pyautogui.position()
                if ex and key_x:
                    ex.delete(0, tk.END)
                    ex.insert(0, str(x))
                    # αν είναι SLIDE Πάνω, ενημέρωσε και το κοινό SLIDE_X
                    if key_x == "SLIDE_X" and slide_x_entry_ref[0]:
                        slide_x_entry_ref[0].delete(0, tk.END)
                        slide_x_entry_ref[0].insert(0, str(x))
                if ey:
                    ey.delete(0, tk.END)
                    ey.insert(0, str(y))
                capturing_label.config(
                    text=f"✓ {label}: ({x if key_x else '↑'}, {y})", fg="#2ecc71")
            except Exception as e:
                capturing_label.config(text=f"Σφάλμα: {e}", fg="#e74c3c")
        threading.Thread(target=run, daemon=True).start()

    for i, (label, key_x, key_y) in enumerate(point_fields):
        row = i + 1
        # χρώμα γραμμής SLIDE
        fg_color = "#f39c12" if "SLIDE" in label else "#ccc"
        tk.Label(grid, text=label, font=("Arial", 9), bg="#2c2c2c",
                 fg=fg_color, width=14, anchor="w").grid(row=row, column=0, padx=4, pady=3)

        # ── X entry ──
        if key_x is not None:
            ex = tk.Entry(grid, width=6, font=("Arial", 9), bg="#444", fg="white",
                          insertbackground="white", justify="center", relief="flat")
            ex.insert(0, str(cfg.get(key_x, 0)))
            ex.grid(row=row, column=1, padx=3)
            all_entries.append((key_x, ex))
            if key_x == "SLIDE_X":
                slide_x_entry_ref[0] = ex
        else:
            # SLIDE Κάτω: δείχνουμε το ίδιο SLIDE_X entry (read-only οπτικά)
            ex_ph = tk.Label(grid, text="↑ ίδιο", font=("Arial", 8),
                             bg="#2c2c2c", fg="#888", width=6)
            ex_ph.grid(row=row, column=1, padx=3)
            ex = None  # δεν αποθηκεύεται X για SLIDE Κάτω

        # ── Y entry ──
        ey = tk.Entry(grid, width=6, font=("Arial", 9), bg="#444", fg="white",
                      insertbackground="white", justify="center", relief="flat")
        ey.insert(0, str(cfg.get(key_y, 0)))
        ey.grid(row=row, column=2, padx=3)
        all_entries.append((key_y, ey))

        tk.Button(grid, text="🎯 Καταγραφή", font=("Arial", 8),
                  bg="#e67e22", fg="white", relief="flat", cursor="hand2",
                  command=lambda lb=label, kx=key_x, ky=key_y, exx=ex, eyy=ey:
                      capture_point(lb, kx, ky, exx, eyy)
                  ).grid(row=row, column=3, padx=4)

    def save():
        try:
            for key, entry in all_entries:
                cfg[key] = int(entry.get())
            save_config(cfg)
            messagebox.showinfo("✓ Αποθήκευση", "Οι ρυθμίσεις αποθηκεύτηκαν!")
            win.destroy()
        except ValueError:
            messagebox.showerror("Σφάλμα", "Βάλε μόνο αριθμούς!")
        except Exception as e:
            messagebox.showerror("Σφάλμα", str(e))

    tk.Button(win, text="💾 Αποθήκευση", font=("Arial", 12, "bold"),
              bg="#2ecc71", fg="white", relief="flat", cursor="hand2",
              command=save).pack(pady=8)

# ── GUI ─────────────────────────────────────────────────────
root = tk.Tk()
root.title("Mouse Mover V4.1")
root.geometry("310x545")
root.resizable(False, False)
root.configure(bg="#2c2c2c")
root.attributes("-topmost", True)

tk.Label(root, text="Mouse Mover V4.1", font=("Arial", 16, "bold"),
         bg="#2c2c2c", fg="white").pack(pady=6)
tk.Label(root, text="✦ Bezier  ✦ Anti-Bot  ✦ Multi-Platform",
         font=("Arial", 9), bg="#2c2c2c", fg="#888").pack()

tk.Button(root, text="⚙ Ρυθμίσεις Συντεταγμένων", font=("Arial", 10),
          bg="#e67e22", fg="white", relief="flat", cursor="hand2",
          command=open_settings).pack(pady=6)

# ── Checklist Επιλογών ──────────────────────────────────────
opts_frame = tk.LabelFrame(root, text=" Επιλογές ", font=("Arial", 9),
                            bg="#2c2c2c", fg="#aaa", bd=1, relief="groove")
opts_frame.pack(padx=15, pady=2, fill="x")

next_var    = tk.BooleanVar(value=cfg.get("USE_NEXT",    True))
list_var    = tk.BooleanVar(value=cfg.get("USE_LIST",    True))
refresh_var = tk.BooleanVar(value=cfg.get("USE_REFRESH", True))
play_var    = tk.BooleanVar(value=cfg.get("USE_PLAY",    True))

row1 = tk.Frame(opts_frame, bg="#2c2c2c")
row1.pack(fill="x")
row2 = tk.Frame(opts_frame, bg="#2c2c2c")
row2.pack(fill="x")

_cb_style = dict(font=("Arial", 10), bg="#2c2c2c", fg="white",
                 selectcolor="#444", activebackground="#2c2c2c",
                 activeforeground="white")

tk.Checkbutton(row1, text="▶ NEXT κλικ",
               variable=next_var, **_cb_style).pack(side="left", padx=10, pady=3)
tk.Checkbutton(row1, text="☰ Λίστα (≡)",
               variable=list_var, **_cb_style).pack(side="left", padx=10, pady=3)
tk.Checkbutton(row2, text="↻ Refresh",
               variable=refresh_var, **_cb_style).pack(side="left", padx=10, pady=3)
tk.Checkbutton(row2, text="▶ Play μετά Refresh",
               variable=play_var, **_cb_style).pack(side="left", padx=10, pady=3)

# ── Shutdown & Status ───────────────────────────────────────
frame = tk.Frame(root, bg="#2c2c2c")
frame.pack(pady=4)
tk.Label(frame, text="Shutdown σε (ώρες):", font=("Arial", 10),
         bg="#2c2c2c", fg="#aaa").pack(side="left", padx=4)
hours_entry = tk.Entry(frame, width=6, font=("Arial", 11), bg="#444",
                        fg="white", insertbackground="white",
                        justify="center", relief="flat")
hours_entry.insert(0, "5.5")
hours_entry.pack(side="left")

status_label = tk.Label(root, text="Κατάσταση: Σταματημένο",
                         font=("Arial", 10), bg="#2c2c2c", fg="#e74c3c")
status_label.pack(pady=2)

countdown_label = tk.Label(root, text="", font=("Courier", 10),
                             bg="#2c2c2c", fg="#f39c12")
countdown_label.pack(pady=1)
list_label = tk.Label(root, text="", font=("Courier", 10),
                       bg="#2c2c2c", fg="#3498db")
list_label.pack(pady=1)
refresh_label = tk.Label(root, text="", font=("Courier", 10),
                          bg="#2c2c2c", fg="#2ecc71")
refresh_label.pack(pady=1)
shutdown_label = tk.Label(root, text="", font=("Arial", 10),
                           bg="#2c2c2c", fg="#e67e22")
shutdown_label.pack(pady=1)

btn = tk.Button(root, text="START", font=("Arial", 14, "bold"),
                bg="#2ecc71", fg="white", width=12, relief="flat",
                cursor="hand2", command=toggle)
btn.pack(pady=6)

tk.Label(root, text="F9=NEXT  F7=Refresh  |  Γωνία=stop",
         font=("Arial", 8), bg="#2c2c2c", fg="#888").pack()

btn_frame = tk.Frame(root, bg="#2c2c2c")
btn_frame.pack(pady=3)
for txt, color, func in [
    ("Test Next",    "#e74c3c", test_next),
    ("Test List",    "#2980b9", test_list),
    ("Test Refresh", "#16a085", do_refresh),
    ("Test Logout",  "#8e44ad", do_logout),
]:
    tk.Button(btn_frame, text=txt, font=("Arial", 9), bg=color, fg="white",
              relief="flat", cursor="hand2",
              command=lambda f=func: threading.Thread(target=f, daemon=True).start()
              ).pack(side="left", padx=2)

root.mainloop()
