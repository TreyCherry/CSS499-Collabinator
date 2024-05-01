from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from .auth import login_required, manager_login_required
from .db import (
    get_roles, STATES, add_role, get_db, update_role, remove_role
)

bp = Blueprint('roles', __name__, url_prefix='/roles')

@bp.route('', methods=('GET', 'POST'))
@login_required
@manager_login_required
def roles():
    if request.method == 'POST': #if form is submitted
        if request.form.get("delete", None) is not None and request.form["delete"] != "": #if delete button is pressed
            if request.form["delete"] == "1" or request.form["delete"] == "2": #if the target role id is 1 or 2, do not allow deletion
                flash("Cannot delete root role.")
                return redirect(url_for('roles'))
            remove_role(request.form["delete"]) #otherwise delete role
            return redirect(url_for('roles')) #reload roles page

        changelist = request.form.get("changed", None) #get list of changes
        changerows = {} #create dict to store changes by row
        if changelist is None or len(changelist) == 0: #if no changes just reload roles page
            return redirect(url_for('roles'))
        
        for change in changelist.split(","): #changes are stored as "<role id>[-<state id>|d]". 
            if "-" in change: 
                split = change.index('-') #get the split index as the location of the '-' in the string
                rowIndex = change[0:split] #the row index is the number before the '-'
            else:
                rowIndex = change #if the change is stored as just the role id with no - then the name of the role is what changed
            if (rowIndex == "1" and (len(change) != 1 and change[2] != 'd')) or rowIndex == "2": #if the root admin role (1) is being changed in anything but name or description do not allow
                flash("Cannot edit root role.") #role 2 is none role and cannot be changed in any capacity
                continue #continue to next change
            if rowIndex not in changerows: #if the current role does not have a key in the changerows dict yet, make it and set it to an empty dict
                changerows[rowIndex] = {}
            if len(change) == len(rowIndex): #when row index is the same as change, it is a name change
                changerows[rowIndex]["name"] = request.form.get(change) #store the rows name as the new name
                continue #go to next change
            if change[split+1] == 'd': #if the change is the role description
                changerows[rowIndex]["description"] = request.form.get(change) #set the description to the new description
                continue #go to next change
            if "states" not in changerows[rowIndex]: #if states key was not yet made for that row, then initialize it with an empty list
                changerows[rowIndex]["states"] = []
            changerows[rowIndex]["states"].append(int(change[split+1:])) #otherwise add the state id to the list of changed states
        
        for index, changerow in changerows.items(): #get each key, value pair in changerows dict
            if get_role(index) is None:
                continue
            try:
                update_role(index, changerow.get("name", None), changerow.get("states", None), changerow.get("description", None)) #update each role with new values
            except get_db().IntegrityError: #if role name already exists flash error for it
                flash("Role names must be unique.")
        
        return redirect(url_for('roles')) #refresh roles when done

    # if no POST, get roles and display them
    roles = get_roles(type=2, invert=True) # get all roles except none role


    return render_template('manage/roles.html', roles=roles, activeNav="roles", states=STATES) #render template with roles and states passed to it

@bp.route('/add', methods=('GET', 'POST'))
@login_required
@manager_login_required
def addRole():
    if request.method == 'POST': # if form is submitted
        if request.form.get("cancel", None) is not None and request.form["cancel"] == "1": #if cancel button is pressed
            return redirect(url_for('roles')) #go back to roles page

        if request.form.get("role_name", None) is None: #post is set when navigating here from the roles page so just refresh to get rid of it
            return redirect(url_for('roles.addRole'))
        
        if request.form["role_name"] == "": #if role name is empty
            flash("Role name cannot be empty.") #say it cannot be empty and try again
            return redirect(url_for('roles.addRole'))

        states = []
        for i in range(11):
            if request.form.get(str(i), None) is not None: #check which states were selected
                states.append(i) #add it to the list

        try:
            add_role(request.form["role_name"], states, request.form["role_description"]) #add the role with its states set
        except get_db().IntegrityError: #if role name already exists flash error for it
            flash("Role with that name already exists")
        else:
            return redirect(url_for('roles')) #if it was successful go back to roles page
        
    return render_template('manage/addRoles.html', activeNav="roles", states=STATES)
