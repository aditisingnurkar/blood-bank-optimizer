"""
Blood Allocation Dashboard — Day 4
Redesigned UI with tkinter + ttk styling
Dark clinical aesthetic: deep navy + crimson accents
"""

import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import os
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

from src.allocation_engine import allocation_pipeline
from src.data_preprocessing import HospitalRequest
from src.donation_portal import open_donation_portal          # ← NEW


# ============================================================
# COLOUR PALETTE
# ============================================================

C = {
    "bg":          "#0A0E1A",   # near-black navy
    "panel":       "#111827",   # card background
    "border":      "#1E2D45",   # subtle border
    "accent":      "#C0392B",   # blood crimson
    "accent2":     "#E74C3C",   # lighter red
    "gold":        "#F39C12",   # warning / partial
    "green":       "#27AE60",   # success
    "text":        "#ECF0F1",   # primary text
    "muted":       "#7F8C9A",   # secondary text
    "entry_bg":    "#0D1520",   # input background
    "entry_fg":    "#ECF0F1",
    "hover":       "#1A2840",
    "table_alt":   "#0F1825",
    "table_sel":   "#1B2F4A",
    "header_bg":   "#0D1520",
    "separator":   "#1E3050",
}

FONTS = {
    "title":   ("Courier New", 20, "bold"),
    "heading": ("Courier New", 12, "bold"),
    "label":   ("Courier New", 9),
    "input":   ("Courier New", 10),
    "mono":    ("Courier New", 9),
    "big":     ("Courier New", 28, "bold"),
    "status":  ("Courier New", 10, "bold"),
    "small":   ("Courier New", 8),
}

# ============================================================
# LOAD DATA
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _path(*parts):
    return os.path.join(BASE_DIR, "..", *parts)

inventory_df  = pd.read_csv(_path("data", "blood_inventory.csv"))
requests_df   = pd.read_csv(_path("data", "hospital_requests.csv"))
distance_df   = pd.read_csv(_path("output", "distance_matrix.csv"))
log_path      = _path("output", "distribution_log.csv")

inventory_df["expiry_date"] = pd.to_datetime(inventory_df["expiry_date"])
requests_df["request_date"] = pd.to_datetime(requests_df["request_date"])


# ============================================================
# LOGGING
# ============================================================

def log_transaction(result):
    entry = pd.DataFrame([{
        "request_id":     result["request_id"],
        "hospital_id":    result["hospital_id"],
        "blood_type":     result["blood_type"],
        "status":         result["status"],
        "message":        result["message"],
        "units_allocated":result["units_allocated"],
        "details":        str(result["details"]),
    }])
    entry.to_csv(log_path, mode="a", header=False, index=False)


# ============================================================
# HELPER WIDGETS
# ============================================================

def make_card(parent, **kwargs):
    """A styled card frame."""
    defaults = dict(bg=C["panel"], bd=0, highlightthickness=1,
                    highlightbackground=C["border"], highlightcolor=C["accent"])
    defaults.update(kwargs)
    return tk.Frame(parent, **defaults)


def make_label(parent, text, style="label", fg=None, **kwargs):
    bg = kwargs.pop("bg", parent["bg"])
    return tk.Label(parent, text=text,
                    font=FONTS[style],
                    fg=fg or C["text"],
                    bg=bg,
                    **kwargs)


def make_separator(parent, orient="h"):
    f = tk.Frame(parent,
                 bg=C["separator"],
                 height=1 if orient == "h" else None,
                 width=None if orient == "h" else 1)
    return f


def styled_combobox(parent, values, width=22):
    cb = ttk.Combobox(parent, values=values, state="readonly",
                      width=width, font=FONTS["input"])
    cb.configure(foreground=C["entry_fg"])
    return cb


def styled_entry(parent, width=24):
    e = tk.Entry(parent, width=width,
                 font=FONTS["input"],
                 bg=C["entry_bg"],
                 fg=C["entry_fg"],
                 insertbackground=C["accent"],
                 relief="flat",
                 bd=4,
                 highlightthickness=1,
                 highlightbackground=C["border"],
                 highlightcolor=C["accent"])
    return e


def styled_button(parent, text, command, color=None, width=22):
    color = color or C["accent"]
    btn = tk.Button(parent, text=text, command=command,
                    font=FONTS["heading"],
                    bg=color, fg=C["text"],
                    activebackground=C["accent2"],
                    activeforeground=C["text"],
                    relief="flat", bd=0,
                    cursor="hand2",
                    width=width,
                    pady=8)
    btn.bind("<Enter>", lambda e: btn.config(bg=C["accent2"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


# ============================================================
# CONFIGURE TTK STYLES
# ============================================================

def configure_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("Treeview",
                    background=C["panel"],
                    foreground=C["text"],
                    fieldbackground=C["panel"],
                    rowheight=26,
                    font=FONTS["mono"],
                    borderwidth=0)
    style.configure("Treeview.Heading",
                    background=C["header_bg"],
                    foreground=C["accent"],
                    font=FONTS["heading"],
                    relief="flat",
                    borderwidth=0)
    style.map("Treeview",
              background=[("selected", C["table_sel"])],
              foreground=[("selected", C["text"])])
    style.map("Treeview.Heading",
              background=[("active", C["accent"])])

    style.configure("TCombobox",
                    fieldbackground=C["entry_bg"],
                    background=C["entry_bg"],
                    foreground=C["entry_fg"],
                    arrowcolor=C["accent"],
                    bordercolor=C["border"],
                    lightcolor=C["border"],
                    darkcolor=C["border"],
                    insertcolor=C["accent"])
    style.map("TCombobox",
              fieldbackground=[("readonly", C["entry_bg"])],
              foreground=[("readonly", C["entry_fg"])],
              selectbackground=[("readonly", C["accent"])],
              selectforeground=[("readonly", C["text"])])

    style.configure("Vertical.TScrollbar",
                    background=C["panel"],
                    troughcolor=C["bg"],
                    arrowcolor=C["muted"])


# ============================================================
# STAT CARD
# ============================================================

def make_stat_card(parent, title, value, color):
    card = make_card(parent, highlightbackground=color)
    card.pack(side="left", fill="both", expand=True, padx=6, pady=4)

    make_label(card, title, style="small", fg=C["muted"]).pack(
        anchor="w", padx=12, pady=(10, 0))
    make_label(card, value, style="big", fg=color).pack(
        anchor="w", padx=12, pady=(0, 10))
    return card


# ============================================================
# MAIN APP
# ============================================================

class BloodDashboard(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("HEMATIX — Blood Allocation System")
        self.geometry("1280x780")
        self.minsize(1100, 700)
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        configure_styles(self)
        self._build_ui()
        self._load_table()
        self._refresh_stats()

    # ----------------------------------------------------------
    # TOP BAR
    # ----------------------------------------------------------

    def _build_topbar(self, parent):
        bar = tk.Frame(parent, bg=C["panel"], height=56)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        tk.Frame(bar, bg=C["accent"], height=3).pack(fill="x", side="top")

        inner = tk.Frame(bar, bg=C["panel"])
        inner.pack(fill="both", expand=True, padx=20)

        make_label(inner, "◈  HEMATIX", style="title", fg=C["accent"]).pack(
            side="left", pady=8)
        make_label(inner, "BLOOD ALLOCATION MANAGEMENT SYSTEM",
                   style="small", fg=C["muted"]).pack(side="left", padx=16, pady=8)

        dot_frame = tk.Frame(inner, bg=C["panel"])
        dot_frame.pack(side="right", pady=8)
        tk.Canvas(dot_frame, width=10, height=10, bg=C["panel"],
                  highlightthickness=0).pack(side="left")
        make_label(dot_frame, "● LIVE", style="small",
                   fg=C["green"]).pack(side="left")

    # ----------------------------------------------------------
    # BUILD FULL UI
    # ----------------------------------------------------------

    def _build_ui(self):
        self._build_topbar(self)

        content = tk.Frame(self, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=14, pady=(10, 14))

        left  = tk.Frame(content, bg=C["bg"], width=270)
        mid   = tk.Frame(content, bg=C["bg"])
        right = tk.Frame(content, bg=C["bg"], width=430)

        left.pack(side="left",  fill="y",    padx=(0, 8))
        mid.pack( side="left",  fill="both", expand=True, padx=(0, 8))
        right.pack(side="right", fill="y")

        left.pack_propagate(False)
        right.pack_propagate(False)

        self._build_input_panel(left)
        self._build_center_panel(mid)
        self._build_right_panel(right)

    # ----------------------------------------------------------
    # LEFT — INPUT PANEL
    # ----------------------------------------------------------

    def _build_input_panel(self, parent):
        card = make_card(parent)
        card.pack(fill="both", expand=True)

        header = tk.Frame(card, bg=C["accent"], height=36)
        header.pack(fill="x")
        header.pack_propagate(False)
        make_label(header, "  ⊕  NEW REQUEST", style="heading",
                   fg=C["text"], bg=C["accent"]).pack(side="left", padx=8, pady=6)

        body = tk.Frame(card, bg=C["panel"])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── RESULT BOX ──
        make_label(body, "LAST RESULT", style="small", fg=C["muted"]).pack(anchor="w")

        self.result_card = tk.Frame(body, bg=C["entry_bg"],
                                    highlightthickness=2,
                                    highlightbackground=C["border"])
        self.result_card.pack(fill="x", pady=(4, 0))

        self.result_status_var = tk.StringVar(value="── PENDING ──")
        self.result_status_lbl = tk.Label(self.result_card,
                                          textvariable=self.result_status_var,
                                          font=("Courier New", 13, "bold"),
                                          fg=C["muted"],
                                          bg=C["entry_bg"],
                                          anchor="w",
                                          padx=10, pady=8)
        self.result_status_lbl.pack(fill="x")

        self.result_var = tk.StringVar(value="Awaiting submission…")
        self.result_label = tk.Label(self.result_card,
                                     textvariable=self.result_var,
                                     font=FONTS["mono"],
                                     fg=C["muted"],
                                     bg=C["entry_bg"],
                                     wraplength=220,
                                     justify="left",
                                     padx=10, pady=0)
        self.result_label.pack(fill="x", pady=(0, 8))

        make_separator(body).pack(fill="x", pady=12)

        # ── INPUT FIELDS ──
        def field(label_text, widget):
            make_label(body, label_text.upper(), style="small",
                       fg=C["muted"]).pack(anchor="w", pady=(8, 2))
            widget.pack(fill="x", ipady=4)

        hospital_ids = sorted(distance_df["hospital_id"].unique().tolist())
        self.cb_hospital = styled_combobox(body, hospital_ids)
        field("Hospital ID", self.cb_hospital)

        self.cb_blood = styled_combobox(
            body, ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        field("Blood Type", self.cb_blood)

        self.entry_units = styled_entry(body)
        field("Units Required", self.entry_units)

        self.cb_urgency = styled_combobox(
            body, ["Emergency", "High", "Medium", "Low"])
        field("Urgency Level", self.cb_urgency)

        make_separator(body).pack(fill="x", pady=14)

        # ── BUTTONS ──────────────────────────────────────────────────────  ← NEW
        styled_button(body, "▶  SUBMIT REQUEST", self._submit,
                      color=C["accent"]).pack(fill="x")

        # Donate button — outlined style, distinct from Submit              ← NEW
        donate_btn = tk.Button(
            body,
            text="♥  DONATE BLOOD",
            command=lambda: open_donation_portal(self),
            font=FONTS["heading"],
            bg=C["panel"],
            fg=C["accent"],
            activebackground=C["accent"],
            activeforeground=C["text"],
            relief="flat", bd=0,
            cursor="hand2",
            pady=7,
            highlightthickness=1,
            highlightbackground=C["accent"],
            highlightcolor=C["accent2"],
        )
        donate_btn.pack(fill="x", pady=(8, 0))
        donate_btn.bind("<Enter>",
                        lambda e: donate_btn.config(bg=C["accent"], fg=C["text"]))
        donate_btn.bind("<Leave>",
                        lambda e: donate_btn.config(bg=C["panel"], fg=C["accent"]))

    # ----------------------------------------------------------
    # CENTER — STATS + TABLE + CHART
    # ----------------------------------------------------------

    def _build_center_panel(self, parent):
        stat_row = tk.Frame(parent, bg=C["bg"])
        stat_row.pack(fill="x", pady=(0, 8))

        self.stat_total  = tk.StringVar(value="—")
        self.stat_types  = tk.StringVar(value="—")
        self.stat_banks  = tk.StringVar(value="—")
        self.stat_expiry = tk.StringVar(value="—")

        for title, var, color in [
            ("TOTAL UNITS",   self.stat_total,  C["accent"]),
            ("BLOOD TYPES",   self.stat_types,  C["gold"]),
            ("BANKS",         self.stat_banks,  C["green"]),
            ("EXPIRING SOON", self.stat_expiry, C["muted"]),
        ]:
            make_stat_card(stat_row, title, var.get(), color)
        self._stat_cards = (self.stat_total, self.stat_types,
                            self.stat_banks, self.stat_expiry)

        tbl_card = make_card(parent)
        tbl_card.pack(fill="both", expand=True)

        tbl_header = tk.Frame(tbl_card, bg=C["header_bg"], height=36)
        tbl_header.pack(fill="x")
        tbl_header.pack_propagate(False)
        make_label(tbl_header, "  ▤  INVENTORY OVERVIEW", style="heading",
                   fg=C["text"], bg=C["header_bg"]).pack(side="left", padx=8, pady=6)

        filter_row = tk.Frame(tbl_card, bg=C["panel"])
        filter_row.pack(fill="x", padx=12, pady=8)
        make_label(filter_row, "FILTER TYPE:", style="small",
                   fg=C["muted"]).pack(side="left")
        self.cb_filter = styled_combobox(
            filter_row,
            ["All"] + ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            width=10)
        self.cb_filter.set("All")
        self.cb_filter.pack(side="left", padx=8)
        self.cb_filter.bind("<<ComboboxSelected>>", lambda e: self._load_table())

        tbl_wrap = tk.Frame(tbl_card, bg=C["panel"])
        tbl_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = ("bank_id", "blood_type", "units_available", "expiry_date")
        self.table = ttk.Treeview(tbl_wrap, columns=cols, show="headings",
                                   selectmode="browse")

        headers = {
            "bank_id":         ("Bank",           90,  "center"),
            "blood_type":      ("Type",           70,  "center"),
            "units_available": ("Units",          80,  "center"),
            "expiry_date":     ("Expiry",         120, "center"),
        }
        for col, (heading, w, anchor) in headers.items():
            self.table.heading(col, text=heading)
            self.table.column(col, width=w, anchor=anchor, minwidth=50)

        scroll = ttk.Scrollbar(tbl_wrap, orient="vertical",
                               command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.table.tag_configure("odd",  background=C["table_alt"])
        self.table.tag_configure("even", background=C["panel"])

    # ----------------------------------------------------------
    # RIGHT — CHARTS PANEL
    # ----------------------------------------------------------

    def _build_right_panel(self, parent):
        card = make_card(parent)
        card.pack(fill="both", expand=True)

        header = tk.Frame(card, bg=C["header_bg"], height=36)
        header.pack(fill="x")
        header.pack_propagate(False)
        make_label(header, "  ◉  ANALYTICS", style="heading",
                   fg=C["text"], bg=C["header_bg"]).pack(side="left", padx=8, pady=6)

        btn_row = tk.Frame(card, bg=C["panel"])
        btn_row.pack(fill="x", padx=10, pady=8)

        charts = [
            ("Availability", self._chart_availability, C["accent"]),
            ("Demand",       self._chart_demand,        C["gold"]),
            ("Heatmap",      self._chart_heatmap,       C["green"]),
            ("Distribution", self._chart_dist,          C["muted"]),
        ]
        for i, (label, cmd, col) in enumerate(charts):
            b = tk.Button(btn_row, text=label, command=cmd,
                          font=FONTS["small"],
                          bg=col, fg=C["text"],
                          relief="flat", bd=0,
                          padx=6, pady=4,
                          cursor="hand2",
                          activebackground=C["accent2"],
                          activeforeground=C["text"])
            b.grid(row=0, column=i, padx=3)
            b.bind("<Enter>", lambda e, c=col: e.widget.config(bg=C["accent2"]))
            b.bind("<Leave>", lambda e, c=col: e.widget.config(bg=c))

        self.fig = Figure(figsize=(5.8, 5.2), facecolor=C["panel"], tight_layout=True)
        self.ax  = self.fig.add_subplot(111)
        self._style_ax(self.ax)

        self.canvas = FigureCanvasTkAgg(self.fig, master=card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True,
                                          padx=10, pady=(0, 10))
        self._chart_availability()

    # ----------------------------------------------------------
    # STATS REFRESH
    # ----------------------------------------------------------

    def _refresh_stats(self):
        total   = int(inventory_df["units_available"].sum())
        types   = inventory_df["blood_type"].nunique()
        banks   = inventory_df["bank_id"].nunique()
        soon    = int((
            (inventory_df["expiry_date"] - pd.Timestamp.now()).dt.days <= 7
        ).sum())

        self.stat_total.set(str(total))
        self.stat_types.set(str(types))
        self.stat_banks.set(str(banks))
        self.stat_expiry.set(str(soon))

        self._update_stat_labels()

    def _update_stat_labels(self):
        """Walk stat bar and update big-number labels."""
        try:
            stat_row = self._stat_row_ref
        except AttributeError:
            return
        values = [
            self.stat_total.get(),
            self.stat_types.get(),
            self.stat_banks.get(),
            self.stat_expiry.get(),
        ]
        for card, val in zip(stat_row.winfo_children(), values):
            for w in card.winfo_children():
                if w.cget("font") == str(FONTS["big"]):
                    w.config(text=val)

    # ----------------------------------------------------------
    # TABLE LOAD
    # ----------------------------------------------------------

    def _load_table(self, highlight_blood=None, highlight_hospital=None):
        for row in self.table.get_children():
            self.table.delete(row)

        filt = self.cb_filter.get() if hasattr(self, "cb_filter") else "All"
        df = inventory_df.copy()
        if filt != "All":
            df = df[df["blood_type"] == filt]

        for i, (_, row) in enumerate(df.iterrows()):
            tag = "odd" if i % 2 else "even"
            expiry_str = str(row["expiry_date"].date()) if hasattr(
                row["expiry_date"], "date") else str(row["expiry_date"])
            self.table.insert("", "end", tag=tag, values=(
                row["bank_id"],
                row["blood_type"],
                row["units_available"],
                expiry_str,
            ))

    # ----------------------------------------------------------
    # SUBMIT  ← BUG FIX: deduct units from inventory_df in memory
    # ----------------------------------------------------------

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

        # ── FIX: Deduct allocated units from the global inventory_df in memory ──
        for detail in result.get("details", []):
            bank_id     = detail["bank_id"]
            units_taken = detail["units_taken"]
            mask = (
                (inventory_df["bank_id"]    == bank_id) &
                (inventory_df["blood_type"] == blood)
            )
            inventory_df.loc[mask, "units_available"] -= units_taken
            # Safety clamp — never go below zero
            inventory_df.loc[mask, "units_available"] = (
                inventory_df.loc[mask, "units_available"].clip(lower=0)
            )

        # Persist updated inventory to disk
        inventory_df.to_csv(_path("data", "blood_inventory.csv"), index=False)

        # Reload table + stats to reflect deducted values
        self._load_table(highlight_blood=blood, highlight_hospital=hospital)
        self._refresh_stats()
        # Refresh the active chart so it also reflects new numbers
        self._chart_availability()

        # Update result box
        status  = result["status"]
        details = ", ".join(f"{d['bank_id']}→{d['units_taken']}"
                            for d in result["details"]) or "—"
        status_colors = {
            "SUCCESS": C["green"],
            "PARTIAL": C["gold"],
            "FAILED":  C["accent"],
        }
        color = status_colors.get(status, C["muted"])

        self.result_status_var.set(f"[ {status} ]")
        self.result_status_lbl.config(fg=color)
        self.result_var.set(f"{result['message']}\n{details}")
        self.result_label.config(fg=C["muted"])
        self.result_card.config(highlightbackground=color)

    # ----------------------------------------------------------
    # CHART HELPERS
    # ----------------------------------------------------------

    def _style_ax(self, ax):
        ax.set_facecolor(C["panel"])
        ax.tick_params(colors=C["muted"], labelsize=7)
        ax.xaxis.label.set_color(C["muted"])
        ax.yaxis.label.set_color(C["muted"])
        ax.title.set_color(C["text"])
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])

    def _redraw(self):
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self._style_ax(self.ax)
        return self.ax

    def _chart_availability(self):
        ax = self._redraw()
        grouped = inventory_df.groupby("blood_type")["units_available"].sum()
        colors  = [C["accent"] if v == grouped.min()
                   else C["green"] for v in grouped.values]
        grouped.plot(kind="bar", ax=ax, color=colors, edgecolor="none",
                     width=0.65)
        ax.set_title("Blood Availability by Type", fontsize=9)
        ax.set_xlabel("")
        ax.set_ylabel("Units", fontsize=8)
        plt.setp(ax.get_xticklabels(), rotation=0, fontsize=8)
        ax.yaxis.grid(True, color=C["border"], linewidth=0.5)
        ax.set_axisbelow(True)
        self.canvas.draw()

    def _chart_demand(self):
        ax = self._redraw()
        df = requests_df.copy()
        grouped = df.groupby("request_date")["units_required"].sum()
        ax.plot(grouped.index, grouped.values,
                color=C["gold"], linewidth=1.8, marker="o",
                markersize=3, markerfacecolor=C["accent"])
        ax.fill_between(grouped.index, grouped.values,
                        alpha=0.12, color=C["gold"])
        ax.set_title("Demand Over Time", fontsize=9)
        ax.set_ylabel("Units Required", fontsize=8)
        ax.tick_params(axis="x", labelrotation=30, labelsize=7)
        ax.yaxis.grid(True, color=C["border"], linewidth=0.5)
        ax.set_axisbelow(True)
        self.canvas.draw()

    def _chart_heatmap(self):
        ax = self._redraw()
        pivot = inventory_df.pivot_table(
            values="units_available",
            index="bank_id",
            columns="blood_type",
            aggfunc="sum",
            fill_value=0,
        )
        cmap = sns.color_palette(
            [C["panel"], C["border"], C["gold"], C["accent"]], as_cmap=True)
        sns.heatmap(pivot, ax=ax, annot=True, fmt=".0f",
                    cmap="RdYlGn_r",
                    linewidths=0.5,
                    linecolor=C["bg"],
                    annot_kws={"size": 7},
                    cbar_kws={"shrink": 0.7})
        ax.set_title("Availability Heatmap", fontsize=9)
        ax.set_xlabel("Blood Type", fontsize=8)
        ax.set_ylabel("Bank", fontsize=8)
        ax.tick_params(labelsize=7)
        self.canvas.draw()

    def _chart_dist(self):
        ax = self._redraw()
        data = inventory_df["units_available"]
        sns.histplot(data, ax=ax, color=C["accent"],
                     kde=True, bins=15, edgecolor="none",
                     line_kws={"color": C["gold"], "linewidth": 1.5})
        ax.set_title("Unit Distribution", fontsize=9)
        ax.set_xlabel("Units Available", fontsize=8)
        ax.set_ylabel("Frequency", fontsize=8)
        ax.yaxis.grid(True, color=C["border"], linewidth=0.5)
        ax.set_axisbelow(True)
        self.canvas.draw()


# ============================================================
# STAT CARD (patched to use StringVar for dynamic updates)
# ============================================================

def build_stat_section(parent):
    """Build stat cards that can be updated dynamically."""
    row = tk.Frame(parent, bg=C["bg"])

    stat_vars   = {}
    stat_labels = {}

    specs = [
        ("TOTAL UNITS",   "stat_total",  C["accent"]),
        ("BLOOD TYPES",   "stat_types",  C["gold"]),
        ("BANKS",         "stat_banks",  C["green"]),
        ("EXPIRING SOON", "stat_expiry", C["muted"]),
    ]

    for title, key, color in specs:
        card = make_card(row, highlightbackground=color)
        card.pack(side="left", fill="both", expand=True, padx=6, pady=4)

        make_label(card, title, style="small", fg=C["muted"]).pack(
            anchor="w", padx=12, pady=(10, 0))

        var = tk.StringVar(value="—")
        lbl = tk.Label(card, textvariable=var,
                       font=FONTS["big"],
                       fg=color,
                       bg=C["panel"])
        lbl.pack(anchor="w", padx=12, pady=(0, 10))

        stat_vars[key]   = var
        stat_labels[key] = lbl

    return row, stat_vars


# ============================================================
# IMPROVED APP (uses patched stat bar)
# ============================================================

class BloodDashboardV2(BloodDashboard):
    """
    Overrides center panel build to use dynamic stat cards.
    """

    def _build_center_panel(self, parent):
        # Dynamic stat cards
        stat_row, self.stat_vars = build_stat_section(parent)
        stat_row.pack(fill="x", pady=(0, 8))
        self._stat_row_ref = stat_row

        # Keep compat attributes
        self.stat_total  = self.stat_vars["stat_total"]
        self.stat_types  = self.stat_vars["stat_types"]
        self.stat_banks  = self.stat_vars["stat_banks"]
        self.stat_expiry = self.stat_vars["stat_expiry"]

        # Inventory table card
        tbl_card = make_card(parent)
        tbl_card.pack(fill="both", expand=True)

        tbl_header = tk.Frame(tbl_card, bg=C["header_bg"], height=36)
        tbl_header.pack(fill="x")
        tbl_header.pack_propagate(False)
        make_label(tbl_header, "  ▤  INVENTORY OVERVIEW", style="heading",
                   fg=C["text"], bg=C["header_bg"]).pack(side="left", padx=8, pady=6)

        filter_row = tk.Frame(tbl_card, bg=C["panel"])
        filter_row.pack(fill="x", padx=12, pady=8)
        make_label(filter_row, "FILTER TYPE:", style="small",
                   fg=C["muted"]).pack(side="left")
        self.cb_filter = styled_combobox(
            filter_row,
            ["All"] + ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            width=10)
        self.cb_filter.set("All")
        self.cb_filter.pack(side="left", padx=8)
        self.cb_filter.bind("<<ComboboxSelected>>", lambda e: self._load_table())

        tbl_wrap = tk.Frame(tbl_card, bg=C["panel"])
        tbl_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = ("bank_id", "blood_type", "units_available", "expiry_date")
        self.table = ttk.Treeview(tbl_wrap, columns=cols, show="headings",
                                   selectmode="browse")
        headers = {
            "bank_id":         ("Bank",    90,  "center"),
            "blood_type":      ("Type",    70,  "center"),
            "units_available": ("Units",   80,  "center"),
            "expiry_date":     ("Expiry",  130, "center"),
        }
        for col, (heading, w, anchor) in headers.items():
            self.table.heading(col, text=heading)
            self.table.column(col, width=w, anchor=anchor, minwidth=50)

        scroll = ttk.Scrollbar(tbl_wrap, orient="vertical",
                               command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.table.tag_configure("odd",  background=C["table_alt"])
        self.table.tag_configure("even", background=C["panel"])

    def _update_stat_labels(self):
        """Update dynamic stat StringVars."""
        self.stat_total.set(
            str(int(inventory_df["units_available"].sum())))
        self.stat_types.set(
            str(inventory_df["blood_type"].nunique()))
        self.stat_banks.set(
            str(inventory_df["bank_id"].nunique()))
        soon = int((
            (inventory_df["expiry_date"] - pd.Timestamp.now()).dt.days <= 7
        ).sum())
        self.stat_expiry.set(str(soon))


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app = BloodDashboardV2()
    app.mainloop()