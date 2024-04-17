from flask import (
    Blueprint, render_template, flash, g, redirect, request, url_for
)
from werkzeug.exceptions import abort
from .auth import login_required
from flaskr.db import get_db




main = Blueprint('main', __name__)

#would be nice to have some sort of launch/landing page
#should we set up a user registration page?
@main.route('/')
def landing():
    #return render_template('index.html')
    return render_template('login.html')

@main.route('/settings')
@login_required
def settings():
    #return render_template('settings.html', name=current_user.name)
    return render_template('settings.html', username=current_user.username)