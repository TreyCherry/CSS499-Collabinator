import functools
import datetime
import random

from flask import (
    Blueprint, flash, get_flashed_messages, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

bp = Blueprint('auth', __name__, url_prefix='/auth')

def new_salt():
    chars=[]
    for _ in range(16):
        chars.append(random.choice(ALPHABET))
    return "".join(chars)

def new_date():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date_registered = new_date()

        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not first_name:
            error = 'First name is required.'
        elif not last_name:
            error = 'Last name is required.'

        salt = new_salt()

        collumns = "email, password, salt, first_name, last_name, date_registered"
        collumnVals = [
            email, generate_password_hash(password+salt), 
            salt, first_name, last_name, date_registered
        ]

        valueStr = "?, ?, ?, ?, ?, ?"

        if error is None:
            try:
                db.execute(
                    "INSERT INTO Users (" + collumns + ") VALUES (" + valueStr + ")",
                    tuple(collumnVals)
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {email} is already registered."
            else:
                return redirect(url_for("auth.login"))
            
        flash(error)

    return render_template("auth/register.html", activeNav="register")

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT user_id, email, password, salt FROM Users WHERE email = ?', (email,)
        ).fetchone()

        if user is None:
            error = 'Incorrect email.'
        elif not check_password_hash(user['password'], password+user['salt']):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['user_id']
            update_activity(user)
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html', activeNav="login")

def update_activity(user):
    if user is not None:
        db = get_db()
        db.execute(
            'UPDATE Users SET last_active = ? WHERE user_id = ?', (int(new_date()), user['user_id'])
        )
        db.commit()
        
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM Users WHERE user_id = ?', (user_id,)
        ).fetchone()

@bp.before_app_request
def check_activity():
    if g.user is not None:
        db = get_db()
        query = db.execute(
            'SELECT last_active FROM Users WHERE user_id = ?', (g.user['user_id'],)
        ).fetchone()
        if int(new_date()) - query['last_active'] < 1000:
            update_activity(g.user)
            return 
        
        session.clear()
        flash("Inactive for more than 10 minutes. Please log in again.")
        return redirect(url_for('auth.login'))

@bp.route('/logout')
def logout():
    messages = get_flashed_messages()
    session.clear()
    for message in messages:
        flash(message)
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view