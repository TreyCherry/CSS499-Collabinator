from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint('members', __name__, url_prefix='/')

@bp.route('/members')
@login_required
def members():
    db = get_db()
    members = db.execute(
        'SELECT * FROM Users'
    ).fetchall()
    return render_template('members.html', members=members, activeNav="members")