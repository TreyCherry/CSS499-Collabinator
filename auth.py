import functools

from flask import (
    Blueprint, flash, get_flashed_messages, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash
from werkzeug.exceptions import abort

from .db import (
    check_state, get_role, add_user, get_user_by_email, 
    update_activity, get_user_by_id, new_date, get_db
)

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        error = None

        if not request.form["email"]:
            error = "Email is required"
        elif not request.form["password"]:
            error = "Password is required"
        elif not request.form["first_name"]:
            error = "First name is required"
        elif not request.form["last_name"]:
            error = "Last name is required"

        if error is None:
            try:
                add_user(request.form["email"], request.form["password"], 2, request.form["first_name"], request.form["last_name"], new_date())
            except get_db().IntegrityError:
                error = f"User {request.form['email']} is already registered."
            else:
                return redirect(url_for("auth.login"))
            
        flash(error)

    return render_template("auth/register.html", activeNav="register")

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        error = None
        user = get_user_by_email(email)

        if user is None:
            error = 'Incorrect email.'
        elif not check_password_hash(user['password'], password+user['salt']):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['user_id']
            update_activity(user["user_id"])
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html', activeNav="login")
        
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_user_by_id(user_id)
        if g.user is not None and g.user["role_id"] is not None:
            stateint = get_role(g.user["role_id"])["allowed_states"]
            #global variable is_manager can be used to check if user is a manager
            g.is_manager = check_state(stateint, 10) 

@bp.before_app_request
def check_activity():
    if g.user is not None:
        lastactive = get_user_by_id(g.user["user_id"])['last_active']
        if lastactive is not None and new_date() - lastactive < 1000:
            update_activity(g.user["user_id"])
            return 
        
        session.clear()
        flash("Inactive for more than 10 minutes. Please log in again.")
        return redirect(url_for('auth.login'))

@bp.route('/logout')
def logout():
    messages = get_flashed_messages() #ensure flashed messages are not lost
    session.clear() #clear session to logout user
    for message in messages:
        flash(message) #reflash messages
    flash("Successfully logged out.")
    return redirect(url_for('index')) #return to homepage

def login_required(view): #decorator to require login to access page
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        if g.user["role_id"] is None:
            return redirect(url_for('index'))
        return view(**kwargs)

    return wrapped_view

def manager_login_required(view): #decorator to require manager login to access page
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.is_manager: # only roles with manage users state can view this page
            return abort(403) # abort with 403 forbidden
        return view(**kwargs)
    return wrapped_view