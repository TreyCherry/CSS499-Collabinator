from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from . import db


auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    #login code goes here
    username = request.form.get('InputUsername')
    password = request.form.get('InputPassword')
    #remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=username).first()

    #check if user actually exists
    #take user-supplied password, hash it, comapare to hashed pw in db
    if not user:
        #flash('Please check your login details and try again')
        flash('Bad user')
        return redirect(url_for('auth.login'))
    if not check_password_hash(user.password, password):
        flash('Bad password')
        return redirect(url_for('auth.login'))

    
    #if above check passes, then we know the user has the right credentials
    #login_user(user, remember=remember)
    login_user(user)
    return redirect(url_for('main.profile'))


@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    #code to validate and add user to db goes here
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')


    user = User.query.filter_by(email=email).first() #query db to see if it returns a user, meaning the email is already used

    if user: #redirect to signup to try a different email
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))
    
    #create new user with form data. Hask password
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'))

    #add new user to db
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))