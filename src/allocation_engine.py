# ==============================
# DAY 3 — ALLOCATION ENGINE
# ==============================

import pandas as pd


# ==============================
# Person 1 — Matching Logic
# ==============================

def match_blood(inventory, blood_type):
    """
    Filter inventory by required blood type
    """
    return list(filter(lambda x: x["blood_type"] == blood_type, inventory))


# ==============================
# Person 3 — Expiry Logic
# ==============================

def filter_valid_units(inventory):
    """
    Remove expired blood units
    """
    return list(filter(lambda x: x["expiry_date"] > pd.Timestamp.now(), inventory))


# ==============================
# Person 2 — Sorting Logic
# ==============================

def urgency_rank(level):
    """
    Convert urgency to numeric priority
    """
    ranks = {"Emergency": 4, "High": 3, "Medium": 2, "Low": 1}
    return ranks.get(level, 0)


def sort_requests(requests):
    """
    Sort requests by urgency (highest first)
    """
    return sorted(
        requests,
        key=lambda r: urgency_rank(r.get_priority()),
        reverse=True
    )


def sort_inventory(inventory):
    """
    Sort inventory by:
    1. Distance (nearest first)
    2. Expiry (earliest first)
    """
    return sorted(
        inventory,
        key=lambda x: (
            x.get("distance_km", float("inf")),  # fallback if missing
            x["expiry_date"]
        )
    )


# ==============================
# Person 4 — Allocation Logic
# ==============================

def allocate_blood(request, inventory):
    """
    Allocate blood units to a request
    Handles:
    - Full allocation
    - Partial allocation
    - No stock
    """
    required = request.units_required
    allocated = 0
    allocation_details = []

    for item in inventory:
        if required <= 0:
            break

        available = item["units_available"]

        if available <= 0:
            continue

        used = min(available, required)

        # Update inventory
        item["units_available"] -= used

        required -= used
        allocated += used

        allocation_details.append({
            "bank_id": item["bank_id"],
            "units_taken": used
        })

    # Return status
    if allocated == 0:
        return ("FAILED", "No stock available", 0, allocation_details)

    elif required > 0:
        return ("PARTIAL", f"Only {allocated} units allocated", allocated, allocation_details)

    else:
        return ("SUCCESS", "Request fulfilled", allocated, allocation_details)


# ==============================
# Integration — FULL PIPELINE
# ==============================

def allocation_pipeline(inventory_df, requests_list, distance_df):
    """
    Complete allocation pipeline:
    1. Match blood type
    2. Remove expired
    3. Attach distance
    4. Sort inventory
    5. Allocate blood
    """

    # Convert DataFrame → list of dicts
    inventory = inventory_df.to_dict("records")
    distance_map = distance_df.to_dict("records")

    results = []

    # Sort requests by urgency
    sorted_requests = sort_requests(requests_list)

    for req in sorted_requests:

        # Step 1: Match blood type
        matched = match_blood(inventory, req.blood_type)

        # Step 2: Remove expired units
        valid = filter_valid_units(matched)

        # Step 3: Attach distance from matrix
        for item in valid:
            for d in distance_map:
                if d["bank_id"] == item["bank_id"] and d["hospital_id"] == req.hospital_id:
                    item["distance_km"] = d["distance_km"]

        # Step 4: Sort inventory
        sorted_inventory = sort_inventory(valid)

        # Step 5: Allocate blood
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