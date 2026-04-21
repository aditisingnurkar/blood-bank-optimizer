import pandas as pd
from functools import reduce
from abc import ABC, abstractmethod

# ==============================
# Person 1: Data Cleaning Layer
# ==============================

def clean_inventory(df):
    df["collection_date"] = pd.to_datetime(df["collection_date"])
    df["expiry_date"] = pd.to_datetime(df["expiry_date"])

    df = df.dropna()
    df = df.sort_values(by="expiry_date")

    return df


def clean_requests(df):
    df["request_date"] = pd.to_datetime(df["request_date"])

    df = df.dropna()
    df = df.sort_values(by="request_date")

    return df


# ==============================
# Person 2: OOP Core (Part 1)
# ==============================

class BloodUnit:
    def __init__(self, blood_type, units, expiry_date):
        self.blood_type = blood_type
        self.units = units
        self.expiry_date = expiry_date

    def is_available(self):
        return self.units > 0

    def __repr__(self):
        return f"{self.blood_type} | Units: {self.units}"


class BloodBank:
    def __init__(self, bank_id):
        self.bank_id = bank_id
        self.inventory = []

    def add_unit(self, blood_unit):
        self.inventory.append(blood_unit)

    def get_units_by_type(self, blood_type):
        return [u for u in self.inventory if u.blood_type == blood_type]


# ==============================
# Abstraction: Base Request
# ==============================

class BaseRequest(ABC):
    def __init__(self, request_id, hospital_id, blood_type, units_required):
        self.request_id = request_id
        self.hospital_id = hospital_id
        self.blood_type = blood_type
        self.units_required = units_required

    @abstractmethod
    def get_priority(self):
        pass


# ==============================
# Person 3: OOP Core (Part 2)
# ==============================

class HospitalRequest(BaseRequest):
    def __init__(self, request_id, hospital_id, blood_type, units_required, urgency):
        super().__init__(request_id, hospital_id, blood_type, units_required)
        self.urgency = urgency
        self.validate()

    def validate(self):
        assert self.units_required > 0, "Invalid units requested"

    def get_priority(self):
        return self.urgency

    def __repr__(self):
        return f"{self.request_id} | {self.blood_type} | {self.units_required} units"


class EmergencyRequest(HospitalRequest):
    def __init__(self, request_id, hospital_id, blood_type, units_required):
        super().__init__(request_id, hospital_id, blood_type, units_required, "High")

    def get_priority(self):
        return "Emergency"


# ==============================
# Person 4: Functional Programming
# ==============================

def filter_by_blood_type(inventory, blood_type):
    return list(filter(lambda x: x["blood_type"] == blood_type, inventory))


def map_to_units(inventory):
    return list(map(lambda x: x["units_available"], inventory))


def total_units(units_list):
    return reduce(lambda x, y: x + y, units_list, 0)


# ==============================
# Helper Functions
# ==============================

def check_expiry(row):
    return row["expiry_date"] > pd.Timestamp.now()


def urgency_rank(level):
    ranks = {"High": 3, "Medium": 2, "Low": 1}
    return ranks.get(level, 0)


# ==============================
# MAIN EXECUTION (TESTING)
# ==============================

if __name__ == "__main__":
    # Load data
    inventory_df = pd.read_csv("data/blood_inventory.csv")
    requests_df = pd.read_csv("data/hospital_requests.csv")

    # Clean data
    inventory_df = clean_inventory(inventory_df)
    requests_df = clean_requests(requests_df)

    print("Data cleaned successfully")

    # Functional programming demo
    inventory_list = inventory_df.to_dict("records")

    filtered = filter_by_blood_type(inventory_list, "A+")
    units = map_to_units(filtered)
    total = total_units(units)

    print("Total A+ units:", total)

    # OOP demo (Person 2)
    bank = BloodBank("B1")

    for _, row in inventory_df.iterrows():
        unit = BloodUnit(row["blood_type"], row["units_available"], row["expiry_date"])
        bank.add_unit(unit)

    print("Units in Bank B1:", bank.inventory)

    # OOP + Polymorphism demo (Person 3)
    requests_list = [
        HospitalRequest("R1", "H1", "A+", 5, "Medium"),
        EmergencyRequest("R2", "H2", "O+", 3)
    ]

    for r in requests_list:
        print(r.request_id, "Priority:", r.get_priority())