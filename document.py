from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .db import get_db

bp = Blueprint('document', __name__)

@bp.route('/')
def index():
    docList = []
    #if g.user:
        
    return render_template('index.html', docs=docList, activeNav="index")