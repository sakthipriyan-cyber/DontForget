"""SQLite database utilities for Don'tForget web application."""

import sqlite3
from datetime import datetime
from pathlib import Path
import json

# Database file path
DB_PATH = Path(__file__).parent / "dontforget.db"


def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def init_db():
    """Initialize the database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checklist_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            packed_items TEXT NOT NULL,
            missing_items TEXT NOT NULL,
            packed_count INTEGER NOT NULL,
            total_items INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            items TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()



def save_checklist_session(destination, packed_items, missing_items, packed_count, total_items):
    """Save a checklist session to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    timestamp = datetime.now().astimezone().isoformat(timespec='seconds')
    packed_json = json.dumps(packed_items)
    missing_json = json.dumps(missing_items)

    cursor.execute('''
        INSERT INTO checklist_sessions
        (destination, timestamp, packed_items, missing_items, packed_count, total_items)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (destination, timestamp, packed_json, missing_json, packed_count, total_items))

    conn.commit()
    session_id = cursor.lastrowid
    conn.close()

    return session_id


def get_all_sessions():
    """Retrieve all checklist sessions from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, destination, timestamp, packed_items, missing_items,
               packed_count, total_items
        FROM checklist_sessions
        ORDER BY timestamp DESC
    ''')

    sessions = cursor.fetchall()
    conn.close()

    return sessions


def delete_all_sessions():
    """Delete all saved checklist history without deleting the table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM checklist_sessions")
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



def get_sessions_by_destination(destination):
    """Retrieve checklist sessions for a specific destination."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, destination, timestamp, packed_items, missing_items,
               packed_count, total_items
        FROM checklist_sessions
        WHERE destination = ?
        ORDER BY timestamp DESC
    ''', (destination,))

    sessions = cursor.fetchall()
    conn.close()

    return sessions


def get_session_count():
    """Get the total number of checklist sessions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM checklist_sessions')
    result = cursor.fetchone()
    conn.close()

    return result['count'] if result else 0


def get_last_session():
    """Get the most recent checklist session."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT destination, timestamp, packed_count, total_items
        FROM checklist_sessions
        ORDER BY timestamp DESC
        LIMIT 1
    ''')

    session = cursor.fetchone()
    conn.close()

    return session


def get_all_destinations():
    """Get list of all unique destinations in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT destination FROM checklist_sessions ORDER BY destination')
    destinations = [row['destination'] for row in cursor.fetchall()]
    conn.close()

    return destinations


def add_destination(name, items):
    """Add a new custom destination with items to a custom_destinations table."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create custom_destinations table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            items TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    timestamp = datetime.now().astimezone().isoformat(timespec='seconds')
    items_json = json.dumps(items)

    try:
        cursor.execute('''
            INSERT INTO custom_destinations (name, items, created_at)
            VALUES (?, ?, ?)
        ''', (name, items_json, timestamp))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_custom_destinations():
    """Get all custom destinations."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, items, created_at
        FROM custom_destinations
        ORDER BY name
    ''')

    destinations = []
    for row in cursor.fetchall():
        destinations.append({
            'id': row['id'],
            'name': row['name'],
            'items': json.loads(row['items']),
            'created_at': row['created_at']
        })

    conn.close()
    return destinations


def delete_destination(name):
    """Delete a custom destination."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM custom_destinations WHERE name = ?', (name,))
    conn.commit()
    conn.close()


def get_all_checklist_items():
    """Get all available checklist items (both built-in and custom)."""
    from core.checklist import CHECKLISTS

    all_items = list(CHECKLISTS.keys())

    # Add custom destinations
    custom_dests = get_custom_destinations()
    for dest in custom_dests:
        if dest['name'] not in all_items:
            all_items.append(dest['name'])

    return sorted(all_items)
