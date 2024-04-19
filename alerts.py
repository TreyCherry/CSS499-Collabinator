import functools
from flask import (
    Blueprint, jsonify, request, session, redirect, url_for, flash
)
from .db import (
    get_alerts_by_user_id, add_alert, mark_alert_as_read_in_db, delete_alert_from_db, get_user_by_id
)

bp = Blueprint('alerts', __name__, url_prefix='/alerts')  # Setup Blueprint

def login_required(view):  # Decorator for login check
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user_id') is None:  # Check session
            return redirect(url_for('auth.login'))  # Redirect if not logged in
        return view(**kwargs)
    return wrapped_view

@bp.route('/', methods=['GET'])  # Fetch alerts route
@login_required
def get_alerts():
    user_id = session.get('user_id')  # Get user ID from session
    alerts = get_alerts_by_user_id(user_id)  # Fetch alerts from DB
    return jsonify({'status': 'success', 'alerts': alerts}), 200  # Return alerts

@bp.route('/add', methods=['POST'])  # Add alert route
@login_required
def add_alert_route():
    user_id = session.get('user_id')  # Get user ID
    message = request.json.get('message')  # Get message from request
    link = request.json.get('link')  # Get link from request
    if not message or not link:
        return jsonify({'status': 'error', 'message': 'Message and link are required'}), 400  # Validate message and link
    add_alert(user_id, message, link)  # Add alert to DB
    return jsonify({'status': 'success'}), 201  # Success response

@bp.route('/<int:alert_id>/read', methods=['PUT'])  # Mark alert as read
@login_required
def mark_alert_read(alert_id):
    mark_alert_as_read_in_db(alert_id)  # Update alert in DB
    return jsonify({'status': 'success'}), 200  # Success response

@bp.route('/<int:alert_id>/delete', methods=['DELETE'])  # Delete alert route
@login_required
def delete_alert(alert_id):
    delete_alert_from_db(alert_id)  # Remove alert from DB
    return jsonify({'status': 'success'}), 200  # Success response
