import json
import os
import sys
import time
import argparse
import keyboard

TRIGGERS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "triggers.json"
)

DEFAULT_TRIGGERS = {
    "sp":  "Hey",
    "brb": "Be right back",
    "@@":  "you@email.com",
}

# Characters that mark the END of a trigger word
BOUNDARY_CHARS = {
    " ", "\n", "\t",
    ".", ",", "!", "?", ";", ":", "-",
    ")", "]", "}", "'", '"',
}

# Map key names -> actual characters
KEY_TO_CHAR = {
    "space": " ",
    "enter": "\n",
    "tab":   "\t",
}


# ──────────────────────────────────────────────
#  Load / save triggers
# ──────────────────────────────────────────────

def load_triggers() -> dict:
    if not os.path.exists(TRIGGERS_FILE):
        with open(TRIGGERS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TRIGGERS, f, indent=2)
        print(f"[info] Created {TRIGGERS_FILE} with default examples.")
    with open(TRIGGERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
#  Core expansion logic
# ──────────────────────────────────────────────

triggers: dict = load_triggers()
buffer:   str  = ""


def expand(word: str, boundary_char: str) -> None:
    """
    Delete (len(word) + 1) chars  ← the trigger + the boundary key
    Then type the replacement, then re-send the boundary key so the
    user's workflow isn't interrupted (cursor lands after replacement,
    with the space/tab/enter still applied).
    """
    # Small delay so the OS registers the boundary key before we start
    # sending backspaces — prevents race conditions in some apps.
    time.sleep(0.05)

    # How many chars to erase:
    #   the trigger word  +  the boundary char (1 key)
    erase_count = len(word) + 1
    for _ in range(erase_count):
        keyboard.send("backspace")
        time.sleep(0.01)   # tiny gap so fast apps keep up

    # Type the replacement text
    keyboard.write(triggers[word], delay=0.01)

    # Re-send the boundary key (so space/enter/tab still works normally)
    # Special case: don't re-send \n or \t as write() chars — use send()
    if boundary_char == "\n":
        keyboard.send("enter")
    elif boundary_char == "\t":
        keyboard.send("tab")
    elif boundary_char == " ":
        keyboard.send("space")
    else:
        keyboard.write(boundary_char)


def on_key_event(event: keyboard.KeyboardEvent) -> None:
    global buffer

    # Only act on key-down events
    if event.event_type != keyboard.KEY_DOWN:
        return

    key = event.name  # e.g. "a", "space", "tab", "backspace", "f1", "shift"

    # ── Ignore pure modifier keys ──────────────────────────────────────
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

    # ── Backspace: shrink buffer ───────────────────────────────────────
    if key == "backspace":
        buffer = buffer[:-1]
        return

    # ── Resolve the character this key produces ────────────────────────
    if key in KEY_TO_CHAR:
        char = KEY_TO_CHAR[key]          # space / enter / tab
    elif len(key) == 1:
        char = key                       # regular printable character
    else:
        # Arrow keys, F-keys, Home, End, etc. → reset buffer, no expand
        buffer = ""
        return

    # ── Boundary character hit → check for trigger ─────────────────────
    if char in BOUNDARY_CHARS:
        word   = buffer
        buffer = ""                      # reset BEFORE expanding (re-entrant safety)

        if word in triggers:
            expand(word, char)
        # If no match, just let the keystroke pass through normally
        return

    # ── Normal printable char → append to buffer ───────────────────────
    buffer += char

    # Safety cap — don't grow forever
    MAX_BUFFER = max((len(k) for k in triggers), default=40) + 5
    if len(buffer) > MAX_BUFFER:
        buffer = buffer[-MAX_BUFFER:]


# ──────────────────────────────────────────────
#  Windows startup helpers
# ──────────────────────────────────────────────

STARTUP_FOLDER = os.path.join(
    os.getenv("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
)
LAUNCHER_NAME = "text_expander_launcher.vbs"


def install_startup() -> None:
    """
    Drops a tiny .vbs file into the Windows Startup folder.
    Uses pythonw.exe so there's NO console window on login.
    """
    # Prefer pythonw.exe (no console); fall back to python.exe
    pythonw = sys.executable
    candidate = pythonw.replace("python.exe", "pythonw.exe")
    if os.path.exists(candidate):
        pythonw = candidate

    script_path = os.path.abspath(__file__)

    # The VBS runs the script hidden (window style 0 = hidden)
    vbs_lines = [
        'Set WshShell = CreateObject("WScript.Shell")',
        # window-style 0 = hidden, bWaitOnReturn = False
        f'WshShell.Run Chr(34) & "{pythonw}" & Chr(34) & " " & Chr(34) & "{script_path}" & Chr(34), 0, False',
    ]
    vbs_content = "\r\n".join(vbs_lines) + "\r\n"

    os.makedirs(STARTUP_FOLDER, exist_ok=True)
    launcher_path = os.path.join(STARTUP_FOLDER, LAUNCHER_NAME)

    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    print(f"[ok] Startup launcher written to:\n     {launcher_path}")
    print("[ok] The expander will start automatically (no window) on every login.")
    print("[info] Starting it now in the background as well...")

    # Also launch it right now so you don't have to log out/in
    import subprocess
    subprocess.Popen(
        [pythonw, script_path],
        creationflags=0x00000008,   # DETACHED_PROCESS
        close_fds=True,
    )
    print("[ok] Running in background. You can close this window.")


def uninstall_startup() -> None:
    launcher_path = os.path.join(STARTUP_FOLDER, LAUNCHER_NAME)
    if os.path.exists(launcher_path):
        os.remove(launcher_path)
        print(f"[ok] Removed: {launcher_path}")
    else:
        print("[info] Launcher not found — was it already removed?")


# ──────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────

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

    if args.uninstall_startup:
        uninstall_startup()
        return

    if args.install_startup:
        install_startup()
        return          # launcher already spawned a background copy

    # ── Normal run ────────────────────────────────────────────────────
    print("=" * 50)
    print(" Text Expander — running")
    print("=" * 50)
    print(f"Triggers file : {TRIGGERS_FILE}")
    print(f"Loaded        : {len(triggers)} trigger(s)\n")
    for k, v in triggers.items():
        print(f"  {k!r:>15}  →  {v!r}")
    print()
    print("Boundary keys : Space, Enter, Tab, punctuation")
    print("Press Ctrl+C to stop.\n")

    keyboard.hook(on_key_event)
    keyboard.wait()


if __name__ == "__main__":
    main()