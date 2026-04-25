# ==============================
# BLOOD ALLOCATION DASHBOARD (FINAL CLEAN VERSION)
# ==============================

import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import os
import matplotlib.pyplot as plt
import seaborn as sns

from allocation_engine import allocation_pipeline

# ==============================
# LOAD DATA
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

inventory_path = os.path.join(BASE_DIR, "..", "data", "blood_inventory.csv")
requests_path = os.path.join(BASE_DIR, "..", "data", "hospital_requests.csv")
distance_path = os.path.join(BASE_DIR, "..", "output", "distance_matrix.csv")

inventory_df = pd.read_csv(inventory_path)
requests_df = pd.read_csv(requests_path)
distance_df = pd.read_csv(distance_path)

# Convert dates
inventory_df["expiry_date"] = pd.to_datetime(inventory_df["expiry_date"])
requests_df["request_date"] = pd.to_datetime(requests_df["request_date"])

# ==============================
# MAIN WINDOW
# ==============================

root = tk.Tk()
root.title("Blood Allocation Dashboard")
root.geometry("1100x700")

# ==============================
# MAIN FRAME
# ==============================

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

# LEFT PANEL
left_frame = tk.Frame(main_frame, bd=2, relief="groove", width=300)
left_frame.pack(side="left", fill="y", padx=10, pady=10)
left_frame.pack_propagate(False)

# RIGHT PANEL
right_frame = tk.Frame(main_frame, bd=2, relief="groove")
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# ==============================
# LEFT — REQUEST PANEL
# ==============================

tk.Label(left_frame, text="Request Panel",
         font=("Arial", 14, "bold")).pack(pady=10)

# Hospital dropdown
tk.Label(left_frame, text="Hospital ID").pack()
hospital_ids = sorted(distance_df["hospital_id"].unique().tolist())
entry_hospital = ttk.Combobox(left_frame, values=hospital_ids, state="readonly")
entry_hospital.pack(pady=5)

# Blood type dropdown
tk.Label(left_frame, text="Blood Type").pack()
entry_blood = ttk.Combobox(
    left_frame,
    values=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    state="readonly"
)
entry_blood.pack(pady=5)

# Units
tk.Label(left_frame, text="Units Required").pack()
entry_units = tk.Entry(left_frame)
entry_units.pack(pady=5)

# Urgency
tk.Label(left_frame, text="Urgency").pack()
entry_urgency = ttk.Combobox(
    left_frame,
    values=["Emergency", "High", "Medium", "Low"],
    state="readonly"
)
entry_urgency.pack(pady=5)

# ==============================
# TABLE (RIGHT)
# ==============================

tk.Label(right_frame, text="Blood Availability",
         font=("Arial", 14, "bold")).pack(pady=10)

columns = ("Bank ID", "Units Available", "Distance (km)")
table = ttk.Treeview(right_frame, columns=columns, show="headings")

for col in columns:
    table.heading(col, text=col)
    table.column(col, width=150, anchor="center")

table.pack(fill="both", expand=True, padx=10, pady=10)

# ==============================
# RESULT LABEL
# ==============================

result_label = tk.Label(root, text="", fg="blue", font=("Arial", 11))
result_label.pack(pady=5)

# ==============================
# LOAD INITIAL DATA INTO TABLE
# ==============================

def load_all_data():
    for row in table.get_children():
        table.delete(row)

    for _, row in inventory_df.iterrows():
        table.insert("", "end", values=(
            row["bank_id"],
            row["units_available"],
            "-"
        ))

# ==============================
# UPDATE TABLE (FILTER + DISTANCE)
# ==============================

def update_table(blood_type, hospital_id):
    for row in table.get_children():
        table.delete(row)

    filtered = inventory_df[inventory_df["blood_type"] == blood_type]

    if filtered.empty:
        result_label.config(text="No stock available")
        return

    for _, row in filtered.iterrows():
        dist = distance_df[
            (distance_df["bank_id"] == row["bank_id"]) &
            (distance_df["hospital_id"] == hospital_id)
        ]

        distance = dist["distance_km"].values[0] if not dist.empty else "N/A"

        table.insert("", "end", values=(
            row["bank_id"],
            row["units_available"],
            distance
        ))

# ==============================
# SUBMIT FUNCTION
# ==============================

def submit():
    try:
        blood = entry_blood.get()
        hospital = entry_hospital.get()
        units = int(entry_units.get())
        urgency = entry_urgency.get()

        if not blood or not hospital:
            messagebox.showerror("Error", "Please fill all fields")
            return

        update_table(blood, hospital)

        req = type("Req", (), {
            "request_id": "R1",
            "hospital_id": hospital,
            "blood_type": blood,
            "units_required": units,
            "get_priority": lambda self: urgency
        })()

        result = allocation_pipeline(inventory_df, [req], distance_df)[0]

        result_label.config(
            text=f"{result['status']} - {result['message']}"
        )

        inventory_df.to_csv(inventory_path, index=False)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ==============================
# BUTTON STYLE
# ==============================

def styled_button(parent, text, command, color):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg="white",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=5
    )

# Submit button
styled_button(left_frame, "Submit Request", submit, "#27ae60").pack(pady=15)

# ==============================
# GRAPH FUNCTIONS (POPUP)
# ==============================

def plot_availability():
    grouped = inventory_df.groupby("blood_type")["units_available"].sum()
    plt.figure()
    grouped.plot(kind="bar")
    plt.title("Blood Availability")
    plt.show()

def plot_demand():
    grouped = requests_df.groupby("blood_type")["units_required"].sum()
    plt.figure()
    grouped.plot(kind="line")
    plt.title("Demand")
    plt.show()

def plot_heatmap():
    pivot = inventory_df.pivot_table(
        values="units_available",
        index="bank_id",
        columns="blood_type",
        aggfunc="sum"
    )
    plt.figure()
    sns.heatmap(pivot)
    plt.title("Heatmap")
    plt.show()

def plot_distribution():
    plt.figure()
    inventory_df["units_available"].plot(kind="hist")
    plt.title("Distribution")
    plt.show()

# ==============================
# GRAPH BUTTONS
# ==============================

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

styled_button(btn_frame, "Availability", plot_availability, "#3498db").grid(row=0, column=0, padx=5)
styled_button(btn_frame, "Demand", plot_demand, "#9b59b6").grid(row=0, column=1, padx=5)
styled_button(btn_frame, "Heatmap", plot_heatmap, "#e67e22").grid(row=0, column=2, padx=5)
styled_button(btn_frame, "Distribution", plot_distribution, "#e74c3c").grid(row=0, column=3, padx=5)

# ==============================
# INITIAL LOAD
# ==============================

load_all_data()

# ==============================
# RUN
# ==============================

root.mainloop()