
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import calendar
import datetime
import os
import csv
import pathlib

from PIL import Image, ImageTk

import image_processor as ip


# ─────────────────────────────────────────────────────────────
# PALETTE  — matches main.py exactly
# ─────────────────────────────────────────────────────────────

BG      = "#1C2B3A"
PANEL   = "#243447"
PANEL2  = "#1A2535"
BORDER  = "#2E4158"
TEXT    = "#E8EDF2"
MUTED   = "#7D93A8"
ACCENT  = "#4A9EDB"
DIM_ACC = "#3A7EBB"
SUCCESS = "#4CAF82"
WARN    = "#E8A83A"
FAIL    = "#E05C5C"
ALT     = "#1E2F3F"
SEP     = "#2E4158"    # separator line colour
SEL_ROW = "#2A3F52"

FF = "Segoe UI"

# Mirror the C dict so all existing C["key"] references keep working
C = {
    "bg":        BG,
    "panel":     PANEL,
    "border":    BORDER,
    "accent":    ACCENT,
    "accent2":   DIM_ACC,
    "gold":      WARN,
    "green":     SUCCESS,
    "text":      TEXT,
    "muted":     MUTED,
    "entry_bg":  PANEL2,
    "entry_fg":  TEXT,
    "separator": SEP,
    "table_alt": ALT,
    "table_sel": SEL_ROW,
    "header_bg": PANEL2,
}

# Mirror FONTS dict — same keys, same structure, navy-appropriate sizes
FONTS = {
    "title":   (FF, 16, "bold"),
    "heading": (FF, 11, "bold"),
    "label":   (FF,  9),
    "input":   (FF, 10),
    "mono":    (FF,  9),
    "small":   (FF,  8),
    "tab":     (FF,  9, "bold"),
    "big":     (FF, 22, "bold"),
}


# ─────────────────────────────────────────────────────────────
# NEARBY CAMPS DATA
# ─────────────────────────────────────────────────────────────

NEARBY_CAMPS = [
    {
        "name":     "City Blood Bank — B1",
        "distance": "0.8 km",
        "hours":    "Open today  9 am – 5 pm",
        "status":   "Accepting walk-ins",
        "color":    SUCCESS,
    },
    {
        "name":     "Red Cross Camp — B2",
        "distance": "2.1 km",
        "hours":    "Camp on May 3rd",
        "status":   "Pre-registration required",
        "color":    WARN,
    },
    {
        "name":     "General Hospital — B4",
        "distance": "3.5 km",
        "hours":    "Mon – Sat  10 am – 4 pm",
        "status":   "Slots available",
        "color":    SUCCESS,
    },
    {
        "name":     "Community Centre Drive — B3",
        "distance": "4.2 km",
        "hours":    "This weekend only",
        "status":   "Limited slots",
        "color":    WARN,
    },
]


# ─────────────────────────────────────────────────────────────
# PERSISTENCE
# ─────────────────────────────────────────────────────────────

_HERE     = os.path.dirname(os.path.abspath(__file__))
_LOG_PATH = os.path.join(_HERE, "..", "output", "donation_log.csv")
_LOG_COLS = ["donor_name", "blood_type", "bank_id",
             "donation_date", "units", "status", "booked_on"]


def _ensure_log():
    os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
    if not os.path.exists(_LOG_PATH):
        with open(_LOG_PATH, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=_LOG_COLS).writeheader()


def load_donations():
    _ensure_log()
    with open(_LOG_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for col in _LOG_COLS:
            r.setdefault(col, "")
    return rows


def save_donation(record: dict):
    _ensure_log()
    for col in _LOG_COLS:
        record.setdefault(col, "")
    with open(_LOG_PATH, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=_LOG_COLS).writerow(record)


# ─────────────────────────────────────────────────────────────
# WIDGET HELPERS
# ─────────────────────────────────────────────────────────────

def _lbl(parent, text, font=None, fg=None, bg=None, **kw):
    return tk.Label(
        parent, text=text,
        font=font or FONTS["label"],
        fg=fg   or C["text"],
        bg=bg   or parent["bg"],
        **kw,
    )


def _sep(parent):
    return tk.Frame(parent, bg=C["separator"], height=1)


def _btn(parent, text, cmd, bg=None, width=None, pady=6):
    bg = bg or C["accent"]
    b  = tk.Button(
        parent, text=text, command=cmd,
        font=FONTS["heading"],
        bg=bg, fg=C["text"],
        activebackground=DIM_ACC,
        activeforeground=C["text"],
        relief="flat", bd=0,
        cursor="hand2",
        pady=pady,
        **({"width": width} if width else {}),
    )
    b.bind("<Enter>", lambda e: b.config(bg=DIM_ACC))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _entry(parent, width=22):
    return tk.Entry(
        parent, width=width,
        font=FONTS["input"],
        bg=C["entry_bg"], fg=C["entry_fg"],
        insertbackground=C["accent"],
        relief="flat", bd=0,
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"],
    )


def _combo(parent, values, width=20):
    cb = ttk.Combobox(parent, values=values, state="readonly",
                      width=width, font=FONTS["input"])
    cb.configure(foreground=C["entry_fg"])
    return cb


def _apply_ttk_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("Treeview",
                background=PANEL, foreground=TEXT,
                fieldbackground=PANEL, rowheight=25,
                font=FONTS["label"], borderwidth=0)
    s.configure("Treeview.Heading",
                background=PANEL2, foreground=ACCENT,
                font=FONTS["small"]+"bold" if False else FONTS["small"],
                relief="flat", borderwidth=0)
    s.map("Treeview",
          background=[("selected", SEL_ROW)],
          foreground=[("selected", TEXT)])
    s.configure("TCombobox",
                fieldbackground=PANEL2, background=PANEL2,
                foreground=TEXT, arrowcolor=ACCENT,
                bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    s.map("TCombobox",
          fieldbackground=[("readonly", PANEL2)],
          foreground=[("readonly", TEXT)],
          selectbackground=[("readonly", ACCENT)],
          selectforeground=[("readonly", "#FFFFFF")])
    s.configure("Vertical.TScrollbar",
                background=PANEL, troughcolor=BG,
                arrowcolor=MUTED, bordercolor=BORDER)


# ═════════════════════════════════════════════════════════════
# CALENDAR WIDGET
# ═════════════════════════════════════════════════════════════

class _MiniCalendar(tk.Frame):
    DAY_LABELS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

    def __init__(self, parent, on_select=None, **kw):
        super().__init__(parent, bg=PANEL2, **kw)
        self.on_select     = on_select
        self.selected_date = None
        self._today        = datetime.date.today()
        self._year         = self._today.year
        self._month        = self._today.month
        self._day_btns     = []

        self._build_nav()
        self._build_header()
        self._build_grid()
        self._render_month()

    def _build_nav(self):
        nav = tk.Frame(self, bg=PANEL2)
        nav.pack(fill="x", pady=(6, 2))

        self._prev_btn = tk.Button(
            nav, text="◀", font=FONTS["small"],
            bg=PANEL2, fg=MUTED,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", bd=0, cursor="hand2", padx=6,
            command=self._prev_month,
        )
        self._prev_btn.pack(side="left", padx=4)

        self._month_lbl = tk.Label(
            nav, text="", font=FONTS["heading"],
            fg=ACCENT, bg=PANEL2,
        )
        self._month_lbl.pack(side="left", expand=True)

        self._next_btn = tk.Button(
            nav, text="▶", font=FONTS["small"],
            bg=PANEL2, fg=MUTED,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", bd=0, cursor="hand2", padx=6,
            command=self._next_month,
        )
        self._next_btn.pack(side="right", padx=4)

    def _build_header(self):
        hdr = tk.Frame(self, bg=PANEL2)
        hdr.pack(fill="x", padx=6)
        for d in self.DAY_LABELS:
            tk.Label(
                hdr, text=d, font=FONTS["small"],
                fg=MUTED, bg=PANEL2,
                width=3, anchor="center",
            ).pack(side="left", expand=True)

    def _build_grid(self):
        self._grid_frame = tk.Frame(self, bg=PANEL2)
        self._grid_frame.pack(fill="both", padx=6, pady=(2, 6))

    def _render_month(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._day_btns.clear()

        self._month_lbl.config(
            text=datetime.date(self._year, self._month, 1).strftime("%B %Y"))

        cal   = calendar.monthcalendar(self._year, self._month)
        today = self._today

        for week in cal:
            row = tk.Frame(self._grid_frame, bg=PANEL2)
            row.pack(fill="x")
            for day in week:
                if day == 0:
                    tk.Label(row, text="", width=3, bg=PANEL2).pack(
                        side="left", expand=True)
                    continue

                d    = datetime.date(self._year, self._month, day)
                past = d < today

                if d == today:
                    bg, fg = ACCENT, "#FFFFFF"
                elif self.selected_date and d == self.selected_date:
                    bg, fg = BORDER, ACCENT
                elif past:
                    bg, fg = PANEL2, SEP
                else:
                    bg, fg = PANEL2, TEXT

                b = tk.Button(
                    row, text=str(day),
                    font=FONTS["small"],
                    bg=bg, fg=fg,
                    relief="flat", bd=0, width=3,
                    cursor="hand2" if not past else "arrow",
                    activebackground=BORDER,
                    activeforeground=ACCENT,
                    command=(lambda _d=d: self._select(_d)) if not past else lambda: None,
                )
                b.pack(side="left", expand=True, pady=1)
                self._day_btns.append((b, d))

    def _select(self, date: datetime.date):
        self.selected_date = date
        self._render_month()
        if self.on_select:
            self.on_select(date)

    def _prev_month(self):
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self._render_month()

    def _next_month(self):
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self._render_month()


# ═════════════════════════════════════════════════════════════
# TAB 1 — SCHEDULE
# ═════════════════════════════════════════════════════════════

class _ScheduleTab(tk.Frame):
    BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    BANK_IDS    = ["B1", "B2", "B3", "B4"]

    def __init__(self, parent, on_booked=None, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self.on_booked = on_booked
        self._build()

    def _build(self):
        _lbl(self, "SELECT DONATION DATE",
             font=FONTS["small"], fg=ACCENT).pack(anchor="w", padx=14, pady=(12, 4))

        self._cal = _MiniCalendar(self, on_select=self._on_date_select)
        self._cal.pack(fill="x", padx=14)

        self._date_lbl = _lbl(self, "No date selected",
                               font=FONTS["small"], fg=MUTED)
        self._date_lbl.pack(anchor="w", padx=14, pady=(2, 8))

        _sep(self).pack(fill="x", padx=14, pady=4)

        form = tk.Frame(self, bg=PANEL)
        form.pack(fill="x", padx=14, pady=4)

        def row(label, widget):
            _lbl(form, label, font=FONTS["small"],
                 fg=MUTED).pack(anchor="w", pady=(6, 2))
            widget.pack(fill="x", ipady=3)

        self._donor_entry = _entry(form)
        row("DONOR NAME", self._donor_entry)

        self._blood_cb = _combo(form, self.BLOOD_TYPES)
        row("BLOOD TYPE", self._blood_cb)

        self._bank_cb = _combo(form, self.BANK_IDS)
        row("PREFERRED BANK", self._bank_cb)

        _sep(self).pack(fill="x", padx=14, pady=10)

        _btn(self, "✔  CONFIRM BOOKING", self._confirm,
             bg=ACCENT).pack(fill="x", padx=14, pady=(0, 8))

        _lbl(self, "Note: minimum 56 days between donations",
             font=FONTS["small"], fg=SEP).pack(pady=(0, 10))

    def _on_date_select(self, date: datetime.date):
        self._date_lbl.config(
            text=f"Selected: {date.strftime('%d %b %Y')}",
            fg=SUCCESS,
        )

    def _confirm(self):
        name  = self._donor_entry.get().strip()
        blood = self._blood_cb.get()
        bank  = self._bank_cb.get()
        date  = self._cal.selected_date

        if not name:
            messagebox.showerror("Missing Info", "Please enter donor name.", parent=self)
            return
        if not blood:
            messagebox.showerror("Missing Info", "Please select blood type.", parent=self)
            return
        if not bank:
            messagebox.showerror("Missing Info", "Please select a bank.", parent=self)
            return
        if not date:
            messagebox.showerror("Missing Info", "Please select a donation date.", parent=self)
            return
        if date < datetime.date.today():
            messagebox.showerror("Invalid Date", "Please select a future date.", parent=self)
            return

        record = {
            "donor_name":    name,
            "blood_type":    blood,
            "bank_id":       bank,
            "donation_date": str(date),
            "units":         "450",
            "status":        "SCHEDULED",
            "booked_on":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_donation(record)

        messagebox.showinfo(
            "Booking Confirmed",
            f"Donation scheduled!\n\n"
            f"Donor : {name}\n"
            f"Type  : {blood}\n"
            f"Bank  : {bank}\n"
            f"Date  : {date.strftime('%d %b %Y')}",
            parent=self,
        )

        self._donor_entry.delete(0, "end")
        self._blood_cb.set("")
        self._bank_cb.set("")
        self._cal.selected_date = None
        self._cal._render_month()
        self._date_lbl.config(text="No date selected", fg=MUTED)

        if self.on_booked:
            self.on_booked(record)


# ═════════════════════════════════════════════════════════════
# TAB 2 — NEARBY CAMPS
# ═════════════════════════════════════════════════════════════

class _NearbyCampsTab(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self._build()

    def _build(self):
        _lbl(self, "CAMPS NEAR YOU",
             font=FONTS["small"], fg=ACCENT).pack(anchor="w", padx=14, pady=(12, 6))

        scroll_frame = tk.Frame(self, bg=PANEL)
        scroll_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        canvas  = tk.Canvas(scroll_frame, bg=PANEL, highlightthickness=0)
        scrollb = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        inner   = tk.Frame(canvas, bg=PANEL)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollb.set)

        canvas.pack(side="left",  fill="both", expand=True)
        scrollb.pack(side="right", fill="y")

        for camp in NEARBY_CAMPS:
            self._camp_card(inner, camp)

    def _camp_card(self, parent, camp):
        card = tk.Frame(
            parent, bg=PANEL2,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        card.pack(fill="x", pady=5)

        top = tk.Frame(card, bg=PANEL2)
        top.pack(fill="x", padx=10, pady=(8, 2))

        _lbl(top, camp["name"],
             font=FONTS["heading"], fg=ACCENT, bg=PANEL2).pack(side="left")
        _lbl(top, camp["distance"],
             font=FONTS["small"], fg=MUTED, bg=PANEL2).pack(side="right")

        _lbl(card, camp["hours"],
             font=FONTS["small"], fg=MUTED, bg=PANEL2,
             anchor="w").pack(fill="x", padx=10, pady=1)

        status_row = tk.Frame(card, bg=PANEL2)
        status_row.pack(fill="x", padx=10, pady=(2, 8))
        _lbl(status_row, f"● {camp['status']}",
             font=FONTS["small"], fg=camp["color"], bg=PANEL2).pack(side="left")


# ═════════════════════════════════════════════════════════════
# TAB 3 — HISTORY
# ═════════════════════════════════════════════════════════════

class _HistoryTab(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=PANEL)
        header.pack(fill="x", padx=14, pady=(12, 6))
        _lbl(header, "DONATION HISTORY",
             font=FONTS["small"], fg=ACCENT).pack(side="left")
        _btn(header, "⟳ Refresh", self._refresh,
             bg=BORDER, pady=2).pack(side="right")

        self._summary_frame = tk.Frame(self, bg=PANEL)
        self._summary_frame.pack(fill="x", padx=14, pady=(0, 8))

        wrap = tk.Frame(self, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self._canvas = tk.Canvas(wrap, bg=PANEL, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self._canvas.yview)
        self._inner = tk.Frame(self._canvas, bg=PANEL)
        self._inner.bind("<Configure>",
                         lambda e: self._canvas.configure(
                             scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._refresh()

    def _refresh(self):
        for w in self._inner.winfo_children():
            w.destroy()
        for w in self._summary_frame.winfo_children():
            w.destroy()

        records   = load_donations()
        completed = [r for r in records if r["status"] == "COMPLETED"]
        scheduled = [r for r in records if r["status"] == "SCHEDULED"]
        cancelled = [r for r in records if r["status"] == "CANCELLED"]

        # Status pills using navy palette
        for label, count, text_c, pill_bg in [
            ("SCHEDULED", len(scheduled), "#FFFFFF", WARN),
            ("COMPLETED", len(completed), "#FFFFFF", SUCCESS),
            ("CANCELLED", len(cancelled), "#FFFFFF", MUTED),
        ]:
            pill = tk.Frame(self._summary_frame, bg=pill_bg,
                            highlightthickness=0)
            pill.pack(side="left", padx=(0, 6))
            tk.Label(pill, text=f" {count}  {label} ",
                     font=FONTS["small"], fg=text_c,
                     bg=pill_bg).pack(padx=4, pady=3)

        if not records:
            _lbl(self._inner, "No donation records yet.",
                 font=FONTS["mono"], fg=MUTED).pack(pady=20)
            return

        def sort_key(r):
            try:
                d = datetime.date.fromisoformat(r["donation_date"])
            except Exception:
                d = datetime.date.min
            order = {"SCHEDULED": 0, "COMPLETED": 1, "CANCELLED": 2}.get(r["status"], 3)
            return (order, d)

        for rec in sorted(records, key=sort_key):
            self._record_card(rec)

    def _record_card(self, rec):
        status   = rec.get("status", "SCHEDULED")
        is_sched = status == "SCHEDULED"
        is_done  = status == "COMPLETED"

        badge_bg = WARN    if is_sched else (SUCCESS if is_done else MUTED)
        badge_fg = "#FFFFFF"

        card = tk.Frame(
            self._inner, bg=PANEL2,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        card.pack(fill="x", pady=4)

        top = tk.Frame(card, bg=PANEL2)
        top.pack(fill="x", padx=10, pady=(8, 2))

        info = tk.Frame(top, bg=PANEL2)
        info.pack(side="left", fill="x", expand=True)

        try:
            d     = datetime.date.fromisoformat(rec["donation_date"])
            d_str = d.strftime("%d %b %Y")
        except Exception:
            d_str = rec.get("donation_date", "—")

        _lbl(info, f"{d_str}  ·  {rec.get('bank_id', '?')}",
             font=FONTS["input"], fg=TEXT, bg=PANEL2).pack(anchor="w")
        _lbl(info, f"Donor: {rec.get('donor_name', '?')}  ·  "
                   f"{rec.get('blood_type', '?')}  ·  450 ml",
             font=FONTS["small"], fg=MUTED, bg=PANEL2).pack(anchor="w")

        tk.Label(
            top, text=f"  {status}  ",
            font=FONTS["small"],
            bg=badge_bg, fg=badge_fg,
            padx=4, pady=3, relief="flat",
        ).pack(side="right", anchor="n", padx=(8, 0))

        bottom = tk.Frame(card, bg=PANEL2)
        bottom.pack(fill="x", padx=10, pady=(2, 8))

        booked_on = rec.get("booked_on", "")
        if booked_on:
            _lbl(bottom, f"Booked on: {booked_on}",
                 font=FONTS["small"], fg=SEP, bg=PANEL2).pack(side="left")

        if is_sched:
            def _cancel(r=rec):
                if messagebox.askyesno(
                    "Cancel Booking",
                    f"Cancel donation booked for {r.get('donation_date')}?",
                    parent=self,
                ):
                    self._cancel_record(r)

            tk.Button(
                bottom, text="✕ Cancel",
                font=FONTS["small"],
                bg=PANEL2, fg=FAIL,
                activebackground=FAIL, activeforeground="#FFFFFF",
                relief="flat", bd=0, cursor="hand2",
                command=_cancel,
            ).pack(side="right")

    def _cancel_record(self, target: dict):
        records = load_donations()
        updated = []
        for r in records:
            if (r["donor_name"]    == target["donor_name"] and
                r["donation_date"] == target["donation_date"] and
                r["bank_id"]       == target["bank_id"] and
                r["status"]        == "SCHEDULED"):
                r["status"] = "CANCELLED"
            updated.append(r)

        _ensure_log()
        with open(_LOG_PATH, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_LOG_COLS)
            w.writeheader()
            for r in updated:
                for col in _LOG_COLS:
                    r.setdefault(col, "")
                w.writerow(r)

        self._refresh()


# ═════════════════════════════════════════════════════════════
# TAB 4 — DONOR PHOTO  (PIL + OpenCV)
# ═════════════════════════════════════════════════════════════

class _PhotoTab(tk.Frame):
    """
    Op 1  Read        – filedialog → PIL.Image.open()
    Op 2  Display     – show original in canvas via ImageTk
    Op 3  Save        – PIL .save() with timestamped filename
    Op 4  Resize      – PIL .resize()  (half-size)
    Op 5  Flip        – cv2.flip() horizontal
    Op 6  Crop        – PIL .crop()  (centre square)
    Op 7  Grayscale   – cv2.cvtColor(…, COLOR_BGR2GRAY)
    Op 8  Contrast    – PIL ImageEnhance.Contrast(factor=2.0)
    """

    PREV_W, PREV_H = 220, 165

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self._orig_pil  = None
        self._curr_pil  = None
        self._photo_ref = None
        self._orig_path = ""
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=PANEL)
        hdr.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(hdr, text="DONOR PHOTO  /  IMAGE PROCESSING",
                 font=FONTS["small"], fg=ACCENT, bg=PANEL).pack(side="left")

        upload_row = tk.Frame(self, bg=PANEL)
        upload_row.pack(fill="x", padx=14, pady=(8, 4))

        self._upload_btn = tk.Button(
            upload_row, text="📂  UPLOAD PHOTO",
            font=FONTS["heading"],
            bg=ACCENT, fg="#FFFFFF",
            activebackground=DIM_ACC, activeforeground="#FFFFFF",
            relief="flat", bd=0, cursor="hand2", pady=5,
            command=self._load_image,
        )
        self._upload_btn.pack(side="left")
        self._upload_btn.bind("<Enter>",
            lambda e: self._upload_btn.config(bg=DIM_ACC))
        self._upload_btn.bind("<Leave>",
            lambda e: self._upload_btn.config(bg=ACCENT))

        self._file_lbl = tk.Label(
            upload_row, text="  No file loaded",
            font=FONTS["small"], fg=MUTED, bg=PANEL, anchor="w",
        )
        self._file_lbl.pack(side="left", padx=8)

        # Preview canvas
        preview_outer = tk.Frame(
            self, bg=PANEL2,
            highlightthickness=1, highlightbackground=BORDER,
        )
        preview_outer.pack(padx=14, pady=(4, 4))

        self._canvas = tk.Canvas(
            preview_outer,
            width=self.PREV_W, height=self.PREV_H,
            bg=PANEL2, highlightthickness=0,
        )
        self._canvas.pack()
        self._draw_placeholder()

        self._op_lbl = tk.Label(
            self, text="No operation applied",
            font=FONTS["small"], fg=MUTED, bg=PANEL,
        )
        self._op_lbl.pack(pady=(2, 4))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(4, 6))

        # Operation buttons — 2-col grid
        grid = tk.Frame(self, bg=PANEL)
        grid.pack(fill="x", padx=14)

        ops = [
            ("① SHOW ORIGINAL",     self._op_display,   BORDER),
            ("② SAVE IMAGE",         self._op_save,      SUCCESS),
            ("③ RESIZE  (½×)",       self._op_resize,    BORDER),
            ("④ FLIP  (horizontal)", self._op_flip,      BORDER),
            ("⑤ CROP  (centre sq.)", self._op_crop,      BORDER),
            ("⑥ GRAYSCALE",          self._op_grayscale, BORDER),
            ("⑦ ENHANCE CONTRAST",   self._op_contrast,  ACCENT),
            ("⑧ RESET",              self._op_reset,     PANEL2),
        ]

        for idx, (label, cmd, bg_col) in enumerate(ops):
            col = idx % 2
            row = idx // 2
            b = tk.Button(
                grid, text=label,
                font=FONTS["small"],
                bg=bg_col, fg=TEXT,
                activebackground=DIM_ACC, activeforeground="#FFFFFF",
                relief="flat", bd=0, cursor="hand2",
                pady=7, padx=4,
                command=cmd,
            )
            b.grid(row=row, column=col, sticky="ew", padx=3, pady=3)
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=DIM_ACC, fg="#FFFFFF"))
            b.bind("<Leave>", lambda e, btn=b, obg=bg_col: btn.config(bg=obg, fg=TEXT))

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(6, 0))
        self._status = tk.Label(
            self, text="Upload a photo to enable operations.",
            font=FONTS["small"], fg=MUTED, bg=PANEL,
            anchor="w", wraplength=460,
        )
        self._status.pack(fill="x", padx=14, pady=(4, 10))

    def _draw_placeholder(self):
        self._canvas.delete("all")
        cx, cy = self.PREV_W // 2, self.PREV_H // 2
        self._canvas.create_text(cx, cy - 14, text="👤",
                                  font=("Segoe UI Emoji", 28), fill=BORDER)
        self._canvas.create_text(cx, cy + 22, text="No photo loaded",
                                  font=FONTS["small"], fill=MUTED)

    def _show(self, pil_img, op_name: str = ""):
        self._curr_pil = pil_img
        thumb = pil_img.copy()
        thumb.thumbnail((self.PREV_W, self.PREV_H), Image.LANCZOS)
        self._photo_ref = ImageTk.PhotoImage(thumb)
        self._canvas.delete("all")
        self._canvas.create_image(
            self.PREV_W // 2, self.PREV_H // 2,
            anchor="center", image=self._photo_ref,
        )
        if op_name:
            self._op_lbl.config(text=f"Showing: {op_name}", fg=WARN)

    def _need_image(self) -> bool:
        if self._orig_pil is None:
            messagebox.showwarning("No Image", "Please upload a photo first.",
                                   parent=self)
            return False
        return True

    # Ops 1-8 — identical logic, only colours changed above

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select donor photo",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
                ("All files",   "*.*"),
            ],
            parent=self,
        )
        if not path:
            return
        self._orig_path = path
        self._orig_pil  = ip.read_image(path)
        self._curr_pil  = self._orig_pil.copy()
        fname = pathlib.Path(path).name
        self._file_lbl.config(
            text=f"  {fname}  ({self._orig_pil.width}×{self._orig_pil.height})",
            fg=SUCCESS,
        )
        self._show(self._orig_pil, "Original  (Op 1+2: Read & Display)")
        self._status.config(
            text=f"Loaded: {fname}  —  use the buttons below to process.",
            fg=MUTED,
        )

    def _op_display(self):
        if not self._need_image(): return
        self._show(self._orig_pil, "Original  (Op 2: Display)")
        self._status.config(text="Op 2 – Displaying original image.", fg=MUTED)

    def _op_save(self):
        if not self._need_image(): return
        dest = ip.save_image(self._curr_pil, self._orig_path)
        self._status.config(
            text=f"Op 3 – Saved as  {dest.name}  ->  output/donor_photos/",
            fg=SUCCESS,
        )
        messagebox.showinfo("Image Saved", f"Saved to:\n{dest}", parent=self)

    def _op_resize(self):
        if not self._need_image(): return
        w, h    = self._orig_pil.size
        resized = ip.resize_image(self._orig_pil, scale=0.5)
        self._show(resized, f"Resized  half  ->  {w//2}x{h//2}  (Op 4)")
        self._curr_pil = resized
        self._status.config(
            text=f"Op 4 – Resized: {w}x{h}  ->  {w//2}x{h//2}.",
            fg=MUTED,
        )

    def _op_flip(self):
        if not self._need_image(): return
        result = ip.flip_image(self._orig_pil, direction="horizontal")
        self._show(result, "Flipped horizontally  (Op 5)")
        self._curr_pil = result
        self._status.config(text="Op 5 – Horizontal flip.", fg=MUTED)

    def _op_crop(self):
        if not self._need_image(): return
        w, h    = self._orig_pil.size
        side    = min(w, h)
        cropped = ip.crop_image(self._orig_pil)
        self._show(cropped, f"Centre crop  {side}x{side}  (Op 6)")
        self._curr_pil = cropped
        self._status.config(
            text=f"Op 6 – Centre square crop {side}x{side}.", fg=MUTED)

    def _op_grayscale(self):
        if not self._need_image(): return
        result = ip.grayscale_image(self._orig_pil)
        self._show(result, "Grayscale  (Op 7)")
        self._curr_pil = result
        self._status.config(text="Op 7 – Grayscale.", fg=MUTED)

    def _op_contrast(self):
        if not self._need_image(): return
        factor   = 2.0
        enhanced = ip.enhance_contrast(self._orig_pil, factor=factor)
        self._show(enhanced, f"Contrast x{factor}  (Op 8)")
        self._curr_pil = enhanced
        self._status.config(text=f"Op 8 – Contrast x{factor}.", fg=MUTED)

    def _op_reset(self):
        if not self._need_image(): return
        self._show(self._orig_pil, "Original (reset)")
        self._curr_pil = self._orig_pil.copy()
        self._status.config(text="Reset to original image.", fg=MUTED)


# ═════════════════════════════════════════════════════════════
# DONATION PORTAL WINDOW
# ═════════════════════════════════════════════════════════════

class DonationPortal(tk.Toplevel):
    TABS = ["SCHEDULE", "NEARBY CAMPS", "MY HISTORY", "DONOR PHOTO"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("HEMATIX — Blood Donation Portal")
        self.geometry("520x700")
        self.minsize(480, 620)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        _apply_ttk_styles(self)

        self._active_tab = 0
        self._tab_btns   = []
        self._tab_frames = []
        self._build()

    def _build(self):
        self._build_header()
        self._build_tab_bar()
        self._build_content()
        self._switch_tab(0)

    def _build_header(self):
        bar = tk.Frame(self, bg=PANEL, height=50)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Left accent stripe matching main.py topbar
        tk.Frame(bar, bg=ACCENT, width=4).pack(side="left", fill="y")

        inner = tk.Frame(bar, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=16)

        _lbl(inner, "♥  BLOOD DONATION PORTAL",
             font=FONTS["title"], fg=ACCENT, bg=PANEL).pack(side="left", pady=10)

        tk.Button(
            inner, text="✕",
            font=FONTS["heading"],
            bg=PANEL, fg=MUTED,
            activebackground=FAIL, activeforeground="#FFFFFF",
            relief="flat", bd=0, cursor="hand2",
            command=self.destroy,
        ).pack(side="right", pady=10)

    def _build_tab_bar(self):
        bar = tk.Frame(self, bg=PANEL2)
        bar.pack(fill="x")

        tk.Frame(bar, bg=BORDER, height=1).pack(fill="x")

        btn_row = tk.Frame(bar, bg=PANEL2)
        btn_row.pack(fill="x", padx=10, pady=6)

        for i, label in enumerate(self.TABS):
            b = tk.Button(
                btn_row, text=label,
                font=FONTS["tab"],
                bg=PANEL2, fg=MUTED,
                activebackground=BORDER, activeforeground=ACCENT,
                relief="flat", bd=0,
                padx=10, pady=6,
                cursor="hand2",
                command=lambda idx=i: self._switch_tab(idx),
            )
            b.pack(side="left", padx=2)
            self._tab_btns.append(b)

        tk.Frame(bar, bg=BORDER, height=1).pack(fill="x")

    def _build_content(self):
        self._content_area = tk.Frame(self, bg=PANEL)
        self._content_area.pack(fill="both", expand=True)

        self._tab_frames = [
            _ScheduleTab(self._content_area, on_booked=self._on_new_booking),
            _NearbyCampsTab(self._content_area),
            _HistoryTab(self._content_area),
            _PhotoTab(self._content_area),
        ]

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        for frame in self._tab_frames:
            frame.pack_forget()
        self._tab_frames[idx].pack(fill="both", expand=True)
        for i, b in enumerate(self._tab_btns):
            b.config(
                bg=ACCENT if i == idx else PANEL2,
                fg="#FFFFFF" if i == idx else MUTED,
            )

    def _on_new_booking(self, record):
        history_tab = self._tab_frames[2]
        if hasattr(history_tab, "_refresh"):
            history_tab._refresh()


# ═════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═════════════════════════════════════════════════════════════

def open_donation_portal(parent):
    """
    Open the Donation Portal as a modal window.
    Call from main.py when the Donate button is clicked.
    """
    portal = DonationPortal(parent)
    portal.wait_window()