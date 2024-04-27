from flask import (
    Blueprint, g, render_template
)

from .auth import login_required

from .db import (
    get_alerts_by_id
)

bp = Blueprint('alerts', __name__)  # Setup Blueprint

@bp.route('/alerts')  # Fetch alerts route
@login_required
def alerts():
    user_id = g.user['user_id'] # Get user ID 
    alerts = get_alerts_by_id(user_id)  # Fetch alerts from DB
    return render_template('alerts.html', activeNav="alerts", alerts=alerts)


def make_alert_message(message_type, **kwargs): #specify message type and pass args that are related to that message
    match message_type:
        case "new_user":
            return f"New user created with email: {kwargs['email']}" #for example this one would be make_alert_message("new_user", email="a@a.com")
        case "doc_upload":
            return f"Document Update: Document \"{kwargs['document_name']}\" uploaded. \"{kwargs['stage_desc']}\""
        case "doc_approved":
            return f"Document Update: Document \"{kwargs['document_name']}\" approved for review, take action now to select reviewers."
        case _:
            return None #if message type doesn't exist, return None