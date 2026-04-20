import pandas as pd
import math
import os

# ==============================
# Person 1: Load + Validate Inventory
# ==============================

def load_inventory():
    df = pd.read_csv("data/blood_inventory.csv")

    valid_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

    assert (df["units_available"] >= 0).all(), "Negative units found"
    assert df["blood_type"].isin(valid_types).all(), "Invalid blood type found"

    return df


# ==============================
# Person 2: Load + Validate Requests
# ==============================

def load_requests():
    df = pd.read_csv("data/hospital_requests.csv")

    valid_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    valid_urgency = ["High", "Medium", "Low"]

    assert (df["units_required"] > 0).all(), "Units must be greater than 0"
    assert df["blood_type"].isin(valid_types).all(), "Invalid blood type found"
    assert df["urgency_level"].isin(valid_urgency).all(), "Invalid urgency level"

    return df


# ==============================
# Haversine Distance Function
# ==============================

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ==============================
# Load Data
# ==============================

banks = pd.read_csv("data/blood_banks.csv")
hospitals = pd.read_csv("data/hospitals.csv")

inventory = load_inventory()   # Person 1
requests = load_requests()     # Person 2


# ==============================
# Person 4: Shared IDs
# ==============================

bank_ids = banks["bank_id"].unique().tolist()
hospital_ids = hospitals["hospital_id"].unique().tolist()


# ==============================
# Data Preprocessing (Person 2)
# ==============================

banks = banks.drop_duplicates().dropna()
hospitals = hospitals.drop_duplicates().dropna()

banks["lat"] = banks["lat"].astype(float)
banks["lon"] = banks["lon"].astype(float)

hospitals["lat"] = hospitals["lat"].astype(float)
hospitals["lon"] = hospitals["lon"].astype(float)


# ==============================
# Person 3: Distance Matrix
# ==============================

result = []

for _, b in banks.iterrows():
    for _, h in hospitals.iterrows():
        distance = calculate_distance(b["lat"], b["lon"], h["lat"], h["lon"])
        time = distance * 2

        result.append({
            "bank_id": b["bank_id"],
            "hospital_id": h["hospital_id"],
            "distance_km": round(distance, 2),
            "estimated_time_min": round(time, 2)
        })

df = pd.DataFrame(result)


# ==============================
# Validation (Distance Matrix)
# ==============================

assert df.isnull().sum().sum() == 0, "Missing values found"
assert (df["distance_km"] >= 0).all(), "Negative distance found"
assert (df["estimated_time_min"] >= 0).all(), "Negative time found"
assert df.duplicated().sum() == 0, "Duplicate rows found"


# ==============================
# Person 4: File Handling Functions
# ==============================

def read_csv_file(path):
    return pd.read_csv(path)

def write_csv_file(dataframe, path):
    dataframe.to_csv(path, index=False)

def append_csv_file(dataframe, path):
    dataframe.to_csv(path, mode='a', header=False, index=False)


# ==============================
# Person 4: Cross-file Validation
# ==============================

def validate_ids():
    inventory_bank_ids = set(inventory["bank_id"])
    request_hospital_ids = set(requests["hospital_id"])

    assert inventory_bank_ids.issubset(set(bank_ids)), "Inventory bank IDs mismatch"
    assert request_hospital_ids.issubset(set(hospital_ids)), "Request hospital IDs mismatch"

    print("All IDs are consistent across files.")


validate_ids()


# ==============================
# Person 4: Create Log File
# ==============================

log_path = "output/distribution_log.csv"

if not os.path.exists(log_path):
    log_df = pd.DataFrame(columns=[
        "bank_id", "hospital_id", "blood_type",
        "units_sent", "request_id", "status"
    ])
    write_csv_file(log_df, log_path)


# ==============================
# Save Distance Matrix
# ==============================

os.makedirs("output", exist_ok=True)
write_csv_file(df, "output/distance_matrix.csv")

print("Distance matrix generated successfully.")