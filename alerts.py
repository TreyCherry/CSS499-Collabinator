from flask import (
    Blueprint, jsonify, request, session, redirect, url_for, flash
)

from .auth import login_required

from .db import (
    get_alerts_by_user_id, add_alert, mark_alert_as_read_in_db, delete_alert_from_db, get_user_by_id
)

bp = Blueprint('alerts', __name__, url_prefix='/alerts')  # Setup Blueprint

@bp.route('/', methods=['GET'])  # Fetch alerts route
@login_required
def get_alerts():
    user_id = session.get('user_id')  # Get user ID from session
    alerts = get_alerts_by_user_id(user_id)  # Fetch alerts from DB
    return jsonify({'status': 'success', 'alerts': alerts}), 200  # Return alerts
