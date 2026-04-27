"""
Blood Bank Optimizer — main.py

Layout (no scrolling anywhere):
  ┌─ topbar ──────────────────────────────────────────────────────┐
  ├─ left sidebar (fixed 300px) ──┬─ main area ───────────────────┤
  │  Form: 2-col grid, no scroll  │  RESULT panel (hero, large)   │
  │  Stat cards (4, stacked)      │  Allocation breakdown table   │
  │                               │  ─────────────────────────── │
  │                               │  Inventory table (compact)    │
  ├───────────────────────────────┴───────────────────────────────┤
  │  Analytics chart (full width, tabbed)                         │
  └───────────────────────────────────────────────────────────────┘
"""

import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

from allocation_engine import allocation_pipeline
from data_preprocessing import HospitalRequest

# ── PATHS ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def P(*parts): return os.path.join(BASE_DIR, "..", *parts)

# ── DATA ──────────────────────────────────────────────────────────────
inventory_df = pd.read_csv(P("data", "blood_inventory.csv"))
requests_df  = pd.read_csv(P("data", "hospital_requests.csv"))
distance_df  = pd.read_csv(P("output", "distance_matrix.csv"))
log_path     = P("output", "distribution_log.csv")
inventory_df["expiry_date"] = pd.to_datetime(inventory_df["expiry_date"])
requests_df["request_date"] = pd.to_datetime(requests_df["request_date"])

# ── PALETTE ───────────────────────────────────────────────────────────
# Navy base, not too dark, not too flashy
BG       = "#1C2B3A"   # page background
PANEL    = "#243447"   # card / panel
PANEL2   = "#1A2535"   # slightly darker panel
BORDER   = "#2E4158"   # border
TEXT     = "#E8EDF2"   # primary text
MUTED    = "#7D93A8"   # secondary text
ACCENT   = "#4A9EDB"   # steel blue — primary action / highlight
DIM_ACC  = "#3A7EBB"   # hover
SUCCESS  = "#4CAF82"   # teal green
WARN     = "#E8A83A"   # warm amber
FAIL     = "#E05C5C"   # soft red

# Stat card colour pairs (border, text)
SC = [
    ("#4A9EDB", "#4A9EDB"),   # blue
    ("#4CAF82", "#4CAF82"),   # green
    ("#E8A83A", "#E8A83A"),   # amber
    ("#E05C5C", "#E05C5C"),   # red
]

ALT     = "#1E2F3F"
SEL_ROW = "#2A3F52"
FF      = "Segoe UI"

def F(sz, wt="normal"): return (FF, sz, wt)

# ── LOGGING ───────────────────────────────────────────────────────────
def log_transaction(result):
    pd.DataFrame([{
        "request_id":      result["request_id"],
        "hospital_id":     result["hospital_id"],
        "blood_type":      result["blood_type"],
        "status":          result["status"],
        "message":         result["message"],
        "units_allocated": result["units_allocated"],
        "details":         str(result["details"]),
    }]).to_csv(log_path, mode="a", header=False, index=False)

# ── HELPERS ───────────────────────────────────────────────────────────
def panel(parent, **kw):
    d = dict(bg=PANEL, highlightthickness=1, highlightbackground=BORDER, bd=0)
    d.update(kw)
    return tk.Frame(parent, **d)

def lbl(parent, text, sz=9, wt="normal", fg=TEXT, **kw):
    bg = kw.pop("bg", parent["bg"])
    return tk.Label(parent, text=text, font=F(sz, wt), fg=fg, bg=bg, **kw)

def hsep(parent): return tk.Frame(parent, bg=BORDER, height=1)

def combo(parent, values, width=16):
    return ttk.Combobox(parent, values=values, state="readonly",
                        width=width, font=F(9))

def ientry(parent, width=16):
    return tk.Entry(parent, font=F(9), bg=PANEL2, fg=TEXT,
                    insertbackground=ACCENT, relief="flat", bd=0,
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=ACCENT, width=width)

def action_btn(parent, text, cmd, color=ACCENT, hover=DIM_ACC):
    b = tk.Button(parent, text=text, command=cmd,
                  font=F(10, "bold"), bg=color, fg="#FFFFFF",
                  activebackground=hover, activeforeground="#FFFFFF",
                  relief="flat", bd=0, cursor="hand2", pady=9)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

# ── TTK STYLES ────────────────────────────────────────────────────────
def apply_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("Treeview",
        background=PANEL, foreground=TEXT, fieldbackground=PANEL,
        rowheight=26, font=F(9), borderwidth=0)
    s.configure("Treeview.Heading",
        background=PANEL2, foreground=MUTED,
        font=F(8, "bold"), relief="flat", borderwidth=0)
    s.map("Treeview",
        background=[("selected", SEL_ROW)],
        foreground=[("selected", TEXT)])
    s.configure("TCombobox",
        fieldbackground=PANEL2, background=PANEL2, foreground=TEXT,
        arrowcolor=MUTED, bordercolor=BORDER,
        lightcolor=BORDER, darkcolor=BORDER,
        selectbackground=PANEL2, selectforeground=TEXT)
    s.map("TCombobox",
        fieldbackground=[("readonly", PANEL2)],
        foreground=[("readonly", TEXT)],
        selectbackground=[("readonly", PANEL2)],
        selectforeground=[("readonly", TEXT)])
    s.configure("Vertical.TScrollbar",
        background=PANEL, troughcolor=BG, arrowcolor=MUTED, bordercolor=BORDER)

# ── APP ───────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blood Bank Optimizer")
        self.geometry("1360x860")
        self.minsize(1200, 780)
        self.configure(bg=BG)
        apply_styles(self)
        self._build()
        self._reload_inv_table()
        self._refresh_stats()

    # ────────────────────────────────────────
    def _build(self):
        self._topbar()

        # outer body: sidebar | main
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        sidebar = tk.Frame(body, bg=BG, width=300)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        self._sidebar(sidebar)
        self._main_area(main)

    # ────────────────────────────────────────
    def _topbar(self):
        bar = tk.Frame(self, bg=PANEL, height=52,
                       highlightthickness=1, highlightbackground=BORDER)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        # accent left stripe
        tk.Frame(bar, bg=ACCENT, width=4).pack(side="left", fill="y")
        inner = tk.Frame(bar, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=16)
        lbl(inner, "Blood Bank Optimizer", 14, "bold",
            fg=TEXT, bg=PANEL).pack(side="left", pady=14)
        lbl(inner, "Allocation & Inventory Dashboard", 9,
            fg=MUTED, bg=PANEL).pack(side="left", padx=14)

    # ────────────────────────────────────────
    def _sidebar(self, parent):
        # ── FORM ────────────────────────────
        form_card = panel(parent)
        form_card.pack(fill="x", pady=(12, 0))

        fhdr = tk.Frame(form_card, bg=ACCENT, height=34)
        fhdr.pack(fill="x")
        fhdr.pack_propagate(False)
        lbl(fhdr, "  New Request", 10, "bold",
            fg="#FFFFFF", bg=ACCENT).pack(side="left", pady=7)

        fbody = tk.Frame(form_card, bg=PANEL)
        fbody.pack(fill="x", padx=14, pady=12)

        # 2-column grid for fields — no scrolling needed
        grid = tk.Frame(fbody, bg=PANEL)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        def field(row, col, label_text, widget):
            lbl(grid, label_text, 8, fg=MUTED, bg=PANEL).grid(
                row=row*2, column=col, sticky="w", pady=(8, 2),
                padx=(0, 8 if col == 0 else 0))
            widget.grid(row=row*2+1, column=col, sticky="ew",
                        pady=(0, 0), padx=(0, 8 if col == 0 else 0),
                        ipady=4)

        hospital_ids = sorted(distance_df["hospital_id"].unique().tolist())
        self.cb_hospital = combo(fbody, hospital_ids, width=14)
        self.cb_blood    = combo(fbody,
            ["A+","A-","B+","B-","AB+","AB-","O+","O-"], width=14)
        self.ent_units   = ientry(fbody, width=14)
        self.cb_urgency  = combo(fbody,
            ["Emergency","High","Medium","Low"], width=14)

        # re-parent to grid
        self.cb_hospital.grid_remove()
        self.cb_blood.grid_remove()
        self.ent_units.grid_remove()
        self.cb_urgency.grid_remove()

        for w in (self.cb_hospital, self.cb_blood, self.ent_units, self.cb_urgency):
            w.configure(master=grid) if False else None

        # just pack them into the grid frame directly
        for w in (self.cb_hospital, self.cb_blood, self.ent_units, self.cb_urgency):
            w.pack_forget()

        lbl(grid, "Hospital", 8, fg=MUTED, bg=PANEL).grid(
            row=0, column=0, sticky="w", pady=(4,2), padx=(0,6))
        self.cb_hospital = combo(grid, hospital_ids, width=13)
        self.cb_hospital.grid(row=1, column=0, sticky="ew", ipady=3,
                               pady=(0,4), padx=(0,6))

        lbl(grid, "Blood Type", 8, fg=MUTED, bg=PANEL).grid(
            row=0, column=1, sticky="w", pady=(4,2))
        self.cb_blood = combo(grid,
            ["A+","A-","B+","B-","AB+","AB-","O+","O-"], width=13)
        self.cb_blood.grid(row=1, column=1, sticky="ew", ipady=3, pady=(0,4))

        lbl(grid, "Units Required", 8, fg=MUTED, bg=PANEL).grid(
            row=2, column=0, sticky="w", pady=(4,2), padx=(0,6))
        self.ent_units = ientry(grid, width=13)
        self.ent_units.grid(row=3, column=0, sticky="ew", ipady=4,
                             pady=(0,4), padx=(0,6))

        lbl(grid, "Urgency", 8, fg=MUTED, bg=PANEL).grid(
            row=2, column=1, sticky="w", pady=(4,2))
        self.cb_urgency = combo(grid,
            ["Emergency","High","Medium","Low"], width=13)
        self.cb_urgency.grid(row=3, column=1, sticky="ew", ipady=3, pady=(0,4))

        hsep(fbody).pack(fill="x", pady=(8, 10))
        action_btn(fbody, "Submit Request", self._submit).pack(fill="x")

        # ── STAT CARDS ──────────────────────
        stats_frame = tk.Frame(parent, bg=BG)
        stats_frame.pack(fill="x", pady=(10, 0))

        self.sv_total  = tk.StringVar(value="—")
        self.sv_types  = tk.StringVar(value="—")
        self.sv_banks  = tk.StringVar(value="—")
        self.sv_expiry = tk.StringVar(value="—")

        specs = [
            ("Total Units",  self.sv_total,  SC[0]),
            ("Blood Types",  self.sv_types,  SC[1]),
            ("Active Banks", self.sv_banks,  SC[2]),
            ("Expiring ≤7d", self.sv_expiry, SC[3]),
        ]

        # 2x2 grid of stat cards
        for i, (title, var, (border_c, text_c)) in enumerate(specs):
            sc = panel(stats_frame,
                       highlightbackground=border_c, highlightthickness=1)
            row, col = divmod(i, 2)
            sc.grid(row=row, column=col,
                    sticky="ew", padx=(0 if col == 0 else 5, 0),
                    pady=(0 if row == 0 else 5, 0))
            stats_frame.columnconfigure(col, weight=1)

            inner = tk.Frame(sc, bg=PANEL)
            inner.pack(padx=10, pady=8, fill="x")
            lbl(inner, title, 8, fg=MUTED, bg=PANEL).pack(anchor="w")
            tk.Label(inner, textvariable=var,
                     font=F(20, "bold"), fg=text_c, bg=PANEL).pack(anchor="w")

    # ────────────────────────────────────────
    def _main_area(self, parent):
        # TOP HALF: result hero | inventory table
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="both", expand=True, pady=(12, 10))

        result_col = tk.Frame(top, bg=BG)
        result_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        inv_col = tk.Frame(top, bg=BG, width=360)
        inv_col.pack(side="right", fill="y")
        inv_col.pack_propagate(False)

        self._result_panel(result_col)
        self._inv_panel(inv_col)

        # BOTTOM: chart
        self._chart_panel(parent)

    # ────────────────────────────────────────
    def _result_panel(self, parent):
        c = panel(parent)
        c.pack(fill="both", expand=True)

        # Header
        rhdr = tk.Frame(c, bg=PANEL2, height=36)
        rhdr.pack(fill="x")
        rhdr.pack_propagate(False)
        lbl(rhdr, "  Allocation Result", 10, "bold",
            fg=TEXT, bg=PANEL2).pack(side="left", pady=8)
        self.lbl_status_badge = lbl(
            rhdr, "  PENDING  ", 8, "bold",
            fg=BG, bg=MUTED)
        self.lbl_status_badge.pack(side="right", padx=12, pady=8)

        # Big status area
        status_frame = tk.Frame(c, bg=PANEL)
        status_frame.pack(fill="x", padx=20, pady=(16, 8))

        self.v_status_big = tk.StringVar(value="Awaiting first request")
        self.lbl_status_big = tk.Label(
            status_frame, textvariable=self.v_status_big,
            font=F(22, "bold"), fg=MUTED, bg=PANEL, anchor="w")
        self.lbl_status_big.pack(fill="x")

        self.v_message = tk.StringVar(value="Fill in the form and submit a request to see allocation results here.")
        tk.Label(status_frame, textvariable=self.v_message,
                 font=F(10), fg=MUTED, bg=PANEL,
                 wraplength=520, justify="left", anchor="w").pack(
            fill="x", pady=(4, 0))

        hsep(c).pack(fill="x", pady=(8, 0))

        # ── Breakdown table (the hero content) ──
        brk_hdr = tk.Frame(c, bg=PANEL2, height=32)
        brk_hdr.pack(fill="x")
        brk_hdr.pack_propagate(False)
        lbl(brk_hdr, "  Banks used in this allocation", 9, "bold",
            fg=MUTED, bg=PANEL2).pack(side="left", pady=7)

        # Sorting explanation
        self.v_sort_note = tk.StringVar(
            value="Sorted by: ① nearest distance  ② earliest expiry")
        tk.Label(brk_hdr, textvariable=self.v_sort_note,
                 font=F(8), fg=MUTED, bg=PANEL2).pack(
            side="right", padx=12, pady=7)

        brk_wrap = tk.Frame(c, bg=PANEL)
        brk_wrap.pack(fill="both", expand=True, padx=14, pady=(8, 14))

        brk_cols = ("bank", "distance_km", "expiry", "days_left",
                    "units_available", "units_taken")
        self.brk_table = ttk.Treeview(brk_wrap, columns=brk_cols,
                                       show="headings", height=7)
        for col, hd, w, a in [
            ("bank",            "Bank",         80, "w"),
            ("distance_km",     "Distance (km)",100, "center"),
            ("expiry",          "Expiry Date",  100, "center"),
            ("days_left",       "Days Left",     76, "center"),
            ("units_available", "Stock",         70, "center"),
            ("units_taken",     "Allocated",     76, "center"),
        ]:
            self.brk_table.heading(col, text=hd)
            self.brk_table.column(col, width=w, anchor=a, minwidth=50)

        bvsb = ttk.Scrollbar(brk_wrap, orient="vertical",
                              command=self.brk_table.yview)
        self.brk_table.configure(yscrollcommand=bvsb.set)
        self.brk_table.pack(side="left", fill="both", expand=True)
        bvsb.pack(side="right", fill="y")

        self.brk_table.tag_configure("allocated", foreground=SUCCESS)
        self.brk_table.tag_configure("partial",   foreground=WARN)

    # ────────────────────────────────────────
    def _inv_panel(self, parent):
        c = panel(parent)
        c.pack(fill="both", expand=True)

        ihdr = tk.Frame(c, bg=PANEL2, height=36)
        ihdr.pack(fill="x")
        ihdr.pack_propagate(False)
        lbl(ihdr, "  Inventory", 10, "bold",
            fg=TEXT, bg=PANEL2).pack(side="left", pady=8)

        filt_row = tk.Frame(c, bg=PANEL)
        filt_row.pack(fill="x", padx=10, pady=(6, 4))
        lbl(filt_row, "Filter:", 8, fg=MUTED, bg=PANEL).pack(side="left")
        self.cb_filter = combo(filt_row,
            ["All","A+","A-","B+","B-","AB+","AB-","O+","O-"], width=7)
        self.cb_filter.set("All")
        self.cb_filter.pack(side="left", padx=6)
        self.cb_filter.bind("<<ComboboxSelected>>",
                            lambda e: self._reload_inv_table())

        hsep(c).pack(fill="x")

        wrap = tk.Frame(c, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        cols = ("bank_id", "blood_type", "units", "days_left")
        self.inv_table = ttk.Treeview(wrap, columns=cols,
                                       show="headings", selectmode="browse")
        for col, hd, w, a in [
            ("bank_id",    "Bank",      90, "w"),
            ("blood_type", "Type",      60, "center"),
            ("units",      "Units",     65, "center"),
            ("days_left",  "Days Left", 70, "center"),
        ]:
            self.inv_table.heading(col, text=hd)
            self.inv_table.column(col, width=w, anchor=a, minwidth=40)

        vsb = ttk.Scrollbar(wrap, orient="vertical",
                            command=self.inv_table.yview)
        self.inv_table.configure(yscrollcommand=vsb.set)
        self.inv_table.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.inv_table.tag_configure("alt",  background=ALT)
        self.inv_table.tag_configure("warn", foreground=WARN)
        self.inv_table.tag_configure("crit", foreground=FAIL)

    # ────────────────────────────────────────
    def _chart_panel(self, parent):
        c = panel(parent)
        c.pack(fill="x", ipady=0)

        chdr = tk.Frame(c, bg=PANEL2, height=36)
        chdr.pack(fill="x")
        chdr.pack_propagate(False)
        lbl(chdr, "  Analytics", 10, "bold",
            fg=TEXT, bg=PANEL2).pack(side="left", pady=8)

        btn_row = tk.Frame(chdr, bg=PANEL2)
        btn_row.pack(side="right", padx=10, pady=4)

        self._chart_btns = {}
        for i, (label, key) in enumerate([
            ("Availability", "avail"),
            ("Demand",       "demand"),
            ("Heatmap",      "heatmap"),
            ("Distribution", "dist"),
        ]):
            b = tk.Button(btn_row, text=label,
                          command=lambda k=key: self._switch_chart(k),
                          font=F(8),
                          bg=ACCENT if i == 0 else PANEL,
                          fg="#FFFFFF" if i == 0 else MUTED,
                          activebackground=ACCENT, activeforeground="#FFFFFF",
                          relief="flat", bd=0, cursor="hand2",
                          padx=10, pady=4)
            b.pack(side="left", padx=(0, 4))
            self._chart_btns[key] = b

        self.fig = Figure(figsize=(13, 2.8), facecolor=PANEL, tight_layout=True)
        self.ax  = self.fig.add_subplot(111)
        self._style_ax(self.ax)

        self.canvas = FigureCanvasTkAgg(self.fig, master=c)
        self.canvas.get_tk_widget().configure(
            bg=PANEL, highlightthickness=0)
        self.canvas.get_tk_widget().pack(
            fill="x", padx=10, pady=(4, 10))
        self._switch_chart("avail")

    # ── DATA ─────────────────────────────────
    def _reload_inv_table(self):
        for r in self.inv_table.get_children():
            self.inv_table.delete(r)
        filt = self.cb_filter.get() if hasattr(self, "cb_filter") else "All"
        df = inventory_df.copy()
        if filt != "All":
            df = df[df["blood_type"] == filt]
        df = df.sort_values("expiry_date")
        now = pd.Timestamp.now()
        for i, (_, row) in enumerate(df.iterrows()):
            days = (row["expiry_date"] - now).days
            tags = ["alt"] if i % 2 == 0 else []
            if days <= 3:   tags.append("crit")
            elif days <= 7: tags.append("warn")
            self.inv_table.insert("", "end", tags=tags, values=(
                row["bank_id"], row["blood_type"],
                int(row["units_available"]), days,
            ))

    def _refresh_stats(self):
        now = pd.Timestamp.now()
        self.sv_total.set(str(int(inventory_df["units_available"].sum())))
        self.sv_types.set(str(inventory_df["blood_type"].nunique()))
        self.sv_banks.set(str(inventory_df["bank_id"].nunique()))
        self.sv_expiry.set(str(int(
            ((inventory_df["expiry_date"] - now).dt.days <= 7).sum())))

    # ── SUBMIT ───────────────────────────────
    def _submit(self):
        blood    = self.cb_blood.get()
        hospital = self.cb_hospital.get()
        urgency  = self.cb_urgency.get()
        try:
            units = int(self.ent_units.get())
        except ValueError:
            messagebox.showerror("Input Error", "Units must be a whole number.")
            return
        if not (blood and hospital and urgency):
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return
        if units <= 0:
            messagebox.showerror("Input Error", "Units must be positive.")
            return

        req = HospitalRequest(
            request_id="R_NEW", hospital_id=hospital,
            blood_type=blood, units_required=units, urgency=urgency,
        )
        result = allocation_pipeline(inventory_df, [req], distance_df)[0]
        log_transaction(result)
        self._reload_inv_table()
        self._refresh_stats()
        self._update_result(result, hospital)
        inventory_df.to_csv(P("data", "blood_inventory.csv"), index=False)

    def _update_result(self, result, hospital_id):
        status  = result["status"]
        details = result["details"]
        clr_map = {"SUCCESS": SUCCESS, "PARTIAL": WARN, "FAILED": FAIL}
        clr     = clr_map.get(status, MUTED)

        # Big status
        labels  = {"SUCCESS": "Fully Allocated",
                   "PARTIAL": "Partially Allocated",
                   "FAILED":  "Allocation Failed"}
        self.v_status_big.set(labels.get(status, status))
        self.lbl_status_big.config(fg=clr)
        self.v_message.set(result["message"])

        # Badge
        self.lbl_status_badge.config(
            text=f"  {status}  ", fg=BG, bg=clr)

        # Breakdown table
        for r in self.brk_table.get_children():
            self.brk_table.delete(r)

        now = pd.Timestamp.now()
        for d in details:
            bid = d["bank_id"]
            ut  = d["units_taken"]

            dr  = distance_df[(distance_df["bank_id"] == bid) &
                               (distance_df["hospital_id"] == hospital_id)]
            dist = f"{dr['distance_km'].values[0]:.1f}" if not dr.empty else "—"

            ir   = inventory_df[inventory_df["bank_id"] == bid]
            if not ir.empty:
                exp  = ir.iloc[0]["expiry_date"].strftime("%Y-%m-%d")
                days = (ir.iloc[0]["expiry_date"] - now).days
                stock = int(ir.iloc[0]["units_available"])
            else:
                exp, days, stock = "—", "—", "—"

            self.brk_table.insert("", "end", tags=("allocated",),
                values=(bid, dist, exp, days, stock, ut))

        # Sort note with live values
        if details:
            first = details[0]["bank_id"]
            dr = distance_df[(distance_df["bank_id"] == first) &
                              (distance_df["hospital_id"] == hospital_id)]
            d_str = f"{dr['distance_km'].values[0]:.1f} km" if not dr.empty else "—"
            ir = inventory_df[inventory_df["bank_id"] == first]
            days2 = (ir.iloc[0]["expiry_date"] - now).days if not ir.empty else "—"
            self.v_sort_note.set(
                f"Sorted by: ① nearest distance  ② earliest expiry"
                f"   ·   Primary bank {first}: {d_str},  {days2} days to expiry")

    # ── CHARTS ───────────────────────────────
    def _style_ax(self, ax):
        ax.set_facecolor(PANEL)
        ax.set_axisbelow(True)
        ax.grid(True, color=BORDER, linewidth=0.5)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.xaxis.label.set_color(MUTED)
        ax.yaxis.label.set_color(MUTED)
        ax.title.set_color(TEXT)
        ax.title.set_fontsize(9)
        for sp in ax.spines.values(): sp.set_edgecolor(BORDER)

    def _redraw(self):
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        self._style_ax(ax)
        return ax

    def _switch_chart(self, key):
        for k, b in self._chart_btns.items():
            b.config(bg=ACCENT if k == key else PANEL,
                     fg="#FFFFFF" if k == key else MUTED)
        {"avail":   self._chart_avail,
         "demand":  self._chart_demand,
         "heatmap": self._chart_heatmap,
         "dist":    self._chart_dist}[key]()

    def _chart_avail(self):
        ax = self._redraw()
        g  = inventory_df.groupby("blood_type")["units_available"].sum()
        colors = [ACCENT] * len(g)
        colors[int(g.values.argmin())] = FAIL
        ax.bar(g.index, g.values, color=colors,
               edgecolor=PANEL, width=0.6, linewidth=0.4)
        ax.set_title("Units Available by Blood Type")
        ax.set_ylabel("Units")
        self.canvas.draw()

    def _chart_demand(self):
        ax = self._redraw()
        g  = requests_df.groupby("request_date")["units_required"].sum()
        ax.plot(g.index, g.values, color=ACCENT, linewidth=1.6,
                marker="o", markersize=3, markerfacecolor=PANEL,
                markeredgecolor=ACCENT, markeredgewidth=1.2)
        ax.fill_between(g.index, g.values, alpha=0.12, color=ACCENT)
        ax.set_title("Demand Over Time")
        ax.set_ylabel("Units")
        ax.tick_params(axis="x", labelrotation=30, labelsize=7)
        self.canvas.draw()

    def _chart_heatmap(self):
        ax = self._redraw()
        pivot = inventory_df.pivot_table(
            values="units_available", index="bank_id",
            columns="blood_type", aggfunc="sum", fill_value=0)
        sns.heatmap(pivot, ax=ax, annot=True, fmt=".0f",
                    cmap="Blues", linewidths=0.4, linecolor=BG,
                    annot_kws={"size": 7}, cbar_kws={"shrink": 0.6})
        ax.set_title("Availability Heatmap (Bank × Type)")
        ax.tick_params(labelsize=7)
        self.canvas.draw()

    def _chart_dist(self):
        ax = self._redraw()
        ax.hist(inventory_df["units_available"], bins=14,
                color=ACCENT, edgecolor=PANEL, linewidth=0.4, alpha=0.85)
        ax.set_title("Distribution of Units per Inventory Entry")
        ax.set_xlabel("Units Available")
        ax.set_ylabel("Frequency")
        self.canvas.draw()


if __name__ == "__main__":
    App().mainloop()