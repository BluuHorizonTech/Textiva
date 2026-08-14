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
#  FILE PATH SETUP
# ──────────────────────────────────────────────────────────────────────────────
# os.path.abspath(__file__)  → full path of THIS script file
#   e.g. C:\Users\You\Desktop\text_expander.py
#
# os.path.dirname(...)  → folder that contains the script
#   e.g. C:\Users\You\Desktop\
#
# os.path.join(folder, "triggers.json")  → full path to triggers file
#   e.g. C:\Users\You\Desktop\triggers.json
#
# This means triggers.json always sits RIGHT NEXT TO the script,
# no matter where you run it from.
# ──────────────────────────────────────────────────────────────────────────────
TRIGGERS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "triggers.json"
)

DEFAULT_TRIGGERS = {
    "sp":  "Hey",
    "brb": "Be right back",
    "@@":  "you@email.com",
}

# ──────────────────────────────────────────────────────────────────────────────
#  BOUNDARY CHARS
# ──────────────────────────────────────────────────────────────────────────────
# These are the characters that "end" a word.
# When you type one of these AFTER a trigger word, expansion fires.
#
# Example: trigger = "brb"
#   You type: b r b [SPACE]   ← space is boundary → fires!
#   You type: b r b s         ← 's' is NOT boundary → no fire (word = "brbs")
#
# This prevents "sp" from firing inside words like "sport" or "special"
# ──────────────────────────────────────────────────────────────────────────────
BOUNDARY_CHARS = {
    " ", "\n", "\t",
    ".", ",", "!", "?", ";", ":", "-",
    ")", "]", "}", "'", '"',
}

# ──────────────────────────────────────────────────────────────────────────────
#  KEY NAME → ACTUAL CHARACTER MAP
# ──────────────────────────────────────────────────────────────────────────────
# The `keyboard` library gives us KEY NAMES like "space", "enter", "tab"
# but we need the actual CHARACTER they represent (" ", "\n", "\t")
# so we can check them against BOUNDARY_CHARS
# ──────────────────────────────────────────────────────────────────────────────
KEY_TO_CHAR = {
    "space": " ",
    "enter": "\n",
    "tab":   "\t",
}


# ──────────────────────────────────────────────────────────────────────────────
#  LOAD / SAVE TRIGGERS
# ──────────────────────────────────────────────────────────────────────────────
# JSON (JavaScript Object Notation) is just a simple text format
# that stores key-value pairs like a dictionary.
#
# triggers.json looks like this:
# {
#   "sp": "Hey",
#   "brb": "Be right back"
# }
#
# json.load()  → reads the file and turns it into a Python dict
# json.dump()  → takes a Python dict and writes it to file as JSON text
# ──────────────────────────────────────────────────────────────────────────────

def load_triggers() -> dict:
    """
    Loads triggers from triggers.json.
    If the file doesn't exist yet, creates it with default examples.
    Returns a Python dictionary like: {"sp": "Hey", "brb": "Be right back"}
    """
    if not os.path.exists(TRIGGERS_FILE):
        # File doesn't exist → create it with defaults
        with open(TRIGGERS_FILE, "w", encoding="utf-8") as f:
            # indent=2 makes it pretty/readable instead of one long line
            json.dump(DEFAULT_TRIGGERS, f, indent=2)
        print(f"[info] Created {TRIGGERS_FILE} with default examples.")

    with open(TRIGGERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_triggers(data: dict) -> None:
    """
    Saves the Python dictionary back to triggers.json.
    Called whenever user adds or deletes a trigger via the GUI.
    """
    with open(TRIGGERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────────────────────
#  GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────
# `triggers` → the dictionary of all shortcuts loaded from JSON
# `buffer`   → what the user has typed so far (we track it char by char)
#
# Why global?
#   The keyboard hook function (on_key_event) runs on EVERY keypress.
#   It needs to read and write `buffer` and `triggers` each time.
#   Globals are the simplest way to share state across function calls.
# ──────────────────────────────────────────────────────────────────────────────
triggers: dict = load_triggers()
buffer:   str  = ""


# ──────────────────────────────────────────────────────────────────────────────
#  EXPAND FUNCTION
# ──────────────────────────────────────────────────────────────────────────────
# This runs when we detect a trigger word followed by a boundary char.
#
# Example: user typed "brb " (brb + space)
#   Step 1: sleep a tiny bit so OS registers the space first
#   Step 2: send backspace 4 times  (b, r, b, space = 4 chars to erase)
#   Step 3: type "Be right back"
#   Step 4: re-send the space so it still acts as a separator
# ──────────────────────────────────────────────────────────────────────────────
def expand(word: str, boundary_char: str) -> None:
    """
    Deletes the typed trigger + boundary char, then types the replacement.

    word          = the trigger that was matched, e.g. "brb"
    boundary_char = the char that ended the word, e.g. " " or "\t"
    """
    # Small pause so the OS has time to process the boundary keypress
    # before we start sending backspaces. Without this, some apps get confused.
    time.sleep(0.05)

    # Erase:  trigger word (N chars)  +  the boundary char (1 char)
    erase_count = len(word) + 1
    for _ in range(erase_count):
        keyboard.send("backspace")
        time.sleep(0.01)   # tiny gap between each backspace for slow apps

    # Type the replacement text character by character
    # delay=0.01 adds 10ms between characters — more reliable than all at once
    keyboard.write(triggers[word], delay=0.01)

    # Re-send the boundary key so the user's workflow continues normally
    # e.g. if they pressed Enter to expand, Enter still moves to next line
    if boundary_char == "\n":
        keyboard.send("enter")
    elif boundary_char == "\t":
        keyboard.send("tab")
    elif boundary_char == " ":
        keyboard.send("space")
    else:
        # For punctuation like "." "," "!" etc.
        keyboard.write(boundary_char)


# ──────────────────────────────────────────────────────────────────────────────
#  KEYBOARD HOOK  (the heart of the whole program)
# ──────────────────────────────────────────────────────────────────────────────
# keyboard.hook(on_key_event) tells the OS:
#   "Call this function for EVERY key the user presses, anywhere on the system"
#
# event.name       → the name of the key, e.g. "a", "space", "backspace", "f1"
# event.event_type → "down" (key pressed) or "up" (key released)
#
# We only care about KEY DOWN events (when you press, not when you release)
# ──────────────────────────────────────────────────────────────────────────────
def on_key_event(event: keyboard.KeyboardEvent) -> None:
    """
    Called automatically on every keypress anywhere on the system.
    Maintains a rolling buffer of recent characters.
    Checks if buffer matches any trigger when a boundary char is pressed.
    """
    global buffer

    # Ignore key-UP events (we only care about key presses, not releases)
    if event.event_type != keyboard.KEY_DOWN:
        return

    key = event.name   # e.g. "a", "space", "tab", "backspace", "shift", "f1"

    # ── 1. IGNORE MODIFIER KEYS ────────────────────────────────────────────
    # Modifier keys (Shift, Ctrl, Alt, etc.) don't type characters.
    # If we let them through, they'd reset or corrupt our buffer.
    # ──────────────────────────────────────────────────────────────────────
    MODIFIERS = {
        "shift", "left shift", "right shift",
        "ctrl",  "left ctrl",  "right ctrl",
        "alt",   "left alt",   "right alt",
        "left windows", "right windows",
        "caps lock", "num lock", "scroll lock",
        "insert", "print screen", "pause",
    }
    if key in MODIFIERS:
        return   # do nothing, don't change the buffer

    # ── 2. BACKSPACE → SHRINK BUFFER ──────────────────────────────────────
    # If user presses backspace, they deleted the last character they typed,
    # so we remove the last character from our buffer too.
    #
    # Example: user typed "s", "p", backspace
    #   buffer goes: "" → "s" → "sp" → "s"
    # ──────────────────────────────────────────────────────────────────────
    if key == "backspace":
        buffer = buffer[:-1]   # [:-1] means "everything except the last char"
        return

    # ── 3. RESOLVE KEY NAME → ACTUAL CHARACTER ─────────────────────────────
    # "space" key  → " "  (a space character)
    # "enter" key  → "\n" (newline character)
    # "tab"   key  → "\t" (tab character)
    # "a"     key  → "a"  (single-char key names are already the character)
    # "f1"    key  → ""   (we don't know/care what char this is)
    # ──────────────────────────────────────────────────────────────────────
    if key in KEY_TO_CHAR:
        char = KEY_TO_CHAR[key]   # space / enter / tab
    elif len(key) == 1:
        char = key                # regular letter, digit, punctuation
    else:
        # F-keys, arrow keys, Home, End, Page Up, etc.
        # These don't type anything, so reset the buffer.
        buffer = ""
        return

    # ── 4. BOUNDARY CHARACTER → CHECK FOR TRIGGER ─────────────────────────
    # If the character the user just typed is a "boundary" (space, enter, tab,
    # punctuation), check whether what they typed BEFORE it is a trigger word.
    # ──────────────────────────────────────────────────────────────────────
    if char in BOUNDARY_CHARS:
        word   = buffer       # everything typed before this boundary char
        buffer = ""           # reset buffer BEFORE calling expand (safety)

        if word in triggers:
            # We have a match! Run expand in a NEW THREAD so the keyboard
            # hook returns immediately and doesn't block other keypresses.
            t = threading.Thread(target=expand, args=(word, char), daemon=True)
            t.start()

        # Whether we expanded or not, the boundary char was already sent
        # by the OS, so we just return. expand() will re-send it after typing.
        return

    # ── 5. NORMAL CHARACTER → ADD TO BUFFER ──────────────────────────────
    buffer += char

    # Safety: keep buffer from growing forever if user types without stopping
    # Max size = length of the longest trigger + a small margin
    MAX_BUFFER = max((len(k) for k in triggers), default=40) + 5
    if len(buffer) > MAX_BUFFER:
        # Keep only the most recent MAX_BUFFER characters
        buffer = buffer[-MAX_BUFFER:]


# ──────────────────────────────────────────────────────────────────────────────
#  MANAGER GUI
# ──────────────────────────────────────────────────────────────────────────────
# Built with tkinter — Python's built-in GUI library (no extra install needed)
#
# Layout:
#   ┌─────────────────────────────────┐
#   │  [Trigger]  [Replacement     ]  │  ← input fields
#   │  [     Add / Update Button   ]  │
#   ├─────────────────────────────────┤
#   │  trigger1  │  replacement1      │  ← table (Treeview widget)
#   │  trigger2  │  replacement2      │
#   │  ...                            │
#   ├─────────────────────────────────┤
#   │  [Delete Selected]              │
#   └─────────────────────────────────┘
# ──────────────────────────────────────────────────────────────────────────────
class ManagerGUI:
    """
    A simple window that lets users:
      - See all current triggers in a table
      - Add new trigger → replacement pairs
      - Delete existing ones
    No JSON knowledge required!
    """

    def __init__(self, root: tk.Tk):
        """
        Called when the GUI is created.
        Sets up all the widgets (buttons, labels, input boxes, table).

        root = the main Tkinter window object
        """
        self.root = root
        self.root.title("Text Expander — Trigger Manager")
        self.root.resizable(False, False)           # fixed size window
        self.root.configure(bg="#f0f0f0")           # light gray background

        # ── TITLE LABEL ────────────────────────────────────────────────
        title = tk.Label(
            root,
            text="⌨  Text Expander Manager",
            font=("Segoe UI", 14, "bold"),
            bg="#f0f0f0",
            fg="#222222",
        )
        title.grid(row=0, column=0, columnspan=3, pady=(14, 4), padx=16)

        # ── SUBTITLE / INSTRUCTIONS ────────────────────────────────────
        subtitle = tk.Label(
            root,
            text='Type a short "trigger" and what it should expand to, then click Add.',
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#555555",
        )
        subtitle.grid(row=1, column=0, columnspan=3, pady=(0, 10), padx=16)

        # ── INPUT SECTION ──────────────────────────────────────────────
        # tk.Frame = invisible container to group widgets together
        input_frame = tk.Frame(root, bg="#f0f0f0")
        input_frame.grid(row=2, column=0, columnspan=3, padx=16, pady=4, sticky="ew")

        # "Trigger" label + entry box
        tk.Label(
            input_frame,
            text="Trigger word:",
            font=("Segoe UI", 10, "bold"),
            bg="#f0f0f0",
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))

        # tk.StringVar = a special string that auto-updates the UI when changed
        self.trigger_var = tk.StringVar()
        trigger_entry = tk.Entry(
            input_frame,
            textvariable=self.trigger_var,
            font=("Segoe UI", 11),
            width=14,
            relief="solid",
            bd=1,
        )
        trigger_entry.grid(row=0, column=1, padx=(0, 14))
        # Pressing Enter in trigger box moves focus to replacement box
        trigger_entry.bind("<Return>", lambda e: replacement_entry.focus())

        # "Replacement" label + entry box
        tk.Label(
            input_frame,
            text="Expands to:",
            font=("Segoe UI", 10, "bold"),
            bg="#f0f0f0",
        ).grid(row=0, column=2, sticky="w", padx=(0, 6))

        self.replacement_var = tk.StringVar()
        replacement_entry = tk.Entry(
            input_frame,
            textvariable=self.replacement_var,
            font=("Segoe UI", 11),
            width=30,
            relief="solid",
            bd=1,
        )
        replacement_entry.grid(row=0, column=3, padx=(0, 14))
        # Pressing Enter in replacement box clicks the Add button
        replacement_entry.bind("<Return>", lambda e: self.add_trigger())

        # ── ADD BUTTON ─────────────────────────────────────────────────
        # command=self.add_trigger → calls that method when clicked
        add_btn = tk.Button(
            input_frame,
            text="➕  Add / Update",
            font=("Segoe UI", 10, "bold"),
            bg="#0078d4",          # Windows blue
            fg="white",
            activebackground="#005fa3",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",        # cursor becomes a pointer on hover
            command=self.add_trigger,
        )
        add_btn.grid(row=0, column=4)

        # ── SEPARATOR LINE ─────────────────────────────────────────────
        ttk.Separator(root, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", padx=16, pady=8
        )

        # ── TABLE (TREEVIEW) ───────────────────────────────────────────
        # ttk.Treeview is Tkinter's table/list widget.
        # columns=("trigger", "replacement") defines 2 columns.
        # show="headings" hides the default blank first column.
        table_frame = tk.Frame(root, bg="#f0f0f0")
        table_frame.grid(row=4, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="nsew")

        self.tree = ttk.Treeview(
            table_frame,
            columns=("trigger", "replacement"),
            show="headings",
            height=10,             # show 10 rows before scrolling
            selectmode="browse",   # only one row selectable at a time
        )

        # Define column headers and widths
        self.tree.heading("trigger",     text="Trigger Word")
        self.tree.heading("replacement", text="Expands To")
        self.tree.column("trigger",      width=130, anchor="w")
        self.tree.column("replacement",  width=380, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar — linked to the treeview's y-scroll
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # When user clicks a row, auto-fill the input boxes with that row's data
        # so they can edit it easily
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # ── DELETE BUTTON ─────────────────────────────────────────────
        del_btn = tk.Button(
            root,
            text="🗑  Delete Selected",
            font=("Segoe UI", 10),
            bg="#d13438",          # red
            fg="white",
            activebackground="#a10d0d",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.delete_trigger,
        )
        del_btn.grid(row=5, column=0, columnspan=3, pady=(0, 14))

        # ── STATUS BAR ────────────────────────────────────────────────
        # Shows feedback messages at the bottom ("Added!", "Deleted!", etc.)
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = tk.Label(
            root,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#e0e0e0",
            fg="#333333",
            anchor="w",
            padx=10,
        )
        status_bar.grid(row=6, column=0, columnspan=3, sticky="ew")

        # Load existing triggers into the table on startup
        self.refresh_table()

    # ── METHODS ────────────────────────────────────────────────────────────

    def refresh_table(self) -> None:
        """
        Clears the table and re-fills it from the `triggers` global dict.
        Called after every add/delete so the table stays up to date.
        """
        # Delete all existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert one row per trigger
        for trigger_word, replacement_text in sorted(triggers.items()):
            # insert("", "end", values=(...)) adds a row at the end
            self.tree.insert("", "end", values=(trigger_word, replacement_text))

    def on_row_select(self, event) -> None:
        """
        When user clicks a row in the table,
        auto-fill the input boxes with that row's data.
        This lets them edit an existing trigger easily.
        """
        selected = self.tree.selection()       # list of selected row IDs
        if not selected:
            return
        row_id = selected[0]
        values = self.tree.item(row_id, "values")  # (trigger, replacement)
        if values:
            self.trigger_var.set(values[0])         # fill trigger input box
            self.replacement_var.set(values[1])     # fill replacement input box

    def add_trigger(self) -> None:
        """
        Reads the trigger + replacement input boxes.
        Validates them (not empty).
        Adds/updates the entry in the global `triggers` dict.
        Saves to JSON.
        Refreshes the table.
        """
        global triggers

        # .get() reads the current text from a StringVar
        # .strip() removes leading/trailing spaces
        trigger_word     = self.trigger_var.get().strip()
        replacement_text = self.replacement_var.get().strip()

        # ── VALIDATION ─────────────────────────────────────────────────
        if not trigger_word:
            messagebox.showwarning("Missing Input", "Please enter a trigger word.")
            return
        if not replacement_text:
            messagebox.showwarning("Missing Input", "Please enter the replacement text.")
            return

        # ── UPDATE DICT + SAVE ─────────────────────────────────────────
        action = "Updated" if trigger_word in triggers else "Added"
        triggers[trigger_word] = replacement_text
        save_triggers(triggers)

        # ── REFRESH UI ─────────────────────────────────────────────────
        self.refresh_table()
        self.trigger_var.set("")        # clear input boxes
        self.replacement_var.set("")
        self.status_var.set(f"✅  {action}: '{trigger_word}'  →  '{replacement_text}'")

    def delete_trigger(self) -> None:
        """
        Deletes the currently selected row from triggers dict + JSON file.
        Shows a confirmation dialog before deleting.
        """
        global triggers

        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Nothing Selected", "Click a row in the table first.")
            return

        row_id = selected[0]
        trigger_word = self.tree.item(row_id, "values")[0]

        # Ask for confirmation before deleting
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Delete trigger '{trigger_word}'?\n\nThis cannot be undone.",
        )
        if not confirmed:
            return

        # Remove from dict, save, refresh
        del triggers[trigger_word]
        save_triggers(triggers)
        self.refresh_table()
        self.trigger_var.set("")
        self.replacement_var.set("")
        self.status_var.set(f"🗑  Deleted: '{trigger_word}'")


# ──────────────────────────────────────────────────────────────────────────────
#  WINDOWS STARTUP HELPERS
# ──────────────────────────────────────────────────────────────────────────────
# The Windows "Startup" folder is a special folder.
# Any shortcut or script placed there runs automatically when you log in.
#
# Path: C:\Users\<You>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
#
# We place a tiny .vbs (Visual Basic Script) file there.
# VBS can run programs silently (no console window) using window-style 0.
# ──────────────────────────────────────────────────────────────────────────────
STARTUP_FOLDER = os.path.join(
    os.getenv("APPDATA", ""),   # e.g. C:\Users\You\AppData\Roaming
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
)
LAUNCHER_NAME = "text_expander_launcher.vbs"


def install_startup() -> None:
    """
    Creates a hidden launcher in the Windows Startup folder.
    Uses pythonw.exe (no console window) so nothing flashes on login.
    Also launches the expander right now without waiting for a reboot.
    """
    # pythonw.exe = Python without a console window
    # We replace "python.exe" with "pythonw.exe" in the current Python path
    pythonw = sys.executable
    candidate = pythonw.replace("python.exe", "pythonw.exe")
    if os.path.exists(candidate):
        pythonw = candidate

    script_path = os.path.abspath(__file__)

    # VBS script content:
    # Chr(34) = the " character (avoids quote-inside-quote issues)
    # window-style 0 = hidden window
    # False = don't wait for the program to finish
    vbs_lines = [
        'Set WshShell = CreateObject("WScript.Shell")',
        f'WshShell.Run Chr(34) & "{pythonw}" & Chr(34) & " " & Chr(34) & "{script_path}" & Chr(34), 0, False',
    ]
    vbs_content = "\r\n".join(vbs_lines) + "\r\n"

    os.makedirs(STARTUP_FOLDER, exist_ok=True)
    launcher_path = os.path.join(STARTUP_FOLDER, LAUNCHER_NAME)

    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    print(f"[ok] Startup launcher written to:\n     {launcher_path}")
    print("[ok] Will auto-start (hidden) on every login.")

    # Launch it right now in the background so you don't need to reboot
    import subprocess
    subprocess.Popen(
        [pythonw, script_path],
        creationflags=0x00000008,   # DETACHED_PROCESS flag
        close_fds=True,
    )
    print("[ok] Running in background now. You can close this window.")


def uninstall_startup() -> None:
    """Removes the startup launcher if it exists."""
    launcher_path = os.path.join(STARTUP_FOLDER, LAUNCHER_NAME)
    if os.path.exists(launcher_path):
        os.remove(launcher_path)
        print(f"[ok] Removed: {launcher_path}")
    else:
        print("[info] Not found — already removed?")


# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
# When you run:  python text_expander.py
#   → main() is called
#   → keyboard hook is started in a background THREAD
#   → GUI window opens
#
# Why a thread for the keyboard hook?
#   keyboard.wait() blocks forever (it waits for keypresses).
#   The GUI also needs to run its own loop (root.mainloop()).
#   Two "forever loops" can't both run on the same thread.
#   Solution: run the keyboard hook on a background daemon thread,
#             and the GUI on the main thread.
#
# daemon=True means: if the main program (GUI) closes,
#   the background thread also dies automatically.
# ──────────────────────────────────────────────────────────────────────────────
def start_keyboard_hook() -> None:
    """Registers the keyboard hook and blocks forever. Runs in a thread."""
    keyboard.hook(on_key_event)
    keyboard.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple Windows text expander")
    parser.add_argument(
        "--install-startup", action="store_true",
        help="Install to Windows startup (runs hidden on every login)",
    )
    parser.add_argument(
        "--uninstall-startup", action="store_true",
        help="Remove from Windows startup",
    )
    args = parser.parse_args()

    # Handle startup install/uninstall commands (no GUI needed)
    if args.uninstall_startup:
        uninstall_startup()
        return

    if args.install_startup:
        install_startup()
        return

    # ── Normal run: start hook + open GUI ─────────────────────────────
    print("=" * 55)
    print(" Text Expander — starting")
    print("=" * 55)
    print(f"Triggers file : {TRIGGERS_FILE}")
    print(f"Loaded        : {len(triggers)} trigger(s)")
    for k, v in triggers.items():
        print(f"  {k!r:>15}  →  {v!r}")
    print()

    # Start keyboard hook in background thread
    hook_thread = threading.Thread(target=start_keyboard_hook, daemon=True)
    hook_thread.start()
    print("[ok] Keyboard hook active — expander is running.")

    # Open the GUI on the main thread
    root = tk.Tk()
    app  = ManagerGUI(root)
    root.mainloop()   # blocks here until user closes the window

    # When window closes, daemon thread dies automatically → clean exit
    print("[info] GUI closed. Exiting.")


if __name__ == "__main__":
    main()