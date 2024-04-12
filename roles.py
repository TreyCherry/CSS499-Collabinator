from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from .auth import login_required, manager_login_required
from .db import (
    get_roles
)

bp = Blueprint('roles', __name__)

@bp.route('/roles', methods=('GET', 'POST'))
@login_required
@manager_login_required
def roles():
    if request.method == 'POST':
        return

    roles = get_roles()
    return render_template('roles.html', roles=roles, activeNav="roles")