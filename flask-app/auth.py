import functools

from flask import (
    Blueprint, flash, get_flashed_messages, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash
from werkzeug.exceptions import abort

from .db import (
    check_state, get_role, add_user, get_user_by_email, 
    update_activity, get_user_by_id, new_date, get_db, date_delta
)

bp = Blueprint('auth', __name__, url_prefix='/auth') #auth is the name of the blueprint

@bp.route('/register', methods=('GET', 'POST')) #register
def register():
    if request.method == 'POST': #if the form is submitted
        error = None

        #check for empty fields
        if not request.form["email"]:
            error = "Email is required"
        elif not request.form["password"]:
            error = "Password is required"
        elif not request.form["first_name"]:
            error = "First name is required"
        elif not request.form["last_name"]:
            error = "Last name is required"

        if error is None: #if no errors
            try: #try to add user
                add_user(request.form["email"], request.form["password"], 2, request.form["first_name"], request.form["last_name"], new_date()) #defined in db.py
            except get_db().IntegrityError: #if email already exists
                error = f"User {request.form['email']} is already registered." #set error message
            else: #in try/except blocks else just runs if no exception 
                flash("Account created successfully. Please log in.")
                #TODO: alert managers
                return redirect(url_for("auth.login")) #redirect to login
            
        flash(error) #flash error message

    return render_template("auth/register.html", activeNav="register") #render register template, NOTE: ActiveNav sets which navbar element is highlighted

@bp.route('/login', methods=('GET', 'POST')) #login
def login():
    if request.method == 'POST': #if the form is submitted
        email = request.form['email'].lower() #email is stored in lowercase
        password = request.form['password'] #password is not stored in lowercase
        error = None 
        user = get_user_by_email(email) #get user info from db table via email

        if user is None: #if no user was found
            error = 'Incorrect email.'
        elif not check_password_hash(user['password'], password+user['salt']): #if password is incorrect
            error = 'Incorrect password.'

        if error is None: #if no errors
            session.clear() #clear session variables
            session['user_id'] = user['user_id'] #set session user_id to user_id from db
            update_activity(user["user_id"]) #update last active time in db
            return redirect(url_for('index')) #redirect to index

        flash(error) #this only runs if there was errors

    return render_template('auth/login.html', activeNav="login") #render login template 
        
@bp.before_app_request #this will load before EACH request, regardless of which page is loaded
def load_logged_in_user(): #set the global user variable if a user is logged in
    user_id = session.get('user_id') #get user_id from session variable (stored in login)

    if user_id is None: #if no user is logged in
        g.user = None #set global user var to None
        g.stateint = None
    else:
        g.user = get_user_by_id(user_id) #if user is logged in store the user info in the global user var
        g.stateint = get_role(g.user["role_id"])["allowed_states"] #store their allowed states in global stateint

    check_activity()

def check_activity(): 
    if g.user is not None: #if user is logged in
        lastactive = get_user_by_id(g.user["user_id"])['last_active'] #get last active time from db
        if lastactive is None:
            return redirect(url_for('auth.logout'))
        timeSince = date_delta(lastactive)
        
        if timeSince.seconds < 600 : #if last active time is less than 10 minutes
            return update_activity(g.user["user_id"]) #update last active time in db to now
        
        session.clear() #otherwise clear session to logout user
        load_logged_in_user()
        flash("Inactive for more than 10 minutes. Please log in again.") #flash message to login again
        return redirect(url_for('auth.login')) #redirect to login

@bp.route('/logout') #logout
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
        if g.user is None: #if no user is logged in
            return redirect(url_for('auth.login')) #redirect to login
        if g.user["role_id"] is None: #if user has no role redirect to index
            return redirect(url_for('index'))
        return view(**kwargs)

    return wrapped_view

def manager_login_required(view): #decorator to require manager login to access page
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not check_state(g.stateint, 10): # only roles with manage users state can view this page
            return abort(403) # abort with 403 forbidden
        return view(**kwargs)
    return wrapped_view