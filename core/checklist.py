
"""Shared checklist definitions and helper functions."""

CHECKLISTS = {
    "College": ["ID Card", "Wallet", "Keys", "Laptop", "Charger"],
    "Lab": ["ID Card", "Lab Record", "Laptop", "Charger", "Pen"],
    "Outing": ["Wallet", "Phone", "Keys", "Water Bottle"],
}


def get_checklist(destination):
    """Return the items for a destination, or raise an error."""
    # Check built-in checklists first
    if destination in CHECKLISTS:
        return CHECKLISTS[destination].copy()

    # Check custom destinations from database
    try:
        from web.database import get_custom_destinations
        custom_dests = get_custom_destinations()
        for dest in custom_dests:
            if dest['name'] == destination:
                return dest['items'].copy()
    except Exception:
        pass

    raise ValueError(f"Unknown destination: {destination}")


def get_all_destinations():
    """Get all available destinations (built-in + custom)."""
    destinations = list(CHECKLISTS.keys())

    try:
        from web.database import get_custom_destinations
        custom_dests = get_custom_destinations()
        for dest in custom_dests:
            if dest['name'] not in destinations:
                destinations.append(dest['name'])
    except Exception:
        pass

    return sorted(destinations)


def calculate_missing_items(destination, packed_items):
    """Return checklist items that have not been packed."""
    checklist = get_checklist(destination)
    packed = set(packed_items)

    return [item for item in checklist if item not in packed]
