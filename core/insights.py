
"""Reusable analytics for Don'tForget."""

from collections import Counter


def analyze_destination(history, destination):
    """Calculate missing-item statistics for one destination."""

    records = [
        record
        for record in history
        if isinstance(record, dict)
        and record.get("destination") == destination
    ]

    sessions = len(records)
    missing_counts = Counter()
    total_items = 0
    total_missing = 0

    for record in records:
        missing = record.get("missing_items", [])

        if not isinstance(missing, list):
            missing = []

        missing_counts.update(
            item for item in missing if isinstance(item, str)
        )
        total_missing += len(missing)

        try:
            count = int(record.get("total_items", 0))
            if count > 0:
                total_items += count
        except (TypeError, ValueError):
            pass

    missing_percentage = (
        total_missing / total_items * 100
        if total_items > 0
        else 0.0
    )

    ranked_items = sorted(
        missing_counts.items(),
        key=lambda entry: (-entry[1], entry[0].lower())
    )

    recommendations = []

    if sessions == 0:
        recommendations.append(
            "Complete a checklist for this destination to begin "
            "building insights."
        )
    elif sessions < 3:
        recommendations.append(
            "Complete at least 3 checklists for this destination "
            "before relying on patterns."
        )
    else:
        high_risk = [
            (item, count)
            for item, count in ranked_items
            if count / sessions >= 0.5
        ]

        moderate = [
            (item, count)
            for item, count in ranked_items
            if 0.25 <= count / sessions < 0.5
        ]

        if high_risk:
            for item, count in high_risk:
                recommendations.append(
                    f"Check {item} before leaving; it was marked "
                    f"missing in {count}/{sessions} checklists."
                )
        elif moderate:
            for item, count in moderate:
                recommendations.append(
                    f"Pay extra attention to {item}; it was marked "
                    f"missing in {count}/{sessions} checklists."
                )
        else:
            recommendations.append(
                "No frequently missing item reached the 25% threshold."
            )

    return {
        "destination": destination,
        "sessions": sessions,
        "total_items_checked": total_items,
        "total_missing": total_missing,
        "missing_percentage": missing_percentage,
        "ranked_items": ranked_items,
        "recommendations": recommendations,
    }
