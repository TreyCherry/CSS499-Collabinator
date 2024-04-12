from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash

from .auth import login_required, new_salt
from .db import get_db, check_state

bp = Blueprint('members', __name__, url_prefix='/')

def checkManager():
    db = get_db()
    stateint = db.execute(
        'SELECT allowed_states FROM Roles WHERE role_id = ?', (g.user['role_id'],)
    ).fetchone()["allowed_states"]
    if stateint is not None and not check_state(stateint, 10): # only roles with manage users state can view this page
        abort(403) # abort with 403 forbidden

@bp.route('/members', methods=('GET', 'POST'))
@login_required
def members():
    checkManager()
    if request.method == 'POST':
        session["target_id"] = request.form["user_id"]
        return redirect(url_for('members.editMember'))

    db = get_db()
    members = db.execute(
        'SELECT * FROM Users'
    ).fetchall()
    return render_template('members.html', members=members, activeNav="members")

@bp.route('/members/edit', methods=('GET', 'POST'))
@login_required
def editMember():
    checkManager()
    targetid = session.pop("target_id", None)
    db = get_db()
    if targetid is None or request.method == 'POST':
        if request.form.get("email", None) is None:
            return redirect(url_for('members'))
        collumns = "email = ?, first_name = ?, last_name = ?, role_id = ?"
        role = int(request.form["role_id"])
        if int(targetid) == 1 and role != 1:
            role = 1
            flash("Default admin account role cannot be changed")
        values = [request.form["email"].lower(), request.form["first_name"].title(), request.form["last_name"].title(), role]
        if request.form["password"] != "":
            collumns += ", password = ?, salt = ?"
            salt = new_salt()
            values.append(generate_password_hash(request.form["password"]+salt))
            values.append(salt)
        values.append(targetid)
        query = "UPDATE Users SET " + collumns + " WHERE user_id = ?"
        db.execute(query, tuple(values))
        db.commit()
        return redirect(url_for('members'))

    session["target_id"] = targetid

    member = db.execute(
        'SELECT * FROM Users WHERE user_id = ?', (targetid,)
    ).fetchone()
    roles = db.execute(
        'SELECT role_id, role_name FROM Roles ORDER BY role_type, role_name'
    ).fetchall()
    return render_template('editMember.html', activeNav="members", member=member, roles=roles)