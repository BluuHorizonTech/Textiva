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
#  THEME
# ──────────────────────────────────────────────────────────────────────────────

C = {
    "bg":             "#0f1117",
    "surface":        "#1a1d27",
    "surface2":       "#22263a",
    "border":         "#2e3248",
    "accent":         "#6c63ff",
    "accent_hover":   "#857dff",
    "accent_press":   "#5348d4",
    "danger":         "#ff4d6d",
    "danger_hover":   "#ff6b84",
    "danger_press":   "#cc2244",
    "success":        "#00d4aa",
    "text_primary":   "#e8eaf6",
    "text_secondary": "#8b90a8",
    "text_muted":     "#555978",
    "row_even":       "#1a1d27",
    "row_odd":        "#1e2133",
    "row_selected":   "#2d2b55",
    "row_sel_fg":     "#c9c6ff",
}

FONT_TITLE  = ("Segoe UI", 17, "bold")
FONT_ENTRY  = ("Segoe UI", 11)
FONT_BTN    = ("Segoe UI", 10, "bold")
FONT_MICRO  = ("Segoe UI",  8, "bold")
FONT_SMALL  = ("Segoe UI",  9)
FONT_TABLE  = ("Segoe UI", 10)
FONT_TABLE_H= ("Segoe UI", 10, "bold")


# ──────────────────────────────────────────────────────────────────────────────
#  MODERN BUTTON  (Frame + Label — no Canvas, no Tcl naming issues)
# ──────────────────────────────────────────────────────────────────────────────

class ModernButton(tk.Frame):
    """
    Flat pill-style button built from a Frame + Label.
    Uses a solid background colour with hover/press states.
    No Canvas → no Tcl widget-name conflicts.
    """

    def __init__(
        self, parent,
        text="",
        command=None,
        bg=C["accent"],
        hover=C["accent_hover"],
        press=C["accent_press"],
        fg=C["text_primary"],
        font=FONT_BTN,
        padx=18, pady=8,
        **kwargs,
    ):
        super().__init__(parent, bg=bg, cursor="hand2", **kwargs)

        self._bg    = bg
        self._hover = hover
        self._press = press
        self._cmd   = command

        self._label = tk.Label(
            self,
            text=text,
            font=font,
            bg=bg,
            fg=fg,
            padx=padx,
            pady=pady,
            cursor="hand2",
        )
        self._label.pack(fill="both", expand=True)

        for widget in (self, self._label):
            widget.bind("<Enter>",           self._on_enter)
            widget.bind("<Leave>",           self._on_leave)
            widget.bind("<ButtonPress-1>",   self._on_press)
            widget.bind("<ButtonRelease-1>", self._on_release)

    def _set_color(self, color: str) -> None:
        self.config(bg=color)
        self._label.config(bg=color)

    def _on_enter(self, _):   self._set_color(self._hover)
    def _on_leave(self, _):   self._set_color(self._bg)
    def _on_press(self, _):   self._set_color(self._press)
    def _on_release(self, _):
        self._set_color(self._hover)
        if self._cmd:
            self._cmd()


# ──────────────────────────────────────────────────────────────────────────────
#  MODERN ENTRY  (Frame wrapper for dark fill + focus border)
# ──────────────────────────────────────────────────────────────────────────────

class ModernEntry(tk.Frame):
    """
    Entry with dark fill and a coloured highlight border on focus.
    """

    def __init__(self, parent, textvariable=None, width=20, **kwargs):
        super().__init__(
            parent,
            bg=C["surface2"],
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
            highlightthickness=1,
            **kwargs,
        )
        self._var = textvariable or tk.StringVar()

        self.entry = tk.Entry(
            self,
            textvariable=self._var,
            font=FONT_ENTRY,
            bg=C["surface2"],
            fg=C["text_primary"],
            insertbackground=C["accent"],
            relief="flat",
            bd=6,
            width=width,
        )
        self.entry.pack(fill="both", expand=True)

        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _):
        self.config(highlightbackground=C["accent"], highlightthickness=2)

    def _on_focus_out(self, _):
        self.config(highlightbackground=C["border"], highlightthickness=1)

    # proxy so callers can treat this like a plain Entry
    def bind(self, seq=None, func=None, add=None):
        super().bind(seq, func, add)
        if hasattr(self, "entry"):
            self.entry.bind(seq, func, add)

    def get(self):       return self._var.get()
    def set(self, val):  self._var.set(val)
    def focus(self):     self.entry.focus()


# ──────────────────────────────────────────────────────────────────────────────
#  GUI
# ──────────────────────────────────────────────────────────────────────────────

class ManagerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Text Expander")
        self.root.resizable(False, False)
        self.root.configure(bg=C["bg"])
        self.root.geometry("700x560")

        self._style_treeview()
        self._build_header()
        self._build_input_card()
        self._build_table_card()
        self._build_status_bar()

        self.refresh_table()

    # ── header ─────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["surface"])
        hdr.pack(fill="x")

        # 3-px accent stripe
        tk.Frame(hdr, bg=C["accent"], height=3).pack(fill="x")

        inner = tk.Frame(hdr, bg=C["surface"])
        inner.pack(fill="x", padx=24, pady=14)

        tk.Label(
            inner,
            text="⌨  Text Expander",
            font=FONT_TITLE,
            bg=C["surface"],
            fg=C["text_primary"],
        ).pack(side="left")

        tk.Label(
            inner,
            text="  —  type a trigger then a space / punctuation to expand",
            font=FONT_SMALL,
            bg=C["surface"],
            fg=C["text_secondary"],
        ).pack(side="left", pady=(5, 0))

    # ── input card ─────────────────────────────────────────────────────
    def _build_input_card(self):
        card = tk.Frame(
            self.root,
            bg=C["surface"],
            highlightbackground=C["border"],
            highlightthickness=1,
        )
        card.pack(fill="x", padx=20, pady=(16, 8))

        inner = tk.Frame(card, bg=C["surface"])
        inner.pack(fill="x", padx=20, pady=16)

        # ── trigger label + entry ─────────────────────────────────────
        tk.Label(
            inner, text="TRIGGER WORD",
            font=FONT_MICRO, bg=C["surface"], fg=C["accent"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.trigger_var = tk.StringVar()
        self.trigger_entry = ModernEntry(
            inner, textvariable=self.trigger_var, width=14,
        )
        self.trigger_entry.grid(row=1, column=0, padx=(0, 12), sticky="ew")
        self.trigger_entry.entry.bind(
            "<Return>", lambda e: self.replacement_entry.focus()
        )

        # ── arrow ─────────────────────────────────────────────────────
        tk.Label(
            inner, text="→",
            font=("Segoe UI", 16), bg=C["surface"], fg=C["text_muted"],
        ).grid(row=0, column=1, rowspan=2, padx=10)

        # ── replacement label + entry ─────────────────────────────────
        tk.Label(
            inner, text="EXPANDS TO",
            font=FONT_MICRO, bg=C["surface"], fg=C["accent"],
        ).grid(row=0, column=2, sticky="w", pady=(0, 4))

        self.replacement_var = tk.StringVar()
        self.replacement_entry = ModernEntry(
            inner, textvariable=self.replacement_var, width=30,
        )
        self.replacement_entry.grid(row=1, column=2, padx=(0, 16), sticky="ew")
        self.replacement_entry.entry.bind("<Return>", lambda e: self.add_trigger())

        # ── add button ────────────────────────────────────────────────
        add_btn = ModernButton(
            inner,
            text="＋  Add / Update",
            command=self.add_trigger,
            bg=C["accent"],
            hover=C["accent_hover"],
            press=C["accent_press"],
        )
        add_btn.grid(row=0, column=3, rowspan=2, padx=(4, 0), sticky="ns")

        inner.columnconfigure(2, weight=1)

    # ── table card ─────────────────────────────────────────────────────
    def _build_table_card(self):
        card = tk.Frame(
            self.root,
            bg=C["surface"],
            highlightbackground=C["border"],
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # card sub-header
        sub_hdr = tk.Frame(card, bg=C["surface2"])
        sub_hdr.pack(fill="x")
        tk.Label(
            sub_hdr, text="  SAVED TRIGGERS",
            font=FONT_MICRO, bg=C["surface2"], fg=C["text_muted"], pady=7,
        ).pack(side="left")

        # treeview
        tree_wrap = tk.Frame(card, bg=C["surface"])
        tree_wrap.pack(fill="both", expand=True, padx=12, pady=(8, 0))

        self.tree = ttk.Treeview(
            tree_wrap,
            columns=("trigger", "replacement"),
            show="headings",
            height=10,
            selectmode="browse",
            style="Modern.Treeview",
        )
        self.tree.heading("trigger",     text="Trigger")
        self.tree.heading("replacement", text="Expands To")
        self.tree.column("trigger",      width=150, anchor="w", minwidth=80)
        self.tree.column("replacement",  width=440, anchor="w", minwidth=200)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        sb = ttk.Scrollbar(
            tree_wrap, orient="vertical",
            command=self.tree.yview,
            style="Modern.Vertical.TScrollbar",
        )
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # action row
        action_row = tk.Frame(card, bg=C["surface"])
        action_row.pack(fill="x", padx=12, pady=10)

        ModernButton(
            action_row,
            text="🗑  Delete Selected",
            command=self.delete_trigger,
            bg=C["danger"],
            hover=C["danger_hover"],
            press=C["danger_press"],
        ).pack(side="right")

    # ── status bar ─────────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=C["surface2"], height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        # green "active" dot
        dot = tk.Canvas(
            bar, width=10, height=10,
            bg=C["surface2"], highlightthickness=0,
        )
        dot.pack(side="left", padx=(12, 5), pady=9)
        dot.create_oval(1, 1, 9, 9, fill=C["success"], outline="")

        tk.Label(
            bar, text="Hook active  •",
            font=FONT_SMALL, bg=C["surface2"], fg=C["text_muted"],
        ).pack(side="left")

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(
            bar,
            textvariable=self.status_var,
            font=FONT_SMALL,
            bg=C["surface2"],
            fg=C["text_secondary"],
        ).pack(side="left", padx=(6, 0))

    # ── treeview / scrollbar styles ────────────────────────────────────
    def _style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Modern.Treeview",
            background=C["row_even"],
            foreground=C["text_primary"],
            fieldbackground=C["row_even"],
            borderwidth=0,
            relief="flat",
            rowheight=32,
            font=FONT_TABLE,
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=C["surface2"],
            foreground=C["text_secondary"],
            borderwidth=0,
            relief="flat",
            font=FONT_TABLE_H,
            padding=(8, 6),
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", C["row_selected"])],
            foreground=[("selected", C["row_sel_fg"])],
        )
        style.map(
            "Modern.Treeview.Heading",
            background=[("active", C["surface2"])],
        )
        style.configure(
            "Modern.Vertical.TScrollbar",
            background=C["surface2"],
            troughcolor=C["surface"],
            borderwidth=0,
            arrowsize=0,
            width=6,
        )
        style.map(
            "Modern.Vertical.TScrollbar",
            background=[("active", C["border"])],
        )

    # ── logic  ──────────────────────────────────────────────
    def refresh_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, (tw, rt) in enumerate(sorted(triggers.items())):
            tag = "odd" if i % 2 else "even"
            self.tree.insert("", "end", values=(tw, rt), tags=(tag,))
        self.tree.tag_configure("even", background=C["row_even"])
        self.tree.tag_configure("odd",  background=C["row_odd"])

    def on_row_select(self, _) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if vals:
            self.trigger_var.set(vals[0])
            self.replacement_var.set(vals[1])

    def add_trigger(self) -> None:
        global triggers
        tw = self.trigger_var.get().strip()
        rt = self.replacement_var.get().strip()

        if not tw:
            messagebox.showwarning("Missing Input", "Please enter a trigger word.")
            return
        if not rt:
            messagebox.showwarning("Missing Input", "Please enter the replacement text.")
            return

        action = "Updated" if tw in triggers else "Added"
        triggers[tw] = rt
        save_triggers(triggers)
        self.refresh_table()
        self.trigger_var.set("")
        self.replacement_var.set("")
        self.status_var.set(f"✅  {action}: '{tw}'  →  '{rt}'")

    def delete_trigger(self) -> None:
        global triggers
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing Selected", "Click a row in the table first.")
            return

        tw = self.tree.item(sel[0], "values")[0]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete trigger '{tw}'?\n\nThis cannot be undone.",
        ):
            return

        del triggers[tw]
        save_triggers(triggers)
        self.refresh_table()
        self.trigger_var.set("")
        self.replacement_var.set("")
        self.status_var.set(f"🗑  Deleted: '{tw}'")


# ──────────────────────────────────────────────────────────────────────────────
#  STARTUP HELPERS  
# ──────────────────────────────────────────────────────────────────────────────

STARTUP_FOLDER = os.path.join(
    os.getenv("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
)
LAUNCHER_NAME = "text_expander_launcher.vbs"


def install_startup() -> None:
    pythonw = sys.executable
    candidate = pythonw.replace("python.exe", "pythonw.exe")
    if os.path.exists(candidate):
        pythonw = candidate

    script_path = os.path.abspath(__file__)
    vbs_lines = [
        'Set WshShell = CreateObject("WScript.Shell")',
        (
            f'WshShell.Run Chr(34) & "{pythonw}" & Chr(34)'
            f' & " " & Chr(34) & "{script_path}" & Chr(34)'
            f' & " --no-gui", 0, False'
        ),
    ]
    vbs_content = "\r\n".join(vbs_lines) + "\r\n"

    os.makedirs(STARTUP_FOLDER, exist_ok=True)
    launcher_path = os.path.join(STARTUP_FOLDER, LAUNCHER_NAME)
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    print(f"[ok] Installed to: {launcher_path}")
    print("[ok] On every login it will run SILENTLY in the background.")

    import subprocess
    subprocess.Popen(
        [pythonw, script_path, "--no-gui"],
        creationflags=0x00000008,
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
#  HOOK RUNNER  
# ──────────────────────────────────────────────────────────────────────────────

def run_hook_only() -> None:
    keyboard.hook(on_key_event)
    keyboard.wait()


# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT  
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Simple Windows text expander")
    parser.add_argument("--install-startup",   action="store_true")
    parser.add_argument("--uninstall-startup", action="store_true")
    parser.add_argument("--no-gui",            action="store_true")
    args = parser.parse_args()

    if args.uninstall_startup:
        uninstall_startup()
        return
    if args.install_startup:
        install_startup()
        return
    if args.no_gui:
        run_hook_only()
        return

    threading.Thread(target=run_hook_only, daemon=True).start()

    root = tk.Tk()
    ManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()