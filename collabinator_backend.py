from flask import Blueprint, render_template
from flask_login import login_required, current_user
from . import db


main = Blueprint('main', __name__)

#would be nice to have some sort of launch/landing page
#should we set up a user registration page?
@main.route('/')
def index():
    #return render_template('index.html')
    return render_template('login.html')

@main.route('/settings')
@login_required
def profile():
    return render_template('settings.html', name=current_user.name)