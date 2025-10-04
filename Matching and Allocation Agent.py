import datetime
import random

# --- Member 1: Data & Charity Profiles ---

def create_mock_data(today):
    """
    Collects/creates mock datasets for donations and defines charity needs profiles.
    (Schema documentation is integrated via comments and data structure definition)
    """
    # Define available items
    items = ["Milk", "Bread", "Canned Soup", "Apples", "Pasta", "Flour", "Rice", "Yogurt"]

    # Generate mock donation data (items, quantity, expiry)
    donations = []
    for i in range(1, 16):
        item_name = random.choice(items)
        days_to_expiry = random.randint(1, 30)
        expiry_date = today + datetime.timedelta(days=days_to_expiry)

        donation = {
            "id": f"D{i:03}",
            "item": item_name,
            "quantity": random.randint(10, 100),
            "expiry_date": expiry_date,
            "is_allocated": False # Flag for allocation
        }
        donations.append(donation)

    # Define charity needs profiles (what items they accept, storage, capacity)
    charity_profiles = [
        {
            "id": "C001",
            "name": "Central Kitchen",
            "capacity_limit": 300, # Total maximum items they can hold
            "current_stock_count": 0,
            "needs": { # Item name: current accepted quantity (max capacity for that item)
                "Milk": 50,
                "Bread": 80,
                "Canned Soup": 120,
                "Flour": 50
            },
            "allocated_items": []
        },
        {
            "id": "C002",
            "name": "Community Shelter",
            "capacity_limit": 250,
            "current_stock_count": 0,
            "needs": {
                "Apples": 75,
                "Pasta": 100,
                "Rice": 50,
                "Bread": 25,
                "Yogurt": 50
            },
            "allocated_items": []
        },
        {
            "id": "C003",
            "name": "Youth Center",
            "capacity_limit": 150,
            "current_stock_count": 0,
            "needs": {
                "Milk": 40,
                "Canned Soup": 60,
                "Pasta": 50
            },
            "allocated_items": []
        }
    ]

    return donations, charity_profiles

# --- Member 2: Urgency Scoring ---

def calculate_urgency_score(expiry_date, today):
    """
    Implements logic for Freshness/Urgency Score based on expiry date.
    Score is normalized from 0 (long time left) to 100 (expiring very soon).
    We cap the max days considered to 30 for the score calculation.
    """
    time_left = expiry_date - today
    days_left = max(0, time_left.days) # Cannot be negative

    # Define the window (e.g., 30 days is the maximum we care about for urgency)
    MAX_URGENCY_DAYS = 30

    if days_left == 0:
        return 100.0 # Expiring today - highest urgency
    elif days_left > MAX_URGENCY_DAYS:
        return 0.0 # Not urgent

    # Linear scaling: 0 days left = 100, MAX_URGENCY_DAYS left = 0
    score = 100 - (days_left / MAX_URGENCY_DAYS) * 100
    return round(score, 2)

def sort_donations_by_priority(donations, today):
    """
    Calculates urgency scores and sorts donations by priority (highest score first).
    """
    scored_donations = []
    for donation in donations:
        score = calculate_urgency_score(donation['expiry_date'], today)
        donation['urgency_score'] = score
        scored_donations.append(donation)

    # Sort in descending order of urgency score
    scored_donations.sort(key=lambda d: d['urgency_score'], reverse=True)
    return scored_donations

# --- Member 3: Allocation Algorithm (Core) ---

def run_allocation_algorithm(donations, charities):
    """
    Implements the constraint satisfaction logic (greedy approach).
    Matches items -> charities considering urgency, needs, and capacity.
    Optimizes so maximum food gets distributed with minimal waste.
    """
    allocation_record = []
    total_distributed = 0
    total_unmatched_waste = 0

    # 1. Iterate through donations, already sorted by urgency (highest first)
    for donation in donations:
        item = donation['item']
        remaining_quantity = donation['quantity']
        original_quantity = donation['quantity']

        # 2. Try to match this donation greedily to a charity
        for charity in charities:
            charity_name = charity['name']
            charity_capacity_remaining = charity['capacity_limit'] - charity['current_stock_count']

            # Check 1: Does the charity accept this item AND still need it?
            if item in charity['needs'] and charity['needs'][item] > 0:

                # Check 2: Does the charity have general capacity remaining?
                if charity_capacity_remaining > 0:
                    needed_by_charity = charity['needs'][item]

                    # Determine the maximum amount we can allocate
                    allocation_amount = min(
                        remaining_quantity,          # Available from donation
                        needed_by_charity,           # Specific item need
                        charity_capacity_remaining   # General capacity limit
                    )

                    if allocation_amount > 0:
                        # Record the allocation
                        record = {
                            "donation_id": donation['id'],
                            "item": item,
                            "quantity": allocation_amount,
                            "charity_id": charity['id'],
                            "charity_name": charity_name
                        }
                        allocation_record.append(record)

                        # Update states (Crucial for constraint satisfaction)
                        remaining_quantity -= allocation_amount
                        charity['needs'][item] -= allocation_amount
                        charity['current_stock_count'] += allocation_amount
                        total_distributed += allocation_amount

                        # Add to charity's internal record (for reporting)
                        charity['allocated_items'].append({
                            "item": item,
                            "quantity": allocation_amount,
                            "score": donation['urgency_score']
                        })

                        # If the entire donation is allocated, break and move to the next donation
                        if remaining_quantity == 0:
                            break

        # 3. Handle Waste (if any quantity remains after checking all charities)
        if remaining_quantity > 0:
            total_unmatched_waste += remaining_quantity
            # Mark the waste for reporting
            allocation_record.append({
                "donation_id": donation['id'],
                "item": item,
                "quantity": remaining_quantity,
                "charity_id": "WASTE",
                "charity_name": "WASTE/NO MATCH"
            })

        # Mark the original donation as fully processed
        donation['is_allocated'] = True

    return allocation_record, total_distributed, total_unmatched_waste

# --- Member 5: Reporting & Integration ---

def generate_report(total_donations_qty, total_distributed, total_unmatched_waste, charities, allocation_record):
    """
    Builds console reports / logs for final distribution and calculates impact metrics.
    """
    print("=" * 60)
    print("           ALLOCATION AGENT - FINAL REPORT           ")
    print("=" * 60)

    # 1. Overall Impact Metrics
    waste_reduction_percentage = (total_distributed / total_donations_qty) * 100 if total_donations_qty > 0 else 0

    print("\n--- IMPACT METRICS ---")
    print(f"Total Donations Received: {total_donations_qty} units")
    print(f"Total Food Distributed:   {total_distributed} units")
    print(f"Total Unmatched Waste:    {total_unmatched_waste} units")
    print(f"Waste Reduction % (Distribution Efficiency): {waste_reduction_percentage:.2f}%")

    # 2. Per-Charity Stats
    print("\n--- PER-CHARITY DISTRIBUTION STATS ---")
    for charity in charities:
        items_received = sum(a['quantity'] for a in charity['allocated_items'])
        capacity_used_percent = (charity['current_stock_count'] / charity['capacity_limit']) * 100

        print(f"\n[{charity['id']}]: {charity['name']}")
        print(f"  > Items Received: {items_received} units")
        print(f"  > Capacity Utilized: {charity['current_stock_count']} / {charity['capacity_limit']} ({capacity_used_percent:.2f}%)")
        
        # FIX: Replaced nested f-string with simple string concatenation inside the join for robustness.
        item_list_str = ", ".join([
            item['item'] + " (" + str(item['quantity']) + ")"
            for item in charity['allocated_items'][:3]
        ])
        print(f'  > Items Distributed: {item_list_str}...') # Show top 3

    # 3. Full Allocation Log (integration/debugging log)
    print("\n--- DETAILED ALLOCATION LOG (TOP 5) ---")
    for i, record in enumerate(allocation_record[:5]):
        print(f"  {i+1}. Donation {record['donation_id']} ({record['item']} x {record['quantity']}) -> {record['charity_name']}")
    print(f"... and {len(allocation_record) - 5} more records.")

# --- Member 4: Testing & Debugging (Integrated Test Function) ---

def run_simulation(case_name, scenario_setup):
    """
    Runs a full simulation for a given scenario setup.
    """
    print(f"\n\n==================================================")
    print(f" RUNNING SCENARIO: {case_name}")
    print(f"==================================================")

    # Setup environment
    today = datetime.date.today()
    donations, charities = scenario_setup(today)

    # Calculate total quantity for reporting
    total_donations_qty = sum(d['quantity'] for d in donations)

    # 1. Urgency Scoring and Sorting (Member 2)
    prioritized_donations = sort_donations_by_priority(donations, today)
    print(f"\n[M2] Top 3 Prioritized Donations:")
    for d in prioritized_donations[:3]:
        print(f"  - {d['item']} (x{d['quantity']}) | Score: {d['urgency_score']:.2f}")


    # 2. Core Allocation (Member 3)
    allocation_record, total_distributed, total_unmatched_waste = run_allocation_algorithm(
        prioritized_donations, charities
    )

    # 3. Reporting (Member 5)
    generate_report(total_donations_qty, total_distributed, total_unmatched_waste, charities, allocation_record)

    # 4. Simple Assertion/Validation (Member 4)
    if total_distributed + total_unmatched_waste == total_donations_qty:
        print("\n[M4] TEST PASSED: Total distribution/waste matches initial donation quantity.")
    else:
        print("\n[M4] TEST FAILED: Quantity mismatch detected.")


def edge_case_oversupply(today):
    """Creates a scenario with oversupply of a single, highly urgent item."""
    donations = [
        {"id": "DSUPER1", "item": "Milk", "quantity": 1000, "expiry_date": today + datetime.timedelta(days=1), "is_allocated": False},
        {"id": "D2", "item": "Bread", "quantity": 50, "expiry_date": today + datetime.timedelta(days=20), "is_allocated": False}
    ]
    charity_profiles = [
        {
            "id": "C10", "name": "Small Pantry", "capacity_limit": 100, "current_stock_count": 0,
            "needs": {"Milk": 50, "Bread": 20}, "allocated_items": []
        },
        {
            "id": "C11", "name": "Milk Only Center", "capacity_limit": 50, "current_stock_count": 0,
            "needs": {"Milk": 40}, "allocated_items": []
        }
    ]
    return donations, charity_profiles

def edge_case_no_match(today):
    """Creates a scenario where the donations don't match any charity needs."""
    donations = [
        {"id": "DNOMATCH1", "item": "Exotic Fruit", "quantity": 200, "expiry_date": today + datetime.timedelta(days=5), "is_allocated": False},
    ]
    charity_profiles = [
        {
            "id": "C20", "name": "Basic Needs", "capacity_limit": 100, "current_stock_count": 0,
            "needs": {"Bread": 50}, "allocated_items": []
        }
    ]
    return donations, charity_profiles

# --- Main Execution ---
if __name__ == "__main__":
    # --- Standard Run ---
    run_simulation("Standard Allocation Run", create_mock_data)

    # --- Edge Case Run 1: Oversupply ---
    run_simulation("Edge Case: Oversupply (Expected High Waste)", edge_case_oversupply)

    # --- Edge Case Run 2: No Match ---
    run_simulation("Edge Case: No Match (Expected 100% Waste)", edge_case_no_match)
