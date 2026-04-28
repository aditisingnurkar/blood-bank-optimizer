import pandas as pd #for data handling
from functools import reduce #functional programming , like sum of units
from abc import ABC, abstractmethod #oops


#used for data typw conversion , the date of type string is converted to datetime format, used for further comparisons
def clean_inventory(df):
    df["collection_date"] = pd.to_datetime(df["collection_date"])
    df["expiry_date"] = pd.to_datetime(df["expiry_date"])

    df = df.dropna()  #data cleaning , used to remove the incomplete rows
    df = df.sort_values(by="expiry_date")

    return df


#same as above but for request dates 
def clean_requests(df):
    df["request_date"] = pd.to_datetime(df["request_date"])

    df = df.dropna() #removes incomplete row 
    df = df.sort_values(by="request_date")

    return df


#represents 1 blood bag
class BloodUnit:
    def __init__(self, blood_type, units, expiry_date):
        self.blood_type = blood_type
        self.units = units
        self.expiry_date = expiry_date

    def is_available(self):      #check the availability of the blood bags 
        return self.units > 0

    def __repr__(self):
        return f"{self.blood_type} | Units: {self.units}"

#represnts a blood storage system to manage and organise all blood units in a structured system
class BloodBank:
    def __init__(self, bank_id):
        self.bank_id = bank_id
        self.inventory = []   #stores a list of BloodUnit objects

    def add_unit(self, blood_unit):
        self.inventory.append(blood_unit)

    def get_units_by_type(self, blood_type):
        return [u for u in self.inventory if u.blood_type == blood_type]


#abstract base class with an abstract method 
#get_priority(), ensuring that all subclasses 
#provide their own implementation of priority logic while hiding internal details

class BaseRequest(ABC):
    def __init__(self, request_id, hospital_id, blood_type, units_required):
        self.request_id = request_id
        self.hospital_id = hospital_id
        self.blood_type = blood_type
        self.units_required = units_required

    @abstractmethod
    def get_priority(self):
        pass


class HospitalRequest(BaseRequest):  #child of BaseRequest class
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



#handeles cases with high priority
class EmergencyRequest(HospitalRequest):  #child of HospitalRequest , multi-level inheritance 
    def __init__(self, request_id, hospital_id, blood_type, units_required):
        super().__init__(request_id, hospital_id, blood_type, units_required, "High")

    def get_priority(self):
        return "Emergency"


#returns the no of units for a particular blood type
def filter_by_blood_type(inventory, blood_type):
    return list(filter(lambda x: x["blood_type"] == blood_type, inventory))

#extracts only the numerical values needed for calc , units returned 
def map_to_units(inventory):
    return list(map(lambda x: x["units_available"], inventory))

#total available units 
def total_units(units_list):
    return reduce(lambda x, y: x + y, units_list, 0)

#datetime comparision , its easy here cause we converted the string type date to datetime datatype in the conversion method(clean_inventory)

def check_expiry(row):
    return row["expiry_date"] > pd.Timestamp.now()

#read data, clean it, calculate total units, convert each row into objects, store them in a blood bank, and then process requests with priority
if __name__ == "__main__":
    # load data
    inventory_df = pd.read_csv("data/blood_inventory.csv")
    requests_df = pd.read_csv("data/hospital_requests.csv")

    # clean data
    inventory_df = clean_inventory(inventory_df)
    requests_df = clean_requests(requests_df)

    print("Data cleaned successfully")

#dataframes converted to list of dictionary , cause functional programming works better on list/dicts
    
    inventory_list = inventory_df.to_dict("records")

    filtered = filter_by_blood_type(inventory_list, "A+")
    units = map_to_units(filtered)
    total = total_units(units)

    print("Total A+ units:", total)

    
    bank = BloodBank("B1")

    for _, row in inventory_df.iterrows():
        unit = BloodUnit(row["blood_type"], row["units_available"], row["expiry_date"])
        bank.add_unit(unit)

    print("Units in Bank B1:", bank.inventory)

    
    requests_list = [
        HospitalRequest("R1", "H1", "A+", 5, "Medium"),
        EmergencyRequest("R2", "H2", "O+", 3)
    ]

    for r in requests_list:
        print(r.request_id, "Priority:", r.get_priority())
