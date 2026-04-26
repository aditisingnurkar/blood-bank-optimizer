# ==============================
# BLOOD ALLOCATION DASHBOARD
# ==============================

import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import os
import matplotlib.pyplot as plt
import seaborn as sns

from allocation_engine import allocation_pipeline
from date_preprocessing import HospitalRequest   # ✅ ADDED

# ==============================
# LOAD DATA
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

inventory_path = os.path.join(BASE_DIR, "..", "data", "blood_inventory.csv")
requests_path = os.path.join(BASE_DIR, "..", "data", "hospital_requests.csv")
distance_path = os.path.join(BASE_DIR, "..", "output", "distance_matrix.csv")
log_path = os.path.join(BASE_DIR, "..", "output", "distribution_log.csv")  # ✅ ADDED

inventory_df = pd.read_csv(inventory_path)
requests_df = pd.read_csv(requests_path)
distance_df = pd.read_csv(distance_path)

# Convert dates
inventory_df["expiry_date"] = pd.to_datetime(inventory_df["expiry_date"])
requests_df["request_date"] = pd.to_datetime(requests_df["request_date"])

# ==============================
# LOGGING FUNCTION ✅ ADDED
# ==============================

def log_transaction(result, path):
    log_entry = pd.DataFrame([{
        "request_id": result["request_id"],
        "hospital_id": result["hospital_id"],
        "blood_type": result["blood_type"],
        "status": result["status"],
        "message": result["message"],
        "units_allocated": result["units_allocated"],
        "details": str(result["details"])
    }])

    log_entry.to_csv(path, mode='a', header=False, index=False)


# ==============================
# MAIN WINDOW
# ==============================

root = tk.Tk()
root.title("Blood Allocation Dashboard")
root.geometry("1100x700")

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
# INPUT PANEL
# ==============================

tk.Label(left_frame, text="Request Panel", font=("Arial", 14, "bold")).pack(pady=10)

tk.Label(left_frame, text="Hospital ID").pack()
hospital_ids = sorted(distance_df["hospital_id"].unique().tolist())
entry_hospital = ttk.Combobox(left_frame, values=hospital_ids, state="readonly")
entry_hospital.pack(pady=5)

tk.Label(left_frame, text="Blood Type").pack()
entry_blood = ttk.Combobox(
    left_frame,
    values=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    state="readonly"
)
entry_blood.pack(pady=5)

tk.Label(left_frame, text="Units Required").pack()
entry_units = tk.Entry(left_frame)
entry_units.pack(pady=5)

tk.Label(left_frame, text="Urgency").pack()
entry_urgency = ttk.Combobox(
    left_frame,
    values=["Emergency", "High", "Medium", "Low"],
    state="readonly"
)
entry_urgency.pack(pady=5)

# ==============================
# TABLE
# ==============================

tk.Label(right_frame, text="Blood Availability", font=("Arial", 14, "bold")).pack(pady=10)

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
# LOAD INITIAL DATA
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
# UPDATE TABLE
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
# SUBMIT FUNCTION (FIXED)
# ==============================

def submit():
    try:
        blood = entry_blood.get()
        hospital = entry_hospital.get()
        urgency = entry_urgency.get()

        # handle units safely
        try:
            units = int(entry_units.get())
        except:
            messagebox.showerror("Error", "Enter valid number of units")
            return

        # ✅ validation
        if not blood or not hospital or not urgency:
            messagebox.showerror("Error", "Please fill all fields")
            return

        if units <= 0:
            messagebox.showerror("Error", "Units must be positive")
            return

        update_table(blood, hospital)

        # ✅ FIXED request object
        req = HospitalRequest(
            request_id="R_NEW",
            hospital_id=hospital,
            blood_type=blood,
            units_required=units,
            urgency=urgency
        )

        result = allocation_pipeline(inventory_df, [req], distance_df)[0]

        # ✅ logging added
        log_transaction(result, log_path)

        # ✅ improved output
        details_text = ", ".join(
            [f"{d['bank_id']}→{d['units_taken']}" for d in result["details"]]
        )

        result_label.config(
            text=f"{result['status']} | {result['message']} | {details_text}"
        )

        # save updated inventory
        inventory_df.to_csv(inventory_path, index=False)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ==============================
# BUTTON
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

styled_button(left_frame, "Submit Request", submit, "#27ae60").pack(pady=15)

# ==============================
# GRAPHS
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

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

styled_button(btn_frame, "Availability", plot_availability, "#3498db").grid(row=0, column=0, padx=5)
styled_button(btn_frame, "Demand", plot_demand, "#9b59b6").grid(row=0, column=1, padx=5)
styled_button(btn_frame, "Heatmap", plot_heatmap, "#e67e22").grid(row=0, column=2, padx=5)
styled_button(btn_frame, "Distribution", plot_distribution, "#e74c3c").grid(row=0, column=3, padx=5)

# ==============================
# START
# ==============================

load_all_data()
root.mainloop()
