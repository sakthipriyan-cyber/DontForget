"""Flask application for Don'tForget web version."""
import json
from flask import Flask, render_template, request, flash, redirect, url_for
from core.checklist import CHECKLISTS, get_checklist, calculate_missing_items
from core.insights import analyze_destination
from core.reminders import calculate_reminder_times
from web.database import (
    init_db,
    save_checklist_session,
    get_session_count,
    get_last_session,
    get_all_sessions,
    get_sessions_by_destination,
    get_all_destinations,
    delete_all_sessions,
)
from web.migration import (
    migrate_history,
    mark_legacy_history_as_handled,
)

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Initialize database on startup
init_db()


@app.route('/')
def home():
    """Home dashboard with quick access to all features."""
    total_sessions = get_session_count()
    last_session = get_last_session()

    last_session_text = "No sessions yet"
    if last_session:
        last_session_text = f"{last_session['destination']} - {last_session['packed_count']}/{last_session['total_items']} items"

    return render_template('home.html',
                          total_sessions=total_sessions,
                          last_session=last_session_text)


@app.route('/checklist', methods=['GET', 'POST'])
def checklist():
    """Destination checklist page."""
    if request.method == 'POST':
        destination = request.form.get('destination')
        packed_items = request.form.getlist('packed_items')

        if not destination or destination not in CHECKLISTS:
            flash('Invalid destination selected.', 'error')
            return redirect(url_for('checklist'))

        try:
            checklist_items = get_checklist(destination)
            missing_items = calculate_missing_items(destination, packed_items)
            packed_count = len(packed_items)
            total_items = len(checklist_items)

            # Save to database
            save_checklist_session(
                destination=destination,
                packed_items=packed_items,
                missing_items=missing_items,
                packed_count=packed_count,
                total_items=total_items
            )

            flash('Checklist saved successfully!', 'success')

            return render_template('checklist.html',
                                  destination=destination,
                                  checklist_items=checklist_items,
                                  packed_items=packed_items,
                                  missing_items=missing_items,
                                  packed_count=packed_count,
                                  total_items=total_items,
                                  completion_percent=(packed_count / total_items * 100) if total_items > 0 else 0,
                                  saved=True)

        except ValueError as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('checklist'))

    # GET request - show form
    from core.checklist import get_all_destinations
    destination = request.args.get('destination', 'College')
    all_destinations = get_all_destinations()

    if destination not in all_destinations:
        destination = all_destinations[0] if all_destinations else 'College'

    checklist_items = get_checklist(destination)

    return render_template('checklist.html',
                          destination=destination,
                          destinations=all_destinations,
                          checklist_items=checklist_items,
                          packed_items=[],
                          missing_items=[],
                          packed_count=0,
                          total_items=len(checklist_items),
                          completion_percent=0,
                          saved=False)


@app.route('/history')
def history():
    """Checklist history page with filtering."""
    filter_destination = request.args.get('destination', 'All')

    if filter_destination == 'All':
        sessions = get_all_sessions()
    else:
        sessions = get_sessions_by_destination(filter_destination)

    # Convert sessions to list of dicts for template
    sessions_list = []
    unique_destinations = set()
    for session in sessions:
        import json
        packed_items = json.loads(session['packed_items'])
        missing_items = json.loads(session['missing_items'])
        completion_percent = (session['packed_count'] / session['total_items'] * 100) if session['total_items'] > 0 else 0
        unique_destinations.add(session['destination'])

        sessions_list.append({
            'id': session['id'],
            'destination': session['destination'],
            'timestamp': session['timestamp'],
            'packed_items': packed_items,
            'missing_items': missing_items,
            'packed_count': session['packed_count'],
            'total_items': session['total_items'],
            'completion_percent': completion_percent
        })

    # Get available destinations for filter
    available_destinations = get_all_destinations()

    return render_template('history.html',
                          sessions=sessions_list,
                          filter_destination=filter_destination,
                          available_destinations=available_destinations,
                          unique_destinations_count=len(unique_destinations))



@app.route('/history/delete-all', methods=['POST'])
def delete_history():
    """Clear history without restoring old legacy records."""
    try:
        # Mark existing legacy records as handled before deleting.
        mark_legacy_history_as_handled()

        # Delete the saved database records.
        deleted_count = delete_all_sessions()

        flash(
            f'History cleared. {deleted_count} session(s) deleted.',
            'success'
        )
    except Exception:
        app.logger.exception("Could not clear history safely.")
        flash(
            'History could not be cleared safely. No deletion was attempted '
            'if updating the migration tracker failed.',
            'error'
        )

    return redirect(url_for('history'))



@app.route('/insights')
def insights():
    """Show destination-specific insights from saved history."""
    history = []

    for session in get_all_sessions():
        history.append({
            "destination": session["destination"],
            "missing_items": json.loads(session["missing_items"]),
            "total_items": session["total_items"],
        })

    results = [
        analyze_destination(history, destination)
        for destination in CHECKLISTS
    ]

    return render_template("insights.html", results=results)


@app.route('/reminder', methods=['GET', 'POST'])
def reminder():
    """Set a browser-based reminder to begin preparing before departure."""
    departure_time = request.form.get('departure_time', '')
    duration_minutes = request.form.get('duration_minutes', '30')
    reminder_data = None
    if request.method == 'POST':
        try:
            departure_at, preparation_at, moved_to_tomorrow = calculate_reminder_times(departure_time, duration_minutes)
            reminder_data = {
                'departure_iso': departure_at.isoformat(),
                'preparation_iso': preparation_at.isoformat(),
                'departure_display': departure_at.strftime('%A, %d %B at %H:%M'),
                'preparation_display': preparation_at.strftime('%A, %d %B at %H:%M'),
                'moved_to_tomorrow': moved_to_tomorrow,
            }
        except ValueError as error:
            flash(str(error), 'error')
    return render_template('reminder.html', departure_time=departure_time, duration_minutes=duration_minutes, reminder=reminder_data)


@app.route('/migrate')
def migrate():
    """Trigger migration from JSON to SQLite (for initial setup)."""
    try:
        migrate_history()
        flash('Migration completed successfully!', 'success')
    except Exception as e:
        flash(f'Migration error: {str(e)}', 'error')

    return redirect(url_for('home'))


@app.route('/settings')
def settings():
    """Settings page for application configuration."""
    from web.database import get_custom_destinations
    custom_destinations = get_custom_destinations()
    return render_template('settings.html', custom_destinations=custom_destinations)


@app.route('/settings/add-destination', methods=['POST'])
def add_destination():
    """Add a new custom destination."""
    from web.database import add_destination
    from flask import jsonify

    data = request.get_json()
    name = data.get('name', '').strip()
    items = data.get('items', [])

    if not name:
        return jsonify({'error': 'Destination name is required'}), 400

    if not items:
        return jsonify({'error': 'At least one item is required'}), 400

    success = add_destination(name, items)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Destination already exists'}), 400


@app.route('/settings/delete-destination', methods=['POST'])
def delete_destination():
    """Delete a custom destination."""
    from web.database import delete_destination
    from flask import jsonify

    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Destination name is required'}), 400

    delete_destination(name)
    return jsonify({'success': True})


@app.route('/export-history')
def export_history():
    """Export checklist history as JSON."""
    from flask import Response
    import json

    sessions = get_all_sessions()
    export_data = []

    for session in sessions:
        export_data.append({
            'id': session['id'],
            'destination': session['destination'],
            'timestamp': session['timestamp'],
            'packed_items': json.loads(session['packed_items']),
            'missing_items': json.loads(session['missing_items']),
            'packed_count': session['packed_count'],
            'total_items': session['total_items']
        })

    response = Response(
        json.dumps(export_data, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=dontforget_history.json'}
    )
    return response


@app.route('/settings/clear-history')
def clear_history():
    """Clear all checklist history without restoring legacy records."""
    try:
        # Protect the migration tracker before deleting database rows.
        mark_legacy_history_as_handled()

        # Use the existing database helper.
        deleted_count = delete_all_sessions()

        flash(
            f'All history has been cleared. '
            f'{deleted_count} record(s) deleted.',
            'success'
        )
    except Exception as e:
        app.logger.exception("Could not clear history safely.")
        flash(
            f'History could not be cleared safely: {e}',
            'error'
        )

    return redirect(url_for('settings'))

@app.route('/hardware')
def hardware():
    """Hardware status page showing unavailable features."""
    return render_template('hardware.html')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
