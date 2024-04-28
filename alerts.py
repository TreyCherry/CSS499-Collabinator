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
            return f"Document Update: Document \"{kwargs['document_name']}\" uploaded and needs approval."
        case "doc_approved":
            return f"Document Update: Document \"{kwargs['document_name']}\" approved for review, take action now to select reviewers."
        case "doc_removed":
            return f"Document Update: Document \"{kwargs['document_name']}\" has been removed."
        case "doc_rejected":
            return f"Document Update: Document \"{kwargs['document_name']}\" has been rejected and removed from the site."
        case "doc_user_added":
            return f"Document Update: You have been selected to contribute to document review on \"{kwargs['document_name']}\". View the document now."
        case "new_comment":
            return f"New comment added to document \"{kwargs['document_name']}\". Click to View"
        case "new_response":
            return f"{kwargs['user_name']} responded to a comment on document \"{kwargs['document_name']}\". Click to View"
        case "comment_resolved":
            return f"{kwargs['first_name']}'s comment \"{kwargs['comment_text']}\" on document \"{kwargs['document_name']}\" has been resolved."
        case "comments_closed":
            return f"Review Update: Comments have been closed for document \"{kwargs['document_name']}\"."
        case "review_closed":
            return f"Review Update: Review for document \"{kwargs['document_name']}\" has been closed."
        case _:
            return None #if message type doesn't exist, return None"