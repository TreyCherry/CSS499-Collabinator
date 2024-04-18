from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from .auth import login_required, manager_login_required
from .db import (
    get_db, update_user, get_users, get_user_by_id, get_roles, remove_user
)

bp = Blueprint('members', __name__, url_prefix='/members')



@bp.route('', methods=('GET', 'POST')) #url prefix is already /members so '' means /members
@login_required #decorator to require login to access page
@manager_login_required #decorator to require manager login to access page
def members():
    if request.method == 'POST': #if the form is submitted
        session["target_id"] = request.form["user_id"] #store the target id in session to access on next page
        return redirect(url_for('members.editMember')) #go to members/edit

    members = get_users() #get all users in database
    return render_template('manage/members.html', members=members, activeNav="members") #render members.html with list of users

@bp.route('/edit', methods=('GET', 'POST')) #accessed at /members/edit
@login_required #decorator to require login to access page
@manager_login_required #decorator to require manager login to access page
def editMember():
    targetid = session.pop("target_id", None) #get target id from session
    if targetid is None:
        return redirect(url_for('members')) #if no target was specified go back to members page
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

    session["target_id"] = targetid #put target id back in session in case page is refreshed before form is submitted

    member = get_user_by_id(targetid) # get user by target id
    roles = get_roles() #get all roles
    return render_template('manage/editMember.html', activeNav="members", member=member, roles=roles) 