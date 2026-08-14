"""
Simple Text Expander for Windows
---------------------------------
SETUP:      pip install keyboard
RUN:        python text_expander.py              ← opens GUI to manage triggers
STARTUP:    python text_expander.py --install-startup   ← registers to run silently on login
REMOVE:     python text_expander.py --uninstall-startup
"""

import json
import os
import sys
import time
import argparse
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard

# ──────────────────────────────────────────────────────────────────────────────
#  PATHS & DEFAULTS
# ──────────────────────────────────────────────────────────────────────────────
TRIGGERS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "triggers.json"
)

DEFAULT_TRIGGERS = {
    "sp":  "Hey",
    "brb": "Be right back",
    "@@":  "you@email.com",
}

BOUNDARY_CHARS = {
    " ", "\n", "\t",
    ".", ",", "!", "?", ";", ":", "-",
    ")", "]", "}", "'", '"',
}

KEY_TO_CHAR = {
    "space": " ",
    "enter": "\n",
    "tab":   "\t",
}

# ──────────────────────────────────────────────────────────────────────────────
#  LOAD / SAVE TRIGGERS
# ──────────────────────────────────────────────────────────────────────────────

def load_triggers() -> dict:
    if not os.path.exists(TRIGGERS_FILE):
        with open(TRIGGERS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TRIGGERS, f, indent=2)
    with open(TRIGGERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_triggers(data: dict) -> None:
    with open(TRIGGERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────────────────────
#  GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────
triggers: dict = load_triggers()
buffer:   str  = ""

# ──────────────────────────────────────────────────────────────────────────────
#  EXPAND
# ──────────────────────────────────────────────────────────────────────────────

def expand(word: str, boundary_char: str) -> None:
    time.sleep(0.05)

    erase_count = len(word) + 1
    for _ in range(erase_count):
        keyboard.send("backspace")
        time.sleep(0.01)

    keyboard.write(triggers[word], delay=0.01)

    if boundary_char == "\n":
        keyboard.send("enter")
    elif boundary_char == "\t":
        keyboard.send("tab")
    elif boundary_char == " ":
        keyboard.send("space")
    else:
        keyboard.write(boundary_char)


# ──────────────────────────────────────────────────────────────────────────────
#  KEYBOARD HOOK
# ──────────────────────────────────────────────────────────────────────────────

def on_key_event(event: keyboard.KeyboardEvent) -> None:
    global buffer

    if event.event_type != keyboard.KEY_DOWN:
        return

    key = event.name

    MODIFIERS = {
        "shift", "left shift", "right shift",
        "ctrl",  "left ctrl",  "right ctrl",
        "alt",   "left alt",   "right alt",
        "left windows", "right windows",
        "caps lock", "num lock", "scroll lock",
        "insert", "print screen", "pause",
    }
    if key in MODIFIERS:
        return

    if key == "backspace":
        buffer = buffer[:-1]
        return

    if key in KEY_TO_CHAR:
        char = KEY_TO_CHAR[key]
    elif len(key) == 1:
        char = key
    else:
        buffer = ""
        return

    if char in BOUNDARY_CHARS:
        word   = buffer
        buffer = ""

        if word in triggers:
            t = threading.Thread(target=expand, args=(word, char), daemon=True)
            t.start()
        return

    buffer += char

    MAX_BUFFER = max((len(k) for k in triggers), default=40) + 5
    if len(buffer) > MAX_BUFFER:
        buffer = buffer[-MAX_BUFFER:]


# ──────────────────────────────────────────────────────────────────────────────
#  GUI
# ──────────────────────────────────────────────────────────────────────────────

class ManagerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Text Expander — Trigger Manager")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        tk.Label(
            root, text="⌨  Text Expander Manager",
            font=("Segoe UI", 14, "bold"), bg="#f0f0f0", fg="#222222",
        ).grid(row=0, column=0, columnspan=3, pady=(14, 4), padx=16)

        tk.Label(
            root,
            text='Type a trigger and what it should expand to, then click Add.',
            font=("Segoe UI", 9), bg="#f0f0f0", fg="#555555",
        ).grid(row=1, column=0, columnspan=3, pady=(0, 10), padx=16)

        # ── Input row ──────────────────────────────────────────────────
        input_frame = tk.Frame(root, bg="#f0f0f0")
        input_frame.grid(row=2, column=0, columnspan=3, padx=16, pady=4, sticky="ew")

        tk.Label(
            input_frame, text="Trigger word:",
            font=("Segoe UI", 10, "bold"), bg="#f0f0f0",
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.trigger_var = tk.StringVar()
        trigger_entry = tk.Entry(
            input_frame, textvariable=self.trigger_var,
            font=("Segoe UI", 11), width=14, relief="solid", bd=1,
        )
        trigger_entry.grid(row=0, column=1, padx=(0, 14))
        trigger_entry.bind("<Return>", lambda e: replacement_entry.focus())

        tk.Label(
            input_frame, text="Expands to:",
            font=("Segoe UI", 10, "bold"), bg="#f0f0f0",
        ).grid(row=0, column=2, sticky="w", padx=(0, 6))

        self.replacement_var = tk.StringVar()
        replacement_entry = tk.Entry(
            input_frame, textvariable=self.replacement_var,
            font=("Segoe UI", 11), width=30, relief="solid", bd=1,
        )
        replacement_entry.grid(row=0, column=3, padx=(0, 14))
        replacement_entry.bind("<Return>", lambda e: self.add_trigger())

        tk.Button(
            input_frame, text="➕  Add / Update",
            font=("Segoe UI", 10, "bold"),
            bg="#0078d4", fg="white",
            activebackground="#005fa3", activeforeground="white",
            relief="flat", padx=12, pady=4, cursor="hand2",
            command=self.add_trigger,
        ).grid(row=0, column=4)

        # ── Separator ──────────────────────────────────────────────────
        ttk.Separator(root, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=16, pady=8
        )

        # ── Table ──────────────────────────────────────────────────────
        table_frame = tk.Frame(root, bg="#f0f0f0")
        table_frame.grid(row=4, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="nsew")

        self.tree = ttk.Treeview(
            table_frame,
            columns=("trigger", "replacement"),
            show="headings", height=10, selectmode="browse",
        )
        self.tree.heading("trigger",     text="Trigger Word")
        self.tree.heading("replacement", text="Expands To")
        self.tree.column("trigger",      width=130, anchor="w")
        self.tree.column("replacement",  width=380, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # ── Delete button ──────────────────────────────────────────────
        tk.Button(
            root, text="🗑  Delete Selected",
            font=("Segoe UI", 10),
            bg="#d13438", fg="white",
            activebackground="#a10d0d", activeforeground="white",
            relief="flat", padx=12, pady=4, cursor="hand2",
            command=self.delete_trigger,
        ).grid(row=5, column=0, columnspan=3, pady=(0, 14))

        # ── Status bar ─────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(
            root, textvariable=self.status_var,
            font=("Segoe UI", 9), bg="#e0e0e0", fg="#333333",
            anchor="w", padx=10,
        ).grid(row=6, column=0, columnspan=3, sticky="ew")

        self.refresh_table()

    def refresh_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for trigger_word, replacement_text in sorted(triggers.items()):
            self.tree.insert("", "end", values=(trigger_word, replacement_text))

    def on_row_select(self, event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if values:
            self.trigger_var.set(values[0])
            self.replacement_var.set(values[1])

    def add_trigger(self) -> None:
        global triggers
        trigger_word     = self.trigger_var.get().strip()
        replacement_text = self.replacement_var.get().strip()

        if not trigger_word:
            messagebox.showwarning("Missing Input", "Please enter a trigger word.")
            return
        if not replacement_text:
            messagebox.showwarning("Missing Input", "Please enter the replacement text.")
            return

        action = "Updated" if trigger_word in triggers else "Added"
        triggers[trigger_word] = replacement_text
        save_triggers(triggers)
        self.refresh_table()
        self.trigger_var.set("")
        self.replacement_var.set("")
        self.status_var.set(f"✅  {action}: '{trigger_word}'  →  '{replacement_text}'")

    def delete_trigger(self) -> None:
        global triggers
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Nothing Selected", "Click a row in the table first.")
            return

        trigger_word = self.tree.item(selected[0], "values")[0]
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Delete trigger '{trigger_word}'?\n\nThis cannot be undone.",
        )
        if not confirmed:
            return

        del triggers[trigger_word]
        save_triggers(triggers)
        self.refresh_table()
        self.trigger_var.set("")
        self.replacement_var.set("")
        self.status_var.set(f"🗑  Deleted: '{trigger_word}'")


# ──────────────────────────────────────────────────────────────────────────────
#  STARTUP HELPERS
# ──────────────────────────────────────────────────────────────────────────────

STARTUP_FOLDER = os.path.join(
    os.getenv("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
)
LAUNCHER_NAME = "text_expander_launcher.vbs"


def install_startup() -> None:
    """
    Writes a .vbs launcher to the Windows Startup folder.
    The launcher runs:  pythonw.exe text_expander.py --no-gui
                                                      ^^^^^^^^
                        --no-gui = keyboard hook only, zero UI, zero console
    """
    pythonw = sys.executable
    candidate = pythonw.replace("python.exe", "pythonw.exe")
    if os.path.exists(candidate):
        pythonw = candidate

    script_path = os.path.abspath(__file__)

    # --no-gui flag tells the script to run silently (hook only, no window)
    vbs_lines = [
        'Set WshShell = CreateObject("WScript.Shell")',
        (
            f'WshShell.Run Chr(34) & "{pythonw}" & Chr(34)'
            f' & " " & Chr(34) & "{script_path}" & Chr(34)'
            f' & " --no-gui", 0, False'
            #                  ^^^^^^^^
            #   window-style 0 = completely hidden
            #   False = don't wait for it to finish
        ),
    ]
    vbs_content = "\r\n".join(vbs_lines) + "\r\n"

    os.makedirs(STARTUP_FOLDER, exist_ok=True)
    launcher_path = os.path.join(STARTUP_FOLDER, LAUNCHER_NAME)
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    print(f"[ok] Installed to: {launcher_path}")
    print("[ok] On every login it will run SILENTLY in the background.")
    print("[ok] No window. No tray icon. Just works.")
    print()
    print("[info] Starting the silent hook RIGHT NOW so you don't need to reboot...")

    # Launch a silent copy right now (--no-gui = no window at all)
    import subprocess
    subprocess.Popen(
        [pythonw, script_path, "--no-gui"],
        creationflags=0x00000008,   # DETACHED_PROCESS — fully independent process
        close_fds=True,
    )
    print("[ok] Done. Text expander is active.")


def uninstall_startup() -> None:
    launcher_path = os.path.join(STARTUP_FOLDER, LAUNCHER_NAME)
    if os.path.exists(launcher_path):
        os.remove(launcher_path)
        print(f"[ok] Removed: {launcher_path}")
    else:
        print("[info] Not found — already removed?")


# ──────────────────────────────────────────────────────────────────────────────
#  KEYBOARD HOOK RUNNER  (used in --no-gui / background mode)
# ──────────────────────────────────────────────────────────────────────────────

def run_hook_only() -> None:
    """
    Silent mode — no window, no console output.
    Just registers the keyboard hook and waits forever.
    This is what runs on startup in the background.
    """
    keyboard.hook(on_key_event)
    keyboard.wait()   # blocks forever, listening to every keypress


# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Simple Windows text expander")
    parser.add_argument(
        "--install-startup", action="store_true",
        help="Install to Windows startup (runs silently on every login)",
    )
    parser.add_argument(
        "--uninstall-startup", action="store_true",
        help="Remove from Windows startup",
    )
    parser.add_argument(
        "--no-gui", action="store_true",
        help="Run silently (keyboard hook only, no window) — used by the startup launcher",
    )
    args = parser.parse_args()

    # ── install / uninstall (no GUI needed) ───────────────────────────
    if args.uninstall_startup:
        uninstall_startup()
        return

    if args.install_startup:
        install_startup()
        return

    # ── SILENT BACKGROUND MODE  (--no-gui) ────────────────────────────
    # This is what the startup launcher calls.
    # Zero windows. Zero console. Just the keyboard hook running forever.
    if args.no_gui:
        run_hook_only()
        return

    # ── NORMAL MODE: GUI + hook thread ────────────────────────────────
    # Start hook in background thread so GUI can run on main thread
    hook_thread = threading.Thread(target=run_hook_only, daemon=True)
    hook_thread.start()

    root = tk.Tk()
    ManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()