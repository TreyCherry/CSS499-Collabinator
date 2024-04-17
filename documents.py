from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .db import get_db, check_state
from .auth import login_required

bp = Blueprint('docs', __name__)

@bp.route('/')
def index():
    docList = []
    #if g.user:
        
    return render_template('index.html', docs=docList, activeNav="index")

@bp.route('/docs/add', methods=('GET', 'POST'))
@login_required
def addDocument():
    if check_state(g.stateint, 0) == False:
        return redirect(url_for('index'))

    return render_template('docview/addDocument.html', activeNav="docs")