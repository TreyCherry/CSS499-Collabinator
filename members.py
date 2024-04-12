from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from .auth import login_required, manager_login_required
from .db import update_user, get_users, get_user_by_id, get_roles

bp = Blueprint('members', __name__, url_prefix='/')



@bp.route('/members', methods=('GET', 'POST'))
@login_required
@manager_login_required
def members():
    if request.method == 'POST':
        session["target_id"] = request.form["user_id"]
        return redirect(url_for('members.editMember'))

    members = get_users()
    return render_template('members.html', members=members, activeNav="members")

@bp.route('/members/edit', methods=('GET', 'POST'))
@login_required
@manager_login_required
def editMember():
    targetid = session.pop("target_id", None)
    if targetid is None or request.method == 'POST':
        if request.form.get("email", None) is None:
            return redirect(url_for('members'))
        update_user(targetid, request.form)
        return redirect(url_for('members'))

    session["target_id"] = targetid

    member = get_user_by_id(targetid)
    roles = get_roles()
    return render_template('editMember.html', activeNav="members", member=member, roles=roles)