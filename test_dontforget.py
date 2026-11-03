
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core.checklist import get_checklist, calculate_missing_items
from core.insights import analyze_destination
import main


class TestDontForget(unittest.TestCase):

    
    def test_insights_count_destination_sessions(self):
        history = [
            {
                "destination": "College",
                "missing_items": ["Keys"],
                "total_items": 5,
            },
            {
                "destination": "Lab",
                "missing_items": ["Pen"],
                "total_items": 5,
            },
        ]

        result = analyze_destination(history, "College")

        self.assertEqual(result["sessions"], 1)
        self.assertEqual(result["total_missing"], 1)

    def test_insights_calculate_missing_percentage(self):
        history = [
            {
                "destination": "College",
                "missing_items": ["Keys"],
                "total_items": 5,
            },
            {
                "destination": "College",
                "missing_items": [],
                "total_items": 5,
            },
        ]

        result = analyze_destination(history, "College")

        self.assertAlmostEqual(result["missing_percentage"], 10.0)

    def test_insights_handle_empty_history(self):
        result = analyze_destination([], "Outing")

        self.assertEqual(result["sessions"], 0)
        self.assertEqual(result["missing_percentage"], 0.0)
        self.assertTrue(result["recommendations"])

    def test_get_checklist_returns_items(self):
        self.assertIn("Lab Record", get_checklist("Lab"))

    def test_get_checklist_returns_independent_list(self):
        items = get_checklist("College")
        items.append("Test Item")

        self.assertNotIn("Test Item", get_checklist("College"))

    def test_calculate_missing_items(self):
        missing = calculate_missing_items(
            "College",
            ["ID Card", "Wallet"]
        )

        self.assertEqual(
            missing,
            ["Keys", "Laptop", "Charger"]
        )

    def test_all_destinations_exist(self):
        """Every supported destination has a checklist."""
        self.assertEqual(
            set(main.CHECKLISTS.keys()),
            {"College", "Lab", "Outing"}
        )

    def test_college_checklist_items(self):
        """College contains the expected essential items."""
        self.assertEqual(
            main.CHECKLISTS["College"],
            ["ID Card", "Wallet", "Keys", "Laptop", "Charger"]
        )

    def test_lab_contains_lab_record(self):
        """Lab checklist includes the lab record."""
        self.assertIn("Lab Record", main.CHECKLISTS["Lab"])

    def test_outing_contains_phone(self):
        """Outing checklist includes a phone."""
        self.assertIn("Phone", main.CHECKLISTS["Outing"])

    def test_save_and_load_history(self):
        """Saved history can be loaded again."""
        sample_record = {
            "destination": "College",
            "timestamp": "2026-10-23T08:00:00+05:30",
            "packed_items": ["ID Card", "Wallet"],
            "missing_items": ["Keys"],
            "packed_count": 2,
            "total_items": 3
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_history.json"

            with (
                patch.object(main, "HISTORY_FILE", test_file),
                patch.object(main, "load_history", wraps=main.load_history)
            ):
                main.save_history(sample_record)

                with test_file.open("r", encoding="utf-8") as file:
                    saved_records = json.load(file)

                self.assertEqual(saved_records, [sample_record])

    def test_missing_history_returns_empty_list(self):
        """A nonexistent history file starts with empty history."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "missing.json"

            with patch.object(main, "HISTORY_FILE", test_file):
                self.assertEqual(main.load_history(), [])

    def test_packed_and_missing_counts(self):
        """Packed and missing counts cover the checklist."""
        checklist = main.CHECKLISTS["College"]
        packed = ["ID Card", "Wallet"]
        missing = [item for item in checklist if item not in packed]

        self.assertEqual(len(packed) + len(missing), len(checklist))
        self.assertEqual(len(packed), 2)


if __name__ == "__main__":
    unittest.main()
