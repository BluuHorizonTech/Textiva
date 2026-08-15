"""
Textiva — Smart Text Expander for Windows
------------------------------------------
SETUP:  pip install keyboard
RUN:    python main.py          ← opens GUI to manage triggers
"""

import json
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import winreg

# ──────────────────────────────────────────────────────────────────────────────
#  PATHS & DEFAULTS
# ──────────────────────────────────────────────────────────────────────────────

APP_NAME = "Textiva"

APP_DATA_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    APP_NAME,
)
os.makedirs(APP_DATA_DIR, exist_ok=True)

TRIGGERS_FILE = os.path.join(APP_DATA_DIR, "triggers.json")

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
#  RESOURCE PATH
# ──────────────────────────────────────────────────────────────────────────────

def resource_path(relative: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


# ──────────────────────────────────────────────────────────────────────────────
#  WINDOWS STARTUP
# ──────────────────────────────────────────────────────────────────────────────

_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_exe_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


def ensure_startup() -> None:
    try:
        exe_path     = _get_exe_path()
        wanted_value = f'"{exe_path}"'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_KEY, 0,
            winreg.KEY_READ | winreg.KEY_SET_VALUE,
        )

        try:
            current, _ = winreg.QueryValueEx(key, APP_NAME)
            if current == wanted_value:
                winreg.CloseKey(key)
                return
        except FileNotFoundError:
            pass

        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, wanted_value)
        winreg.CloseKey(key)
    except OSError:
        pass


# ──────────────────────────────────────────────────────────────────────────────
#  LOAD / SAVE TRIGGERS
# ──────────────────────────────────────────────────────────────────────────────

def load_triggers() -> dict:
    if not os.path.exists(TRIGGERS_FILE):
        _write_triggers(DEFAULT_TRIGGERS)
        return dict(DEFAULT_TRIGGERS)
    try:
        with open(TRIGGERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        raise ValueError("not a dict")
    except (json.JSONDecodeError, ValueError, OSError):
        _backup_triggers()
        _write_triggers(DEFAULT_TRIGGERS)
        return dict(DEFAULT_TRIGGERS)


def save_triggers(data: dict) -> None:
    _write_triggers(data)


def _write_triggers(data: dict) -> None:
    with open(TRIGGERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _backup_triggers() -> None:
    backup = TRIGGERS_FILE + ".backup"
    try:
        os.replace(TRIGGERS_FILE, backup)
    except OSError:
        pass


# ──────────────────────────────────────────────────────────────────────────────
#  GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────

triggers: dict = load_triggers()
buffer:   str  = ""

# ──────────────────────────────────────────────────────────────────────────────
#  EXPAND
# ──────────────────────────────────────────────────────────────────────────────

def expand(word: str, replacement: str, boundary_char: str) -> None:
    time.sleep(0.05)
    erase_count = len(word) + 1
    for _ in range(erase_count):
        keyboard.send("backspace")
        time.sleep(0.01)
    keyboard.write(replacement, delay=0.01)
    if boundary_char == "\n":
        keyboard.send("enter")
    elif boundary_char == "\t":
        keyboard.send("tab")
    elif boundary_char == " ":
        keyboard.send("space")
    else:
        keyboard.write(boundary_char)


# ──────────────────────────────────────────────────────────────────────────────
#  KEYBOARD HOOK (Dynamically updates to reflect instant registration)
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
            replacement = triggers[word]
            t = threading.Thread(
                target=expand, args=(word, replacement, char), daemon=True,
            )
            t.start()
        return

    buffer += char

    MAX_BUFFER = (max((len(k) for k in triggers), default=40) + 5) if triggers else 45
    if len(buffer) > MAX_BUFFER:
        buffer = buffer[-MAX_BUFFER:]


# ──────────────────────────────────────────────────────────────────────────────
#  THEME COLORS & FONTS
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
    "danger_bg":      "#2a1520",
    "success":        "#00d4aa",
    "text_primary":   "#e8eaf6",
    "text_secondary": "#8b90a8",
    "text_muted":     "#555978",
    "row_even":       "#1a1d27",
    "row_odd":        "#1e2133",
    "row_hover":      "#252940",
    "row_selected":   "#2d2b55",
    "row_sel_fg":     "#c9c6ff",
}

FONT_TITLE   = ("Segoe UI", 17, "bold")
FONT_ENTRY   = ("Segoe UI", 11)
FONT_BTN     = ("Segoe UI", 10, "bold")
FONT_MICRO   = ("Segoe UI",  8, "bold")
FONT_SMALL   = ("Segoe UI",  9)
FONT_TABLE_H = ("Segoe UI",  9, "bold")
FONT_TRIGGER = ("Consolas",  11, "bold")
FONT_REPLACE = ("Segoe UI",  10)


# ──────────────────────────────────────────────────────────────────────────────
#  MODERN BUTTON
# ──────────────────────────────────────────────────────────────────────────────

class ModernButton(tk.Frame):
    def __init__(
        self, parent, text="", command=None,
        bg=C["accent"], hover=C["accent_hover"], press=C["accent_press"],
        fg=C["text_primary"], font=FONT_BTN,
        padx=18, pady=8, **kwargs,
    ):
        super().__init__(parent, bg=bg, cursor="hand2", **kwargs)
        self._bg    = bg
        self._hover = hover
        self._press = press
        self._cmd   = command

        self._label = tk.Label(
            self, text=text, font=font, bg=bg, fg=fg,
            padx=padx, pady=pady, cursor="hand2",
        )
        self._label.pack(fill="both", expand=True)

        for w in (self, self._label):
            w.bind("<Enter>",           self._on_enter)
            w.bind("<Leave>",           self._on_leave)
            w.bind("<ButtonPress-1>",   self._on_press)
            w.bind("<ButtonRelease-1>", self._on_release)

    def _set_color(self, c):
        self.config(bg=c); self._label.config(bg=c)

    def _on_enter(self, _):   self._set_color(self._hover)
    def _on_leave(self, _):   self._set_color(self._bg)
    def _on_press(self, _):   self._set_color(self._press)
    def _on_release(self, _):
        self._set_color(self._hover)
        if self._cmd: self._cmd()


# ──────────────────────────────────────────────────────────────────────────────
#  MODERN ENTRY
# ──────────────────────────────────────────────────────────────────────────────

class ModernEntry(tk.Frame):
    def __init__(self, parent, textvariable=None, width=20, **kwargs):
        super().__init__(
            parent, bg=C["surface2"],
            highlightbackground=C["border"], highlightcolor=C["accent"],
            highlightthickness=1, **kwargs,
        )
        self._var = textvariable or tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self._var, font=FONT_ENTRY,
            bg=C["surface2"], fg=C["text_primary"],
            insertbackground=C["accent"], relief="flat", bd=6, width=width,
        )
        self.entry.pack(fill="both", expand=True)
        self.entry.bind("<FocusIn>",  self._fi)
        self.entry.bind("<FocusOut>", self._fo)

    def _fi(self, _): self.config(highlightbackground=C["accent"], highlightthickness=2)
    def _fo(self, _): self.config(highlightbackground=C["border"], highlightthickness=1)

    def bind(self, seq=None, func=None, add=None):
        super().bind(seq, func, add)
        if hasattr(self, "entry"): self.entry.bind(seq, func, add)

    def get(self):      return self._var.get()
    def set(self, val): self._var.set(val)
    def focus(self):    self.entry.focus()


# ──────────────────────────────────────────────────────────────────────────────
#  DELETE ICON (Canvas-drawn Red Cross — No Font Dependencies)
# ──────────────────────────────────────────────────────────────────────────────

class DeleteIcon(tk.Canvas):
    SIZE = 28

    def __init__(self, parent, command=None, bg_color=None, **kwargs):
        self._base_bg    = bg_color or C["row_selected"]
        super().__init__(
            parent, width=self.SIZE, height=self.SIZE,
            bg=self._base_bg, highlightthickness=0, cursor="hand2",
        )
        self._cmd        = command
        self._hover_bg   = C["danger_bg"]
        self._line_color = C["danger"]
        self._line_hover = "#ff8fa3"

        self._draw(self._line_color)

        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, color):
        self.delete("icon")
        p, s = 8, self.SIZE
        self.create_line(p, p, s-p, s-p, fill=color, width=2, tags="icon")
        self.create_line(s-p, p, p, s-p, fill=color, width=2, tags="icon")

    def _on_enter(self, _):
        self.config(bg=self._hover_bg); self._draw(self._line_hover)
    def _on_leave(self, _):
        self.config(bg=self._base_bg);  self._draw(self._line_color)
    def _on_press(self, _):
        self.config(bg=C["danger_press"])
    def _on_release(self, _):
        self.config(bg=self._hover_bg); self._draw(self._line_hover)
        if self._cmd: self._cmd()

    def set_bg(self, color):
        self._base_bg = color; self.config(bg=color)


# ──────────────────────────────────────────────────────────────────────────────
#  TRIGGER ROW (Renders delete icon ONLY when selected)
# ──────────────────────────────────────────────────────────────────────────────

class TriggerRow(tk.Frame):
    def __init__(self, parent, trigger, replacement, row_bg,
                 on_select, on_delete, **kwargs):
        super().__init__(parent, bg=row_bg, **kwargs)

        self._trigger     = trigger
        self._replacement = replacement
        self._base_bg     = row_bg
        self._on_select   = on_select
        self._on_delete   = on_delete
        self._selected    = False

        # --- Trigger text ---
        self.lbl_trigger = tk.Label(
            self, text=trigger, font=FONT_TRIGGER,
            bg=row_bg, fg=C["accent"], anchor="w", padx=14, pady=8,
        )
        self.lbl_trigger.pack(side="left", fill="y")

        # --- Arrow spacer ---
        self.lbl_arrow = tk.Label(
            self, text="->", font=("Segoe UI", 12),
            bg=row_bg, fg=C["text_muted"], padx=6,
        )
        self.lbl_arrow.pack(side="left", fill="y")

        # --- Replacement Text ---
        self.lbl_replace = tk.Label(
            self, text=replacement, font=FONT_REPLACE,
            bg=row_bg, fg=C["text_primary"], anchor="w", padx=8, pady=8,
        )
        self.lbl_replace.pack(side="left", fill="both", expand=True)

        # --- Delete Icon (Created but NOT packed/visible initially) ---
        self.del_icon = DeleteIcon(
            self, command=lambda: self._on_delete(self._trigger),
            bg_color=C["row_selected"],
        )

        # Row interactive triggers
        for w in (self, self.lbl_trigger, self.lbl_arrow, self.lbl_replace):
            w.bind("<Enter>",         self._hover_in)
            w.bind("<Leave>",         self._hover_out)
            w.bind("<ButtonPress-1>", self._click)

    def _set_all_bg(self, c):
        self.config(bg=c)
        self.lbl_trigger.config(bg=c)
        self.lbl_arrow.config(bg=c)
        self.lbl_replace.config(bg=c)
        self.del_icon.set_bg(c)

    def _hover_in(self, _):
        if not self._selected:
            self._set_all_bg(C["row_hover"])

    def _hover_out(self, _):
        if not self._selected:
            self._set_all_bg(self._base_bg)

    def _click(self, _):
        self._on_select(self._trigger, self._replacement)

    def select(self):
        """Called when this row is selected — displays the red delete icon."""
        self._selected = True
        self._set_all_bg(C["row_selected"])
        self.lbl_trigger.config(fg=C["row_sel_fg"])
        self.lbl_replace.config(fg=C["row_sel_fg"])
        
        # Packing makes it dynamically slide-in on selection
        self.del_icon.pack(side="right", padx=(4, 14), pady=4)

    def deselect(self):
        """Called when row is deselected — hides the red delete icon."""
        self._selected = False
        self._set_all_bg(self._base_bg)
        self.lbl_trigger.config(fg=C["accent"])
        self.lbl_replace.config(fg=C["text_primary"])
        
        # Hides the delete icon completely
        self.del_icon.pack_forget()


# ──────────────────────────────────────────────────────────────────────────────
#  GUI
# ──────────────────────────────────────────────────────────────────────────────

class ManagerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.resizable(False, False)
        self.root.configure(bg=C["bg"])
        self.root.geometry("720x600")

        self._set_window_icon(self.root)

        self._selected_row = None
        self._row_widgets = []

        self._build_header()
        self._build_input_card()
        self._build_table_card()
        self._build_status_bar()

        self.refresh_table()

    def _set_window_icon(self, window) -> None:
        ico = resource_path("Textiva.ico")
        if os.path.exists(ico):
            try:
                window.iconbitmap(ico)
                return
            except Exception:
                pass
        png = resource_path("Textiva_icon.png")
        if os.path.exists(png):
            try:
                img = tk.PhotoImage(file=png)
                window.iconphoto(True, img)
                window._icon_ref = img
                return
            except Exception:
                pass

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["surface"])
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C["accent"], height=3).pack(fill="x")

        inner = tk.Frame(hdr, bg=C["surface"])
        inner.pack(fill="x", padx=24, pady=14)

        tk.Label(
            inner, text="Textiva", font=FONT_TITLE,
            bg=C["surface"], fg=C["text_primary"],
        ).pack(side="left")

        tk.Label(
            inner,
            text="  —  type a trigger then space / punctuation to expand",
            font=FONT_SMALL, bg=C["surface"], fg=C["text_secondary"],
        ).pack(side="left", pady=(5, 0))

    def _build_input_card(self):
        card = tk.Frame(
            self.root, bg=C["surface"],
            highlightbackground=C["border"], highlightthickness=1,
        )
        card.pack(fill="x", padx=20, pady=(16, 8))

        inner = tk.Frame(card, bg=C["surface"])
        inner.pack(fill="x", padx=20, pady=16)

        tk.Label(
            inner, text="TRIGGER WORD",
            font=FONT_MICRO, bg=C["surface"], fg=C["accent"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        tk.Label(
            inner, text="->",
            font=("Segoe UI", 16), bg=C["surface"], fg=C["text_muted"],
        ).grid(row=0, column=1, rowspan=2, padx=10)

        tk.Label(
            inner, text="EXPANDS TO",
            font=FONT_MICRO, bg=C["surface"], fg=C["accent"],
        ).grid(row=0, column=2, sticky="w", pady=(0, 4))

        self.trigger_var = tk.StringVar()
        self.trigger_entry = ModernEntry(
            inner, textvariable=self.trigger_var, width=14,
        )
        self.trigger_entry.grid(row=1, column=0, padx=(0, 12), sticky="ew")
        self.trigger_entry.entry.bind(
            "<Return>", lambda e: self.replacement_entry.focus()
        )

        self.replacement_var = tk.StringVar()
        self.replacement_entry = ModernEntry(
            inner, textvariable=self.replacement_var, width=30,
        )
        self.replacement_entry.grid(row=1, column=2, padx=(0, 12), sticky="ew")
        self.replacement_entry.entry.bind("<Return>", lambda e: self.add_trigger())

        add_btn = ModernButton(
            inner, text="+  Add / Update",
            command=self.add_trigger,
            bg=C["accent"], hover=C["accent_hover"], press=C["accent_press"],
        )
        add_btn.grid(row=0, column=3, rowspan=2, padx=(4, 0), sticky="ns")

        inner.columnconfigure(2, weight=1)

    def _build_table_card(self):
        card = tk.Frame(
            self.root, bg=C["surface"],
            highlightbackground=C["border"], highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        col_hdr = tk.Frame(card, bg=C["surface2"])
        col_hdr.pack(fill="x")

        tk.Label(
            col_hdr, text="  TRIGGER", font=FONT_TABLE_H,
            bg=C["surface2"], fg=C["text_muted"], anchor="w", padx=14, pady=6,
        ).pack(side="left")

        tk.Label(
            col_hdr, text="EXPANDS TO", font=FONT_TABLE_H,
            bg=C["surface2"], fg=C["text_muted"], anchor="w", padx=50, pady=6,
        ).pack(side="left", fill="x", expand=True)

        scroll_frame = tk.Frame(card, bg=C["surface"])
        scroll_frame.pack(fill="both", expand=True, padx=2, pady=(2, 2))

        self._canvas = tk.Canvas(
            scroll_frame, bg=C["surface"], highlightthickness=0, bd=0,
        )
        self._scrollbar = tk.Scrollbar(
            scroll_frame, orient="vertical", command=self._canvas.yview,
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=C["surface"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw",
        )

        self._list_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._empty_label = tk.Label(
            self._list_frame,
            text="\n\n  No triggers yet.\n  Add one above to get started!",
            font=FONT_SMALL, bg=C["surface"], fg=C["text_muted"],
            anchor="center", justify="center",
        )

    def _on_frame_configure(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=C["surface2"], height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        dot = tk.Canvas(
            bar, width=10, height=10, bg=C["surface2"], highlightthickness=0,
        )
        dot.pack(side="left", padx=(12, 5), pady=9)
        dot.create_oval(1, 1, 9, 9, fill=C["success"], outline="")

        tk.Label(
            bar, text="Hook active  ·", font=FONT_SMALL,
            bg=C["surface2"], fg=C["text_muted"],
        ).pack(side="left")

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(
            bar, textvariable=self.status_var, font=FONT_SMALL,
            bg=C["surface2"], fg=C["text_secondary"],
        ).pack(side="left", padx=(6, 0))

        tk.Label(
            bar, text=f"  Data: {APP_DATA_DIR}", font=FONT_SMALL,
            bg=C["surface2"], fg=C["text_muted"],
        ).pack(side="right", padx=(0, 12))

    # ── Logic ──────────────────────────────────────────────────────────
    def refresh_table(self) -> None:
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()
        self._selected_row = None

        if not triggers:
            self._empty_label.pack(fill="both", expand=True, pady=30)
            return
        else:
            self._empty_label.pack_forget()

        for i, (tw, rt) in enumerate(sorted(triggers.items())):
            row_bg = C["row_odd"] if i % 2 else C["row_even"]
            row = TriggerRow(
                self._list_frame,
                trigger=tw, replacement=rt, row_bg=row_bg,
                on_select=self._on_row_select,
                on_delete=self._on_row_delete,
            )
            row.pack(fill="x")
            self._row_widgets.append(row)

    def _on_row_select(self, trigger: str, replacement: str) -> None:
        if self._selected_row:
            self._selected_row.deselect()

        for row in self._row_widgets:
            if row._trigger == trigger:
                row.select()
                self._selected_row = row
                break

        self.trigger_var.set(trigger)
        self.replacement_var.set(replacement)

    def _on_row_delete(self, trigger: str) -> None:
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete trigger  '{trigger}'?\n\nThis cannot be undone.",
        ):
            return

        if trigger in triggers:
            del triggers[trigger]
            save_triggers(triggers)

        self.refresh_table()
        self.trigger_var.set("")
        self.replacement_var.set("")
        self.status_var.set(f"Deleted: '{trigger}'")

    def add_trigger(self) -> None:
        global triggers
        tw = self.trigger_var.get().strip()
        rt = self.replacement_var.get().strip()

        if not tw:
            messagebox.showwarning("Missing Input", "Please enter a trigger word.")
            return
        if not rt:
            messagebox.showwarning(
                "Missing Input", "Please enter the replacement text.",
            )
            return

        action = "Updated" if tw in triggers else "Added"
        triggers[tw] = rt
        save_triggers(triggers)
        self.refresh_table()
        self.trigger_var.set("")
        self.replacement_var.set("")
        self.status_var.set(f"{action}: '{tw}'  ->  '{rt}'")


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
    ensure_startup()
    threading.Thread(target=run_hook_only, daemon=True).start()
    root = tk.Tk()
    ManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()