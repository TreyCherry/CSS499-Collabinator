from flask import Blueprint, render_template, g
from flask_login import login_required
from .db import get_alerts  # not sure if this is the right import

bp = Blueprint('alerts', __name__, url_prefix='/alerts')

@bp.route('/')
@login_required
def alerts():
    db = get_db()
    user_id = g.user['id']
    alerts = get_alerts(db, user_id)
    return render_template('alerts.html', alerts=alerts)
