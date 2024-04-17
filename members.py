from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from .auth import login_required, manager_login_required
from .db import (
    get_db, update_user, get_users, get_user_by_id, get_roles, remove_user
)

bp = Blueprint('members', __name__, url_prefix='/')



@bp.route('/members', methods=('GET', 'POST'))
@login_required
@manager_login_required
def members():
    if request.method == 'POST':
        session["target_id"] = request.form["user_id"]
        return redirect(url_for('members.editMember'))

    members = get_users()
    return render_template('manage/members.html', members=members, activeNav="members")

@bp.route('/members/edit', methods=('GET', 'POST'))
@login_required
@manager_login_required
def editMember():
    targetid = session.pop("target_id", None)
    if targetid is None:
        return redirect(url_for('members'))
    if request.method == 'POST':
        if request.form.get("delete", None) is not None:
            if request.form["delete"] == "1":
                if targetid == "1":
                    flash("Cannot delete root account.")
                    return redirect(url_for('members'))
                remove_user(targetid)
            return redirect(url_for('members'))
        try:
            update_user(targetid, request.form)
        except get_db().IntegrityError:
            flash("Email already in use.")
        else:
            return redirect(url_for('members'))

    session["target_id"] = targetid

    member = get_user_by_id(targetid)
    roles = get_roles()
    return render_template('manage/editMember.html', activeNav="members", member=member, roles=roles)