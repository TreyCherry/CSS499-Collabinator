from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint('workflow', __name__)

@bp.route('/')
def index():
    docList = []
    if g.user:
        db = get_db()
        allowedDocs = db.execute(
            'SELECT document_id FROM DocRoleStates WHERE role_id = ? AND allowed_states > 0', (g.user['role_id'],)
        ).fetchall()
        for docId in allowedDocs:
            doc = db.execute(
                'SELECT * FROM Documents WHERE document_id = ?', (docId)
            ).fetchone()
            docList.append(doc)
    return render_template('index.html', docs=docList, activeNav="index")