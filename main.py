import json
from pathlib import Path
from datetime import datetime
from core.checklist import CHECKLISTS

HISTORY_FILE = Path(__file__).with_name("history.json")
# Don'tForget — Smart Departure Assistant

# Each destination has its own list of essential items.
CHECKLISTS = {
    "College": [
        "ID Card",
        "Wallet",
        "Keys",
        "Laptop",
        "Charger",
    ],
    "Lab": [
        "ID Card",
        "Lab Record",
        "Laptop",
        "Charger",
        "Pen",
    ],
    "Outing": [
        "Wallet",
        "Phone",
        "Keys",
        "Water Bottle",
    ],
}


def load_history():
    """Load saved checklist records from the JSON file."""

    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            history = json.load(file)

        if isinstance(history, list):
            return history

        print("Warning: History file has an unexpected format.")
        return []

    except (json.JSONDecodeError, OSError):
        print("Warning: Could not read history.json.")
        return []


def save_history(record):
    """Append one checklist record and save the history."""

    history = load_history()
    history.append(record)

    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)

        print("Checklist history saved successfully.")

    except OSError:
        print("Warning: Could not save checklist history.")

def choose_destination():
    """Ask the user where they are going."""

    destinations = list(CHECKLISTS.keys())

    print("\nWhere are you going today?")

    for number, destination in enumerate(destinations, start=1):
        print(f"{number}. {destination}")

    while True:
        choice = input("Enter your choice: ").strip()

        if choice.isdigit():
            number = int(choice)

            if 1 <= number <= len(destinations):
                return destinations[number - 1]

        print("Invalid choice. Please enter a listed number.")


def run_checklist(destination):
    """Let the user mark items as packed."""

    items = CHECKLISTS[destination]
    packed_items = set()

    print(f"\n--- {destination} Checklist ---")

    for item in items:
        while True:
            answer = input(f"Have you packed {item}? (y/n): ")
            answer = answer.strip().lower()

            if answer in ("y", "n"):
                break

            print("Please enter y for yes or n for no.")

        if answer == "y":
            packed_items.add(item)

    missing_items = [
        item for item in items if item not in packed_items
    ]
    record = {
        "destination": destination,
        "timestamp": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "packed_items": [
            item for item in items if item in packed_items
        ],
        "missing_items": missing_items,
        "packed_count": len(packed_items),
        "total_items": len(items),
    }

    save_history(record)

    print("\n========== CHECKLIST SUMMARY ==========")
    print(f"Destination: {destination}")
    print(f"Packed: {len(packed_items)}/{len(items)}")

    if missing_items:
        print("\nItems you still need to check:")
        for item in missing_items:
            print(f"- {item}")

        print("\nPlease check these items before leaving.")
    else:
        print("\nAll listed items are marked as packed!")

    print("=======================================")


def show_history():
    """Display previously saved checklist results."""

    history = load_history()

    print("\n========== CHECKLIST HISTORY ==========")

    if not history:
        print("No saved checklist history yet.")
        return

    for number, record in enumerate(history, start=1):
        print(f"\nRecord {number}")
        print(f"Destination: {record.get('destination', 'Unknown')}")
        print(f"Date/time: {record.get('timestamp', 'Unknown')}")
        print(
            f"Packed: {record.get('packed_count', 0)}/"
            f"{record.get('total_items', 0)}"
        )

        missing = record.get("missing_items", [])

        if missing:
            print("Missing items: " + ", ".join(missing))
        else:
            print("Missing items: None")

    print("\n=======================================")



def main():
    while True:
        print("\n" + "=" * 45)
        print("   DON'TFORGET - SMART DEPARTURE ASSISTANT")
        print("=" * 45)
        print("1. Start a new checklist")
        print("2. View checklist history")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            destination = choose_destination()
            run_checklist(destination)

        elif choice == "2":
            show_history()

        elif choice == "3":
            print("Goodbye! Check your essentials before leaving.")
            break

        else:
            print("Invalid choice. Enter 1, 2, or 3.")



if __name__ == "__main__":
    main()
