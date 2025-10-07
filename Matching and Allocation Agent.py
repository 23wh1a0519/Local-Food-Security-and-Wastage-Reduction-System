import datetime
import random

# --- Member 1: Data & Charity Profiles ---

def create_mock_data(today):
    items = ["Milk", "Bread", "Canned Soup", "Apples", "Pasta", "Flour", "Rice", "Yogurt"]

    donations = []
    for i in range(1, 16):
        item_name = random.choice(items)
        days_to_expiry = random.randint(1, 30)
        expiry_date = today + datetime.timedelta(days=days_to_expiry)
        donations.append({
            "id": f"D{i:03}",
            "item": item_name,
            "quantity": random.randint(10, 100),
            "expiry_date": expiry_date,
            "is_allocated": False
        })

    charity_profiles = [
        {
            "id": "C001",
            "name": "Central Kitchen",
            "capacity_limit": 300,
            "current_stock_count": 0,
            "needs": {"Milk": 50, "Bread": 80, "Canned Soup": 120, "Flour": 50},
            "allocated_items": []
        },
        {
            "id": "C002",
            "name": "Community Shelter",
            "capacity_limit": 250,
            "current_stock_count": 0,
            "needs": {"Apples": 75, "Pasta": 100, "Rice": 50, "Bread": 25, "Yogurt": 50},
            "allocated_items": []
        },
        {
            "id": "C003",
            "name": "Youth Center",
            "capacity_limit": 150,
            "current_stock_count": 0,
            "needs": {"Milk": 40, "Canned Soup": 60, "Pasta": 50},
            "allocated_items": []
        }
    ]
    return donations, charity_profiles


# --- Member 2: Urgency Scoring ---

def calculate_urgency_score(expiry_date, today):
    days_left = max(0, (expiry_date - today).days)
    MAX_URGENCY_DAYS = 30
    if days_left == 0:
        return 100.0
    elif days_left > MAX_URGENCY_DAYS:
        return 0.0
    return round(100 - (days_left / MAX_URGENCY_DAYS) * 100, 2)


def sort_donations_by_priority(donations, today):
    for d in donations:
        d['urgency_score'] = calculate_urgency_score(d['expiry_date'], today)
    donations.sort(key=lambda x: x['urgency_score'], reverse=True)
    return donations


# --- Member 3: Allocation Algorithm ---

def run_allocation_algorithm(donations, charities):
    allocation_record = []
    total_distributed = total_unmatched_waste = 0

    for donation in donations:
        item = donation['item']
        remaining_quantity = donation['quantity']

        for charity in charities:
            if item in charity['needs'] and charity['needs'][item] > 0:
                capacity_remaining = charity['capacity_limit'] - charity['current_stock_count']
                if capacity_remaining > 0:
                    alloc = min(remaining_quantity, charity['needs'][item], capacity_remaining)
                    if alloc > 0:
                        allocation_record.append({
                            "donation_id": donation['id'],
                            "item": item,
                            "quantity": alloc,
                            "charity_id": charity['id'],
                            "charity_name": charity['name']
                        })
                        remaining_quantity -= alloc
                        charity['needs'][item] -= alloc
                        charity['current_stock_count'] += alloc
                        charity['allocated_items'].append({
                            "item": item,
                            "quantity": alloc,
                            "score": donation['urgency_score']
                        })
                        total_distributed += alloc
                        if remaining_quantity == 0:
                            break

        if remaining_quantity > 0:
            total_unmatched_waste += remaining_quantity
            allocation_record.append({
                "donation_id": donation['id'],
                "item": item,
                "quantity": remaining_quantity,
                "charity_id": "WASTE",
                "charity_name": "WASTE/NO MATCH"
            })
        donation['is_allocated'] = True

    return allocation_record, total_distributed, total_unmatched_waste


# --- Member 5: Reporting ---

def generate_report(total_donations_qty, total_distributed, total_unmatched_waste, charities, allocation_record):
    print("=" * 60)
    print("           ALLOCATION AGENT - FINAL REPORT           ")
    print("=" * 60)

    waste_reduction_percentage = (total_distributed / total_donations_qty) * 100 if total_donations_qty > 0 else 0
    print("\n--- IMPACT METRICS ---")
    print(f"Total Donations: {total_donations_qty} units")
    print(f"Distributed:     {total_distributed} units")
    print(f"Unmatched Waste: {total_unmatched_waste} units")
    print(f"Efficiency:      {waste_reduction_percentage:.2f}%")

    print("\n--- PER-CHARITY STATS ---")
    for c in charities:
        capacity_used_percent = (c['current_stock_count'] / c['capacity_limit']) * 100
        print(f"\n[{c['id']}] {c['name']}")
        print(f"  Items Received: {sum(i['quantity'] for i in c['allocated_items'])}")
        print(f"  Capacity Used:  {c['current_stock_count']} / {c['capacity_limit']} ({capacity_used_percent:.2f}%)")
        items_preview = ", ".join([i['item'] + f'({i["quantity"]})' for i in c['allocated_items'][:3]])
        print(f"  Distributed: {items_preview}...")

    print("\n--- ALLOCATION LOG (TOP 5) ---")
    for i, r in enumerate(allocation_record[:5]):
        print(f"  {i+1}. Donation {r['donation_id']} ({r['item']} x {r['quantity']}) -> {r['charity_name']}")
    print(f"... and {len(allocation_record) - 5} more records.")


# --- Member 4: Testing ---

def run_simulation(case_name, scenario_setup):
    print(f"\n\n==================================================")
    print(f" RUNNING SCENARIO: {case_name}")
    print(f"==================================================")

    today = datetime.date.today()
    donations, charities = scenario_setup(today)
    total_qty = sum(d['quantity'] for d in donations)

    prioritized = sort_donations_by_priority(donations, today)
    print(f"\nTop 3 Prioritized Donations:")
    for d in prioritized[:3]:
        print(f"  - {d['item']} (x{d['quantity']}) | Score: {d['urgency_score']:.2f}")

    record, distributed, waste = run_allocation_algorithm(prioritized, charities)
    generate_report(total_qty, distributed, waste, charities, record)

    if distributed + waste == total_qty:
        print("\nTEST PASSED ✅")
    else:
        print("\nTEST FAILED ❌")


def edge_case_oversupply(today):
    donations = [
        {"id": "DSUPER1", "item": "Milk", "quantity": 1000, "expiry_date": today + datetime.timedelta(days=1), "is_allocated": False},
        {"id": "D2", "item": "Bread", "quantity": 50, "expiry_date": today + datetime.timedelta(days=20), "is_allocated": False}
    ]
    charities = [
        {"id": "C10", "name": "Small Pantry", "capacity_limit": 100, "current_stock_count": 0, "needs": {"Milk": 50, "Bread": 20}, "allocated_items": []},
        {"id": "C11", "name": "Milk Only Center", "capacity_limit": 50, "current_stock_count": 0, "needs": {"Milk": 40}, "allocated_items": []}
    ]
    return donations, charities


def edge_case_no_match(today):
    donations = [{"id": "DNOMATCH1", "item": "Exotic Fruit", "quantity": 200, "expiry_date": today + datetime.timedelta(days=5), "is_allocated": False}]
    charities = [{"id": "C20", "name": "Basic Needs", "capacity_limit": 100, "current_stock_count": 0, "needs": {"Bread": 50}, "allocated_items": []}]
    return donations, charities


# --- Main ---

if __name__ == "__main__":
    run_simulation("Standard Allocation Run", create_mock_data)
    run_simulation("Edge Case: Oversupply", edge_case_oversupply)
    run_simulation("Edge Case: No Match", edge_case_no_match)

