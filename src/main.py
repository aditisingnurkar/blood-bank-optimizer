import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

from src.allocation_engine import allocation_pipeline
from src.data_preprocessing import HospitalRequest
from src.donation_portal import open_donation_portal


# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _path(*parts):
    return os.path.join(BASE_DIR, "..", *parts)


# ─────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────

inventory_df = pd.read_csv(_path("data", "blood_inventory.csv"))
requests_df  = pd.read_csv(_path("data", "hospital_requests.csv"))
distance_df  = pd.read_csv(_path("output", "distance_matrix.csv"))
log_path     = _path("output", "distribution_log.csv")

inventory_df["expiry_date"] = pd.to_datetime(inventory_df["expiry_date"])
requests_df["request_date"] = pd.to_datetime(requests_df["request_date"])


# ─────────────────────────────────────────────────────────────
# PALETTE  — navy, not too dark, not flashy
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
SEL_ROW = "#2A3F52"

SC = [
    ("#4A9EDB", "#4A9EDB"),
    ("#4CAF82", "#4CAF82"),
    ("#E8A83A", "#E8A83A"),
    ("#E05C5C", "#E05C5C"),
]

FF = "Segoe UI"

def F(sz, wt="normal"):
    return (FF, sz, wt)


# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# WIDGET HELPERS
# ─────────────────────────────────────────────────────────────

def make_card(parent, **kw):
    d = dict(bg=PANEL, highlightthickness=1,
             highlightbackground=BORDER, bd=0)
    d.update(kw)
    return tk.Frame(parent, **d)

def lbl(parent, text, sz=9, wt="normal", fg=TEXT, **kw):
    bg = kw.pop("bg", parent["bg"])
    return tk.Label(parent, text=text, font=F(sz, wt), fg=fg, bg=bg, **kw)

def hsep(parent):
    return tk.Frame(parent, bg=BORDER, height=1)

def styled_combobox(parent, values, width=16):
    return ttk.Combobox(parent, values=values, state="readonly",
                        width=width, font=F(9))

def styled_entry(parent, width=16):
    return tk.Entry(parent, font=F(9), bg=PANEL2, fg=TEXT,
                    insertbackground=ACCENT, relief="flat", bd=0,
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=ACCENT, width=width)

def styled_button(parent, text, command, color=None, width=20):
    color = color or ACCENT
    b = tk.Button(parent, text=text, command=command,
                  font=F(10, "bold"), bg=color, fg="#FFFFFF",
                  activebackground=DIM_ACC, activeforeground="#FFFFFF",
                  relief="flat", bd=0, cursor="hand2",
                  width=width, pady=8)
    b.bind("<Enter>", lambda e: b.config(bg=DIM_ACC))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


# ─────────────────────────────────────────────────────────────
# TTK STYLES
# ─────────────────────────────────────────────────────────────

def configure_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure("Treeview",
                background=PANEL, foreground=TEXT,
                fieldbackground=PANEL, rowheight=26,
                font=F(9), borderwidth=0)
    s.configure("Treeview.Heading",
                background=PANEL2, foreground=ACCENT,
                font=F(9, "bold"), relief="flat", borderwidth=0)
    s.map("Treeview",
          background=[("selected", SEL_ROW)],
          foreground=[("selected", TEXT)])
    s.map("Treeview.Heading",
          background=[("active", ACCENT)])

    s.configure("TCombobox",
                fieldbackground=PANEL2, background=PANEL2,
                foreground=TEXT, arrowcolor=ACCENT,
                bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                insertcolor=ACCENT)
    s.map("TCombobox",
          fieldbackground=[("readonly", PANEL2)],
          foreground=[("readonly", TEXT)],
          selectbackground=[("readonly", ACCENT)],
          selectforeground=[("readonly", TEXT)])

    s.configure("Vertical.TScrollbar",
                background=PANEL, troughcolor=BG,
                arrowcolor=MUTED, bordercolor=BORDER)


# ─────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────

class BloodDashboard(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("HEMATIX — Blood Allocation System")
        self.geometry("1360x860")
        self.minsize(1200, 780)
        self.configure(bg=BG)
        self.resizable(True, True)
        configure_styles(self)
        self._build_ui()
        self._load_table()
        self._refresh_stats()

    # ── TOPBAR ───────────────────────────────────────────────

    def _build_topbar(self):
        bar = tk.Frame(self, bg=PANEL, height=52,
                       highlightthickness=1, highlightbackground=BORDER)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Frame(bar, bg=ACCENT, width=4).pack(side="left", fill="y")

        inner = tk.Frame(bar, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=16)

        lbl(inner, "◈  HEMATIX", 14, "bold",
            fg=ACCENT, bg=PANEL).pack(side="left", pady=14)
        lbl(inner, "BLOOD ALLOCATION MANAGEMENT SYSTEM", 9,
            fg=MUTED, bg=PANEL).pack(side="left", padx=14)

        dot = tk.Frame(inner, bg=PANEL)
        dot.pack(side="right")
        lbl(dot, "● LIVE", 9, fg=SUCCESS, bg=PANEL).pack(pady=14)

    # ── FULL UI ──────────────────────────────────────────────

    def _build_ui(self):
        self._build_topbar()

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # sidebar | main
        sidebar = tk.Frame(body, bg=BG, width=300)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        self._build_sidebar(sidebar)
        self._build_main(main)

    # ── SIDEBAR: form + stats ─────────────────────────────────

    def _build_sidebar(self, parent):

        # ── FORM CARD ──
        form_card = make_card(parent)
        form_card.pack(fill="x", pady=(12, 0))

        fhdr = tk.Frame(form_card, bg=ACCENT, height=36)
        fhdr.pack(fill="x")
        fhdr.pack_propagate(False)
        lbl(fhdr, "  ⊕  NEW REQUEST", 10, "bold",
            fg="#FFFFFF", bg=ACCENT).pack(side="left", pady=8)

        fbody = tk.Frame(form_card, bg=PANEL)
        fbody.pack(fill="x", padx=14, pady=12)

        # 2-column grid — all 4 fields visible without scrolling
        g = tk.Frame(fbody, bg=PANEL)
        g.pack(fill="x")
        g.columnconfigure(0, weight=1)
        g.columnconfigure(1, weight=1)

        hospital_ids = sorted(distance_df["hospital_id"].unique().tolist())

        lbl(g, "HOSPITAL ID", 8, fg=MUTED, bg=PANEL).grid(
            row=0, column=0, sticky="w", pady=(4, 2), padx=(0, 6))
        self.cb_hospital = styled_combobox(g, hospital_ids, width=13)
        self.cb_hospital.grid(row=1, column=0, sticky="ew",
                               ipady=3, pady=(0, 6), padx=(0, 6))

        lbl(g, "BLOOD TYPE", 8, fg=MUTED, bg=PANEL).grid(
            row=0, column=1, sticky="w", pady=(4, 2))
        self.cb_blood = styled_combobox(
            g, ["A+","A-","B+","B-","AB+","AB-","O+","O-"], width=13)
        self.cb_blood.grid(row=1, column=1, sticky="ew",
                            ipady=3, pady=(0, 6))

        lbl(g, "UNITS REQUIRED", 8, fg=MUTED, bg=PANEL).grid(
            row=2, column=0, sticky="w", pady=(4, 2), padx=(0, 6))
        self.entry_units = styled_entry(g, width=13)
        self.entry_units.grid(row=3, column=0, sticky="ew",
                               ipady=4, pady=(0, 6), padx=(0, 6))

        lbl(g, "URGENCY LEVEL", 8, fg=MUTED, bg=PANEL).grid(
            row=2, column=1, sticky="w", pady=(4, 2))
        self.cb_urgency = styled_combobox(
            g, ["Emergency","High","Medium","Low"], width=13)
        self.cb_urgency.grid(row=3, column=1, sticky="ew",
                              ipady=3, pady=(0, 6))

        hsep(fbody).pack(fill="x", pady=(6, 10))

        # Submit button
        styled_button(fbody, "▶  SUBMIT REQUEST",
                      self._submit, color=ACCENT).pack(fill="x")

        # Donate button — outlined, distinct from submit
        donate_btn = tk.Button(
            fbody,
            text="♥  DONATE BLOOD",
            command=lambda: open_donation_portal(self),
            font=F(10, "bold"),
            bg=PANEL,
            fg=ACCENT,
            activebackground=ACCENT,
            activeforeground="#FFFFFF",
            relief="flat", bd=0,
            cursor="hand2",
            pady=7,
            highlightthickness=1,
            highlightbackground=ACCENT,
            highlightcolor=DIM_ACC,
        )
        donate_btn.pack(fill="x", pady=(8, 0))
        donate_btn.bind("<Enter>",
            lambda e: donate_btn.config(bg=ACCENT, fg="#FFFFFF"))
        donate_btn.bind("<Leave>",
            lambda e: donate_btn.config(bg=PANEL, fg=ACCENT))

        # ── STAT CARDS 2×2 ──
        stats_outer = tk.Frame(parent, bg=BG)
        stats_outer.pack(fill="x", pady=(10, 0))

        self.stat_total  = tk.StringVar(value="—")
        self.stat_types  = tk.StringVar(value="—")
        self.stat_banks  = tk.StringVar(value="—")
        self.stat_expiry = tk.StringVar(value="—")

        specs = [
            ("TOTAL UNITS",   self.stat_total,  SC[0]),
            ("BLOOD TYPES",   self.stat_types,  SC[1]),
            ("ACTIVE BANKS",  self.stat_banks,  SC[2]),
            ("EXPIRING ≤7d",  self.stat_expiry, SC[3]),
        ]

        for i, (title, var, (border_c, text_c)) in enumerate(specs):
            sc = make_card(stats_outer,
                           highlightbackground=border_c,
                           highlightthickness=1)
            row, col = divmod(i, 2)
            sc.grid(row=row, column=col, sticky="ew",
                    padx=(0 if col == 0 else 5, 0),
                    pady=(0 if row == 0 else 5, 0))
            stats_outer.columnconfigure(col, weight=1)

            inner = tk.Frame(sc, bg=PANEL)
            inner.pack(padx=10, pady=8, fill="x")
            lbl(inner, title, 8, fg=MUTED, bg=PANEL).pack(anchor="w")
            tk.Label(inner, textvariable=var,
                     font=F(20, "bold"), fg=text_c,
                     bg=PANEL).pack(anchor="w")

    # ── MAIN AREA ────────────────────────────────────────────

    def _build_main(self, parent):
        # TOP HALF: result panel | inventory table
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="both", expand=True, pady=(12, 10))

        result_col = tk.Frame(top, bg=BG)
        result_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        inv_col = tk.Frame(top, bg=BG, width=360)
        inv_col.pack(side="right", fill="y")
        inv_col.pack_propagate(False)

        self._build_result_panel(result_col)
        self._build_inventory_panel(inv_col)

        # BOTTOM: chart strip
        self._build_chart_panel(parent)

    # ── RESULT PANEL (hero) ──────────────────────────────────

    def _build_result_panel(self, parent):
        c = make_card(parent)
        c.pack(fill="both", expand=True)

        # Header
        rhdr = tk.Frame(c, bg=PANEL2, height=36)
        rhdr.pack(fill="x")
        rhdr.pack_propagate(False)
        lbl(rhdr, "  ▤  ALLOCATION RESULT", 10, "bold",
            fg=TEXT, bg=PANEL2).pack(side="left", pady=8)

        self.lbl_status_badge = lbl(
            rhdr, "  PENDING  ", 8, "bold",
            fg=BG, bg=MUTED)
        self.lbl_status_badge.pack(side="right", padx=12, pady=6)

        # Big status text
        status_frame = tk.Frame(c, bg=PANEL)
        status_frame.pack(fill="x", padx=20, pady=(14, 8))

        self.result_status_var = tk.StringVar(value="── PENDING ──")
        self.result_status_lbl = tk.Label(
            status_frame, textvariable=self.result_status_var,
            font=F(22, "bold"), fg=MUTED, bg=PANEL, anchor="w")
        self.result_status_lbl.pack(fill="x")

        self.result_var = tk.StringVar(
            value="Fill in the form and submit a request.")
        tk.Label(status_frame, textvariable=self.result_var,
                 font=F(10), fg=MUTED, bg=PANEL,
                 wraplength=500, justify="left", anchor="w").pack(
            fill="x", pady=(4, 0))

        hsep(c).pack(fill="x", pady=(8, 0))

        # Breakdown sub-header
        brk_hdr = tk.Frame(c, bg=PANEL2, height=32)
        brk_hdr.pack(fill="x")
        brk_hdr.pack_propagate(False)
        lbl(brk_hdr, "  Banks used in this allocation", 9, "bold",
            fg=MUTED, bg=PANEL2).pack(side="left", pady=7)

        self.v_sort_note = tk.StringVar(
            value="Sorted by: ① nearest distance  ② earliest expiry")
        tk.Label(brk_hdr, textvariable=self.v_sort_note,
                 font=F(8), fg=MUTED, bg=PANEL2).pack(
            side="right", padx=12, pady=7)

        # Breakdown table
        brk_wrap = tk.Frame(c, bg=PANEL)
        brk_wrap.pack(fill="both", expand=True, padx=14, pady=(8, 14))

        brk_cols = ("bank", "distance_km", "expiry", "days_left",
                    "stock_before", "units_taken", "stock_after")
        self.brk_table = ttk.Treeview(brk_wrap, columns=brk_cols,
                                       show="headings", height=7)
        for col, hd, w, a in [
            ("bank",         "Bank",          80,  "w"),
            ("distance_km",  "Distance (km)", 100, "center"),
            ("expiry",       "Expiry Date",   100, "center"),
            ("days_left",    "Days Left",      76, "center"),
            ("stock_before", "Stock Before",   90, "center"),
            ("units_taken",  "Allocated",      76, "center"),
            ("stock_after",  "Stock After",    90, "center"),
        ]:
            self.brk_table.heading(col, text=hd)
            self.brk_table.column(col, width=w, anchor=a, minwidth=40)

        bvsb = ttk.Scrollbar(brk_wrap, orient="vertical",
                              command=self.brk_table.yview)
        self.brk_table.configure(yscrollcommand=bvsb.set)
        self.brk_table.pack(side="left", fill="both", expand=True)
        bvsb.pack(side="right", fill="y")

        self.brk_table.tag_configure("allocated", foreground=SUCCESS)
        self.brk_table.tag_configure("partial",   foreground=WARN)

    # ── INVENTORY PANEL ──────────────────────────────────────

    def _build_inventory_panel(self, parent):
        c = make_card(parent)
        c.pack(fill="both", expand=True)

        ihdr = tk.Frame(c, bg=PANEL2, height=36)
        ihdr.pack(fill="x")
        ihdr.pack_propagate(False)
        lbl(ihdr, "  ▤  INVENTORY OVERVIEW", 10, "bold",
            fg=TEXT, bg=PANEL2).pack(side="left", pady=8)

        filt_row = tk.Frame(c, bg=PANEL)
        filt_row.pack(fill="x", padx=10, pady=(6, 4))
        lbl(filt_row, "FILTER TYPE:", 8, fg=MUTED, bg=PANEL).pack(side="left")
        self.cb_filter = styled_combobox(filt_row,
            ["All","A+","A-","B+","B-","AB+","AB-","O+","O-"], width=8)
        self.cb_filter.set("All")
        self.cb_filter.pack(side="left", padx=6)
        self.cb_filter.bind("<<ComboboxSelected>>",
                            lambda e: self._load_table())

        hsep(c).pack(fill="x")

        wrap = tk.Frame(c, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        cols = ("bank_id", "blood_type", "units_available", "expiry_date")
        self.table = ttk.Treeview(wrap, columns=cols,
                                   show="headings", selectmode="browse")
        for col, hd, w, a in [
            ("bank_id",         "Bank",    90,  "w"),
            ("blood_type",      "Type",    60,  "center"),
            ("units_available", "Units",   65,  "center"),
            ("expiry_date",     "Expiry", 110,  "center"),
        ]:
            self.table.heading(col, text=hd)
            self.table.column(col, width=w, anchor=a, minwidth=40)

        vsb = ttk.Scrollbar(wrap, orient="vertical",
                            command=self.table.yview)
        self.table.configure(yscrollcommand=vsb.set)
        self.table.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.table.tag_configure("odd",  background=ALT)
        self.table.tag_configure("even", background=PANEL)
        self.table.tag_configure("warn", foreground=WARN)
        self.table.tag_configure("crit", foreground=FAIL)

    # ── CHART PANEL (full-width strip at bottom) ─────────────

    def _build_chart_panel(self, parent):
        c = make_card(parent)
        c.pack(fill="x")

        chdr = tk.Frame(c, bg=PANEL2, height=36)
        chdr.pack(fill="x")
        chdr.pack_propagate(False)
        lbl(chdr, "  ◉  ANALYTICS", 10, "bold",
            fg=TEXT, bg=PANEL2).pack(side="left", pady=8)

        btn_row = tk.Frame(chdr, bg=PANEL2)
        btn_row.pack(side="right", padx=10, pady=4)

        charts = [
            ("Availability", self._chart_availability, ACCENT),
            ("Demand",       self._chart_demand,        WARN),
            ("Heatmap",      self._chart_heatmap,       SUCCESS),
            ("Distribution", self._chart_dist,          MUTED),
        ]
        self._chart_btns = {}
        for i, (label, cmd, col) in enumerate(charts):
            b = tk.Button(btn_row, text=label, command=cmd,
                          font=F(8),
                          bg=ACCENT if i == 0 else PANEL,
                          fg="#FFFFFF" if i == 0 else MUTED,
                          activebackground=ACCENT,
                          activeforeground="#FFFFFF",
                          relief="flat", bd=0,
                          cursor="hand2", padx=10, pady=4)
            b.pack(side="left", padx=(0, 4))
            self._chart_btns[label] = b

        self.fig = Figure(figsize=(13, 2.8), facecolor=PANEL, tight_layout=True)
        self.ax  = self.fig.add_subplot(111)
        self._style_ax(self.ax)

        self.canvas = FigureCanvasTkAgg(self.fig, master=c)
        self.canvas.get_tk_widget().configure(bg=PANEL, highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="x", padx=10, pady=(4, 10))
        self._chart_availability()

    # ── STATS REFRESH ────────────────────────────────────────

    def _refresh_stats(self):
        now  = pd.Timestamp.now()
        soon = int(((inventory_df["expiry_date"] - now).dt.days <= 7).sum())
        self.stat_total.set(str(int(inventory_df["units_available"].sum())))
        self.stat_types.set(str(inventory_df["blood_type"].nunique()))
        self.stat_banks.set(str(inventory_df["bank_id"].nunique()))
        self.stat_expiry.set(str(soon))

    # ── TABLE LOAD ───────────────────────────────────────────

    def _load_table(self, highlight_blood=None, highlight_hospital=None):
        for row in self.table.get_children():
            self.table.delete(row)

        filt = self.cb_filter.get() if hasattr(self, "cb_filter") else "All"
        df = inventory_df.copy()
        if filt != "All":
            df = df[df["blood_type"] == filt]
        df = df.sort_values("expiry_date")

        now = pd.Timestamp.now()
        for i, (_, row) in enumerate(df.iterrows()):
            days = (row["expiry_date"] - now).days
            expiry_str = (row["expiry_date"].strftime("%Y-%m-%d")
                          if hasattr(row["expiry_date"], "strftime")
                          else str(row["expiry_date"]))
            tags = ["odd" if i % 2 else "even"]
            if days <= 3:   tags.append("crit")
            elif days <= 7: tags.append("warn")
            self.table.insert("", "end", tags=tags, values=(
                row["bank_id"],
                row["blood_type"],
                int(row["units_available"]),
                expiry_str,
            ))

    # ── SUBMIT ───────────────────────────────────────────────

    def _submit(self):
        blood    = self.cb_blood.get()
        hospital = self.cb_hospital.get()
        urgency  = self.cb_urgency.get()

        try:
            units = int(self.entry_units.get())
        except ValueError:
            messagebox.showerror("Input Error", "Units must be a whole number.")
            return

        if not blood or not hospital or not urgency:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return
        if units <= 0:
            messagebox.showerror("Input Error", "Units must be a positive number.")
            return

        req = HospitalRequest(
            request_id="R_NEW",
            hospital_id=hospital,
            blood_type=blood,
            units_required=units,
            urgency=urgency,
        )

        result = allocation_pipeline(inventory_df, [req], distance_df)[0]
        log_transaction(result)

        # ── Capture stock BEFORE deduction so breakdown can show it ──
        pre_stock = {}
        for detail in result.get("details", []):
            bid = detail["bank_id"]
            ir  = inventory_df[
                (inventory_df["bank_id"]    == bid) &
                (inventory_df["blood_type"] == blood)
            ]
            pre_stock[bid] = int(ir.iloc[0]["units_available"]) if not ir.empty else 0

        # ── Deduct allocated units from inventory_df in memory ──
        for detail in result.get("details", []):
            bank_id     = detail["bank_id"]
            units_taken = detail["units_taken"]
            mask = (
                (inventory_df["bank_id"]    == bank_id) &
                (inventory_df["blood_type"] == blood)
            )
            inventory_df.loc[mask, "units_available"] -= units_taken
            inventory_df.loc[mask, "units_available"] = (
                inventory_df.loc[mask, "units_available"].clip(lower=0))

        # ── Persist to disk ──
        inventory_df.to_csv(_path("data", "blood_inventory.csv"), index=False)

        # ── Refresh inventory table, stats, chart ──
        self._load_table(highlight_blood=blood, highlight_hospital=hospital)
        self._refresh_stats()
        self._chart_availability()

        # ── Update result display ──
        status  = result["status"]
        details = result.get("details", [])
        detail_str = ", ".join(
            f"{d['bank_id']}→{d['units_taken']}" for d in details) or "—"

        status_colors = {
            "SUCCESS": SUCCESS,
            "PARTIAL": WARN,
            "FAILED":  FAIL,
        }
        color = status_colors.get(status, MUTED)

        # Badge
        self.lbl_status_badge.config(
            text=f"  {status}  ", fg=BG, bg=color)

        # Big status label
        status_labels = {
            "SUCCESS": "Fully Allocated",
            "PARTIAL": "Partially Allocated",
            "FAILED":  "Allocation Failed",
        }
        self.result_status_var.set(status_labels.get(status, status))
        self.result_status_lbl.config(fg=color)

        self.result_var.set(f"{result['message']}\n{detail_str}")

        # Fill breakdown table — pass pre-deduction stock
        self._fill_breakdown(details, hospital, blood, pre_stock)

    # ── FILL BREAKDOWN ───────────────────────────────────────

    def _fill_breakdown(self, details, hospital_id, blood_type, pre_stock=None):
        """
        Populate the 'Banks used in this allocation' treeview.

        Columns:
          Bank | Distance (km) | Expiry Date | Days Left |
          Stock Before | Allocated | Stock After

        Stock Before = units available BEFORE this allocation.
        Stock After  = units available NOW (live from inventory_df post-deduction).
        """
        for r in self.brk_table.get_children():
            self.brk_table.delete(r)

        pre_stock = pre_stock or {}
        now = pd.Timestamp.now()

        for d in details:
            bid = d["bank_id"]
            ut  = d["units_taken"]

            # Distance to requesting hospital
            dr   = distance_df[(distance_df["bank_id"]     == bid) &
                                (distance_df["hospital_id"] == hospital_id)]
            dist = (f"{dr['distance_km'].values[0]:.1f}"
                    if not dr.empty else "—")

            # Current (post-deduction) row from inventory
            ir = inventory_df[inventory_df["bank_id"] == bid]
            if not ir.empty:
                exp         = ir.iloc[0]["expiry_date"].strftime("%Y-%m-%d")
                days        = (ir.iloc[0]["expiry_date"] - now).days
                stock_after = int(ir.iloc[0]["units_available"])
            else:
                exp, days, stock_after = "—", "—", "—"

            stock_before = pre_stock.get(bid, "—")

            self.brk_table.insert("", "end", tags=("allocated",),
                values=(bid, dist, exp, days,
                        stock_before, ut, stock_after))

        # Update sort note with primary bank details
        if details:
            first = details[0]["bank_id"]
            dr    = distance_df[(distance_df["bank_id"]     == first) &
                                 (distance_df["hospital_id"] == hospital_id)]
            d_str = (f"{dr['distance_km'].values[0]:.1f} km"
                     if not dr.empty else "—")
            ir    = inventory_df[inventory_df["bank_id"] == first]
            days2 = ((ir.iloc[0]["expiry_date"] - now).days
                     if not ir.empty else "—")
            self.v_sort_note.set(
                f"Sorted by: ① nearest distance  ② earliest expiry"
                f"   ·   Primary bank {first}: {d_str},  {days2} days to expiry")

    # ── CHART HELPERS ────────────────────────────────────────

    def _style_ax(self, ax):
        ax.set_facecolor(PANEL)
        ax.set_axisbelow(True)
        ax.grid(True, color=BORDER, linewidth=0.5)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.xaxis.label.set_color(MUTED)
        ax.yaxis.label.set_color(MUTED)
        ax.title.set_color(TEXT)
        ax.title.set_fontsize(9)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER)

    def _redraw(self):
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self._style_ax(self.ax)
        return self.ax

    def _switch_chart_btn(self, active_label):
        for label, b in self._chart_btns.items():
            b.config(
                bg=ACCENT if label == active_label else PANEL,
                fg="#FFFFFF" if label == active_label else MUTED)

    def _chart_availability(self):
        self._switch_chart_btn("Availability")
        ax = self._redraw()
        grouped = inventory_df.groupby("blood_type")["units_available"].sum()
        colors  = [FAIL if v == grouped.min() else ACCENT
                   for v in grouped.values]
        grouped.plot(kind="bar", ax=ax, color=colors,
                     edgecolor="none", width=0.65)
        ax.set_title("Blood Availability by Type", fontsize=9)
        ax.set_xlabel("")
        ax.set_ylabel("Units", fontsize=8)
        plt.setp(ax.get_xticklabels(), rotation=0, fontsize=8)
        self.canvas.draw()

    def _chart_demand(self):
        self._switch_chart_btn("Demand")
        ax = self._redraw()
        grouped = requests_df.groupby("request_date")["units_required"].sum()
        ax.plot(grouped.index, grouped.values,
                color=WARN, linewidth=1.8, marker="o",
                markersize=3, markerfacecolor=FAIL)
        ax.fill_between(grouped.index, grouped.values,
                        alpha=0.12, color=WARN)
        ax.set_title("Demand Over Time", fontsize=9)
        ax.set_ylabel("Units Required", fontsize=8)
        ax.tick_params(axis="x", labelrotation=30, labelsize=7)
        self.canvas.draw()

    def _chart_heatmap(self):
        self._switch_chart_btn("Heatmap")
        ax = self._redraw()
        pivot = inventory_df.pivot_table(
            values="units_available", index="bank_id",
            columns="blood_type", aggfunc="sum", fill_value=0)
        sns.heatmap(pivot, ax=ax, annot=True, fmt=".0f",
                    cmap="Blues", linewidths=0.5, linecolor=BG,
                    annot_kws={"size": 7}, cbar_kws={"shrink": 0.6})
        ax.set_title("Availability Heatmap", fontsize=9)
        ax.set_xlabel("Blood Type", fontsize=8)
        ax.set_ylabel("Bank", fontsize=8)
        ax.tick_params(labelsize=7)
        self.canvas.draw()

    def _chart_dist(self):
        self._switch_chart_btn("Distribution")
        ax = self._redraw()
        sns.histplot(inventory_df["units_available"],
                     ax=ax, color=ACCENT, kde=True, bins=15,
                     edgecolor="none",
                     line_kws={"color": WARN, "linewidth": 1.5})
        ax.set_title("Unit Distribution", fontsize=9)
        ax.set_xlabel("Units Available", fontsize=8)
        ax.set_ylabel("Frequency", fontsize=8)
        self.canvas.draw()


# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    BloodDashboard().mainloop()