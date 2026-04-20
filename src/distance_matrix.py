import pandas as pd
import math
import os

# Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# Load data
banks = pd.read_csv("data/blood_banks.csv")
hospitals = pd.read_csv("data/hospitals.csv")

# Data cleaning
banks = banks.drop_duplicates().dropna()
hospitals = hospitals.drop_duplicates().dropna()

banks["lat"] = banks["lat"].astype(float)
banks["lon"] = banks["lon"].astype(float)

hospitals["lat"] = hospitals["lat"].astype(float)
hospitals["lon"] = hospitals["lon"].astype(float)

# Distance matrix generation
result = []

for _, b in banks.iterrows():
    for _, h in hospitals.iterrows():
        distance = calculate_distance(b["lat"], b["lon"], h["lat"], h["lon"])
        time = distance * 2  # simple assumption

        result.append({
            "bank_id": b["bank_id"],
            "hospital_id": h["hospital_id"],
            "distance_km": round(distance, 2),
            "estimated_time_min": round(time, 2)
        })

df = pd.DataFrame(result)

# Validation
assert df.isnull().sum().sum() == 0, "Missing values found"
assert (df["distance_km"] >= 0).all(), "Negative distance found"
assert (df["estimated_time_min"] >= 0).all(), "Negative time found"
assert df.duplicated().sum() == 0, "Duplicate rows found"

# Save
os.makedirs("output", exist_ok=True)
df.to_csv("output/distance_matrix.csv", index=False)

print("Distance matrix generated successfully.")