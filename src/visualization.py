# ==============================
# VISUALIZATION MODULE (Day 4)
# ==============================

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# ==============================
# Matplotlib — Basic Graphs
# ==============================

def plot_blood_availability(inventory_df):
    grouped = inventory_df.groupby("blood_type")["units_available"].sum()

    plt.figure()
    grouped.plot(kind='bar')
    plt.title("Blood Availability by Type")
    plt.xlabel("Blood Type")
    plt.ylabel("Units Available")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()


def plot_demand_over_time(requests_df):
    df = requests_df.copy()
    df["request_date"] = pd.to_datetime(df["request_date"])

    grouped = df.groupby("request_date")["units_required"].sum()

    plt.figure()
    grouped.plot()
    plt.title("Demand Over Time")
    plt.xlabel("Date")
    plt.ylabel("Units Required")
    plt.tight_layout()
    plt.show()


# ==============================
# Seaborn — Advanced Graphs
# ==============================

def plot_shortage_heatmap(inventory_df):
    pivot = inventory_df.pivot_table(
        values="units_available",
        index="bank_id",
        columns="blood_type",
        aggfunc="sum"
    )

    plt.figure()
    sns.heatmap(pivot, annot=True, fmt=".0f")
    plt.title("Blood Availability Heatmap")
    plt.tight_layout()
    plt.show()


def plot_distribution(inventory_df):
    plt.figure()
    sns.histplot(inventory_df["units_available"], kde=True)
    plt.title("Distribution of Blood Units")
    plt.tight_layout()
    plt.show()