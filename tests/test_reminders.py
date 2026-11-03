from datetime import datetime

import pytest

from core.reminders import calculate_reminder_times, parse_departure_time, validate_duration


def test_parse_departure_time_accepts_24_hour_time():
    assert parse_departure_time("09:30").hour == 9


@pytest.mark.parametrize("value", ["9:30 AM", "25:00", "not-a-time"])
def test_parse_departure_time_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        parse_departure_time(value)


@pytest.mark.parametrize("value", [0, 721, "many"])
def test_validate_duration_rejects_out_of_range_values(value):
    with pytest.raises(ValueError):
        validate_duration(value)


def test_calculate_reminder_times_returns_preparation_time():
    departure, preparation, moved = calculate_reminder_times("09:30", 45, datetime(2026, 10, 24, 8, 0))
    assert departure == datetime(2026, 10, 24, 9, 30)
    assert preparation == datetime(2026, 10, 24, 8, 45)
    assert moved is False


def test_passed_departure_time_is_scheduled_for_tomorrow():
    departure, preparation, moved = calculate_reminder_times("09:30", 30, datetime(2026, 10, 24, 18, 0))
    assert departure == datetime(2026, 10, 25, 9, 30)
    assert preparation == datetime(2026, 10, 25, 9, 0)
    assert moved is True
