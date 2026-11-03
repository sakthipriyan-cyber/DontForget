"""Safe migration of existing history.json to SQLite database."""

import json
from pathlib import Path

# Import database functions directly
from web.database import get_db_connection, init_db

# Paths
HISTORY_JSON = Path(__file__).parent.parent / "history.json"
MIGRATION_TRACKER = Path(__file__).parent / "migration_tracker.json"


def load_json_history():
    """Load history from the JSON file (read-only)."""
    if not HISTORY_JSON.exists():
        print(f"History file not found: {HISTORY_JSON}")
        return []

    try:
        with HISTORY_JSON.open("r", encoding="utf-8") as file:
            history = json.load(file)

        if isinstance(history, list):
            return history

        print("Warning: History file has an unexpected format.")
        return []

    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not read history.json: {e}")
        return []


def get_migrated_ids():
    """Load the set of already migrated record IDs."""
    if not MIGRATION_TRACKER.exists():
        return set()

    try:
        with MIGRATION_TRACKER.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return set(data.get("migrated_ids", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_migrated_ids(migrated_ids):
    """Save the set of migrated record IDs."""
    try:
        with MIGRATION_TRACKER.open("w", encoding="utf-8") as file:
            json.dump({"migrated_ids": list(migrated_ids)}, file, indent=4)
    except OSError as e:
        print(f"Warning: Could not save migration tracker: {e}")


def create_record_id(record):
    """Create a unique ID for a record based on its content."""
    # Use timestamp + destination + packed items as unique identifier
    timestamp = record.get("timestamp", "")
    destination = record.get("destination", "")
    packed = tuple(sorted(record.get("packed_items", [])))
    return f"{timestamp}|{destination}|{packed}"


def mark_legacy_history_as_handled():
    """Prevent existing legacy records from returning after history is cleared."""
    # Read the legacy history without modifying it.
    if HISTORY_JSON.exists():
        with HISTORY_JSON.open("r", encoding="utf-8") as file:
            history = json.load(file)

        if not isinstance(history, list):
            raise ValueError("Legacy history must be a JSON list.")
    else:
        history = []

    # Read the tracker strictly; don't overwrite an unreadable tracker.
    migrated_ids = set()

    if MIGRATION_TRACKER.exists():
        with MIGRATION_TRACKER.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Migration tracker has an invalid format.")

        ids = data.get("migrated_ids")
        if not isinstance(ids, list) or not all(
            isinstance(record_id, str) for record_id in ids
        ):
            raise ValueError("Migration tracker IDs are invalid.")

        migrated_ids.update(ids)

    # Mark every valid existing legacy record as handled.
    for record in history:
        if isinstance(record, dict):
            migrated_ids.add(create_record_id(record))

    # Write a temporary file, then replace the tracker atomically.
    temp_path = MIGRATION_TRACKER.with_name(
        MIGRATION_TRACKER.name + ".tmp"
    )

    try:
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(
                {"migrated_ids": sorted(migrated_ids)},
                file,
                indent=4,
            )

        temp_path.replace(MIGRATION_TRACKER)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return len(migrated_ids)


def migrate_history():
    """Migrate JSON history to SQLite without modifying the original file."""
    print("Starting migration...")

    # Initialize database
    init_db()

    # Load existing migrated IDs
    migrated_ids = get_migrated_ids()

    # Load JSON history (read-only)
    json_history = load_json_history()

    if not json_history:
        print("No records found in history.json")
        return

    print(f"Found {len(json_history)} records in history.json")
    print(f"Already migrated: {len(migrated_ids)} records")

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()

    new_migrations = 0

    for record in json_history:
        if not isinstance(record, dict):
            continue

        # Create unique ID for this record
        record_id = create_record_id(record)

        # Skip if already migrated
        if record_id in migrated_ids:
            continue

        # Extract data
        destination = record.get("destination")
        timestamp = record.get("timestamp")
        packed_items = record.get("packed_items", [])
        missing_items = record.get("missing_items", [])
        packed_count = record.get("packed_count", 0)
        total_items = record.get("total_items", 0)

        # Validate required fields
        if not all([destination, timestamp]):
            print(f"Skipping invalid record: {record_id}")
            continue

        # Convert lists to JSON for storage
        import json as json_module
        packed_json = json_module.dumps(packed_items)
        missing_json = json_module.dumps(missing_items)

        # Insert into database
        try:
            cursor.execute('''
                INSERT INTO checklist_sessions
                (destination, timestamp, packed_items, missing_items, packed_count, total_items)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (destination, timestamp, packed_json, missing_json, packed_count, total_items))

            migrated_ids.add(record_id)
            new_migrations += 1
            print(f"Migrated: {destination} at {timestamp}")

        except Exception as e:
            print(f"Error migrating record {record_id}: {e}")

    # Commit changes
    conn.commit()
    conn.close()

    # Save migration tracker
    save_migrated_ids(migrated_ids)

    print(f"\nMigration complete!")
    print(f"New records migrated: {new_migrations}")
    print(f"Total records in tracker: {len(migrated_ids)}")
    print(f"Original history.json was NOT modified.")


if __name__ == "__main__":
    migrate_history()
