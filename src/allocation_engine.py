import pandas as pd

# Filtering Inventory by required blood type
def match_blood(inventory, blood_type):
    return list(filter(lambda x: x["blood_type"] == blood_type, inventory))


#Filtering expired blood units
def filter_valid_units(inventory):
    return list(filter(lambda x: x["expiry_date"] > pd.Timestamp.now(), inventory))


# Sorting Logic (assigning numbers to urgency levels for sorting)
def urgency_rank(level):
    ranks = {"Emergency": 4, "High": 3, "Medium": 2, "Low": 1}
    return ranks.get(level, 0)

# Sorting requests by urgency
def sort_requests(requests):
    return sorted(
        requests,
        key=lambda r: urgency_rank(r.get_priority()),
        reverse=True
    )

# Sorting inventory by distance and expiry
def sort_inventory(inventory):
    return sorted(
        inventory,
        key=lambda x: (
            x.get("distance_km", float("inf")),  # fallback if missing
            x["expiry_date"]
        )
    )


# Allocation Logic (full, partial and no stock allocation)
def allocate_blood(request, inventory):
    required = request.units_required
    allocated = 0
    allocation_details = []

    #inventory stores list of banks with available blood types and number of units
    for item in inventory:       
        if required <= 0:
            break

        available = item["units_available"]

        if available <= 0:
            continue

        #cannot allocate more than required or available
        used = min(available, required)

        # Update inventory
        item["units_available"] -= used

        required -= used
        allocated += used

        allocation_details.append({
            "bank_id": item["bank_id"],
            "units_taken": used
        })

    if allocated == 0:
        return ("FAILED", "No stock available", 0, allocation_details)

    elif required > 0:
        return ("PARTIAL", f"Only {allocated} units allocated", allocated, allocation_details)

    else:
        return ("SUCCESS", "Request fulfilled", allocated, allocation_details)


# Full Integration

def allocation_pipeline(inventory_df, requests_list, distance_df):

    # Convert expiry_date to datetime object for filtering
    inventory_df["expiry_date"] = pd.to_datetime(inventory_df["expiry_date"])

    # Convert DataFrame to list of dicts
    inventory = inventory_df.to_dict("records")
    distance_map = distance_df.to_dict("records")

    results = []

    # Sort requests by urgency
    sorted_requests = sort_requests(requests_list)

    for req in sorted_requests:

        # Match blood type
        matched = match_blood(inventory, req.blood_type)

        # Remove expired units
        valid = filter_valid_units(matched)

        # Attach distance from matrix
        for item in valid:
            for d in distance_map:
                if d["bank_id"] == item["bank_id"] and d["hospital_id"] == req.hospital_id:
                    item["distance_km"] = d["distance_km"]

        # Sort inventory
        sorted_inventory = sort_inventory(valid)

        # Allocate blood
        status, message, units, details = allocate_blood(req, sorted_inventory)

        # Store result
        results.append({
            "request_id": req.request_id,
            "hospital_id": req.hospital_id,
            "blood_type": req.blood_type,
            "status": status,
            "message": message,
            "units_allocated": units,
            "details": details
        })

    return results