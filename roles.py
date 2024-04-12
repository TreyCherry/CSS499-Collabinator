from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from .auth import login_required, manager_login_required
from .db import (
    get_roles, STATES, get_states
)

bp = Blueprint('roles', __name__)

@bp.route('/roles', methods=('GET', 'POST'))
@login_required
@manager_login_required
def roles():
    if request.method == 'POST':
        return

    roles = get_roles(type=2, invert=True)


    return render_template('manage/roles.html', roles=roles, activeNav="roles", states=STATES)