from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from .auth import login_required, manager_login_required
from .db import (
    get_roles, STATES, add_role, get_db, update_role, remove_role
)

bp = Blueprint('roles', __name__)

@bp.route('/roles', methods=('GET', 'POST'))
@login_required
@manager_login_required
def roles():
    if request.method == 'POST':
        if request.form.get("delete", None) is not None and request.form["delete"] != "":
            if request.form["delete"] == "1" or request.form["delete"] == "2":
                flash("Cannot delete root role.")
                return redirect(url_for('roles'))
            try:
                remove_role(request.form["delete"])
            except get_db().IntegrityError:
                flash("Role id does not exist.")
            else:
                return redirect(url_for('roles'))

        changelist = request.form.get("changed", None)
        changerows = {}
        if changelist is None or len(changelist) == 0:
            return redirect(url_for('roles'))
        
        for change in changelist.split(","):
            if "-" in change:
                split = change.index('-')
                rowIndex = change[0:split]
            else:
                rowIndex = change
            if (rowIndex == "1" and (len(change) != 1 and change[2] != 'd')) or rowIndex == "2":
                flash("Cannot edit root role.")
                continue
            if rowIndex not in changerows:
                changerows[rowIndex] = {}
            if len(change) == len(rowIndex):
                changerows[rowIndex]["name"] = request.form.get(rowIndex)
                continue
            if change[split+1] == 'd':
                changerows[rowIndex]["description"] = request.form.get(change)
                continue
            if "states" not in changerows[rowIndex]:
                changerows[rowIndex]["states"] = []
            changerows[rowIndex]["states"].append(int(change[split+1:]))
        
        for index, changerow in changerows.items():
            try:
                update_role(index, changerow.get("name", None), changerow.get("states", None), changerow.get("description", None))
            except get_db().IntegrityError:
                flash("Role names must be unique.")
            else:
                return redirect(url_for('roles'))

    roles = get_roles(type=2, invert=True)


    return render_template('manage/roles.html', roles=roles, activeNav="roles", states=STATES)

@bp.route('/roles/add', methods=('GET', 'POST'))
@login_required
@manager_login_required
def addRole():
    if request.method == 'POST':
        if request.form.get("cancel", None) is not None and request.form["cancel"] == "1":
            return redirect(url_for('roles'))

        if request.form.get("role_name", None) is None or request.form["role_name"] == "":
            return redirect(url_for('roles.addRole'))

        states = []
        for i in range(11):
            if request.form.get(str(i), None) is not None:
                states.append(i)

        try:
            add_role(request.form["role_name"], states, request.form["role_description"])
        except get_db().IntegrityError:
            flash("Role with that name already exists")
        else:
            return redirect(url_for('roles'))
        
    return render_template('manage/addRoles.html', activeNav="roles", states=STATES)