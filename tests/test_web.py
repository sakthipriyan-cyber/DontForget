"""Route tests for the Don'tForget Flask application."""

import importlib
import sys

pytest = importlib.import_module("pytest")


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create the app against a fresh SQLite database for each test."""
    database = importlib.import_module("web.database")
    test_database = tmp_path / "dontforget-test.db"
    monkeypatch.setattr(database, "DB_PATH", test_database)

    # Import the app only after redirecting the database to a temporary file.
    sys.modules.pop("web.app", None)
    app_module = importlib.import_module("web.app")
    app_module.app.config.update(TESTING=True)
    app_module.app.config["TEST_DATABASE"] = test_database

    yield app_module.app

    sys.modules.pop("web.app", None)


@pytest.fixture
def client(app):
    return app.test_client()


def test_checklist_get_uses_selected_destination_without_saving(client):
    response = client.get("/checklist?destination=Lab")

    assert response.status_code == 200
    assert b"Lab Essentials" in response.data
    assert b"Lab Record" in response.data


def test_checklist_get_invalid_destination_falls_back_to_college(client):
    response = client.get("/checklist?destination=Unknown")

    assert response.status_code == 200
    assert b"College Essentials" in response.data
    assert b"Unknown Essentials" not in response.data


def test_checklist_post_saves_session_and_shows_summary(client):
    response = client.post(
        "/checklist",
        data={
            "destination": "Outing",
            "packed_items": ["Wallet", "Phone"],
        },
    )

    assert response.status_code == 200
    assert b"Outing Checklist Summary" in response.data
    assert b"Success!" in response.data
    assert b"Keys" in response.data

    database = importlib.import_module("web.database")
    assert database.DB_PATH == client.application.config["TEST_DATABASE"]


def test_checklist_post_invalid_destination_redirects_without_saving(client):
    response = client.post(
        "/checklist",
        data={"destination": "Unknown", "packed_items": []},
    )

    assert response.status_code == 302
    assert "/checklist" in response.headers["Location"]

    with client.session_transaction() as session:
        assert (
            "error",
            "Invalid destination selected.",
        ) in session["_flashes"]

    redirected = client.get(response.headers["Location"])
    assert redirected.status_code == 200
    assert b"College Essentials" in redirected.data


def test_history_displays_saved_sessions_and_destination_filter(client):
    client.post(
        "/checklist",
        data={"destination": "College", "packed_items": ["ID Card"]},
    )

    all_history = client.get("/history")
    filtered_history = client.get("/history?destination=Lab")

    assert all_history.status_code == 200
    assert b"College" in all_history.data
    assert b"Wallet" in all_history.data
    assert b"<h3>College</h3>" not in filtered_history.data


def test_smart_insights_uses_saved_history(client):
    client.post(
        "/checklist",
        data={"destination": "Outing", "packed_items": ["Wallet", "Phone"]},
    )

    response = client.get("/insights")

    assert response.status_code == 200
    assert b"Smart Insights" in response.data
    assert b"Outing" in response.data
    assert b"Keys" in response.data


def test_reminder_get_renders_form(client):
    response = client.get("/reminder")

    assert response.status_code == 200
    assert b"Departure Reminder" in response.data
    assert b"Preparation time (minutes)" in response.data


def test_reminder_post_valid_input_displays_preparation_time(client):
    response = client.post(
        "/reminder",
        data={"departure_time": "23:30", "duration_minutes": "45"},
    )

    assert response.status_code == 200
    assert b"Reminder set" in response.data
    assert b"Start preparing at" in response.data
    assert b"Keep this page open" in response.data


@pytest.mark.parametrize(
    ("departure_time", "duration_minutes", "message"),
    [
        ("not-a-time", "30", "Enter a departure time in HH:MM format."),
        (
            "09:00",
            "0",
            "Preparation duration must be between 1 and 720 minutes.",
        ),
        (
            "09:00",
            "721",
            "Preparation duration must be between 1 and 720 minutes.",
        ),
        (
            "09:00",
            "many",
            "Preparation duration must be a whole number of minutes.",
        ),
    ],
)
def test_reminder_post_invalid_input_shows_error(
    client, departure_time, duration_minutes, message
):
    response = client.post(
        "/reminder",
        data={
            "departure_time": departure_time,
            "duration_minutes": duration_minutes,
        },
    )

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert ("error", message) in session["_flashes"]

    assert b"Reminder set" not in response.data