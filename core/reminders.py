"""Validation and time calculations for departure reminders."""

from datetime import datetime, timedelta

MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 720


def parse_departure_time(value):
    """Parse a 24-hour HH:MM value, raising ValueError for bad input."""
    if not isinstance(value, str):
        raise ValueError("Enter a departure time in HH:MM format.")
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError as exc:
        raise ValueError("Enter a departure time in HH:MM format.") from exc


def validate_duration(value):
    """Return duration as minutes when it is within the supported range."""
    try:
        duration = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Preparation duration must be a whole number of minutes.") from exc
    if not MIN_DURATION_MINUTES <= duration <= MAX_DURATION_MINUTES:
        raise ValueError(f"Preparation duration must be between {MIN_DURATION_MINUTES} and {MAX_DURATION_MINUTES} minutes.")
    return duration


def calculate_reminder_times(departure_time, duration_minutes, now=None):
    """Return departure/preparation datetimes, moving passed times to tomorrow."""
    departure = parse_departure_time(departure_time) if isinstance(departure_time, str) else departure_time
    duration = validate_duration(duration_minutes)
    current = now or datetime.now()
    departure_at = datetime.combine(current.date(), departure)
    moved_to_tomorrow = departure_at <= current
    if moved_to_tomorrow:
        departure_at += timedelta(days=1)
    return departure_at, departure_at - timedelta(minutes=duration), moved_to_tomorrow
