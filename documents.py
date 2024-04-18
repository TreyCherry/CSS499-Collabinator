from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, 
    send_from_directory,current_app
)
from werkzeug.exceptions import abort

from .db import (
    get_db, check_state, upload_file, get_documents, STATES, get_user_by_id,
    get_doc_by_id, get_filename
)
from .auth import login_required

import os

bp = Blueprint('docs', __name__)

@bp.route('/')
def index():
    docList = None
    authors = {}
    if g.stateint and check_state(g.stateint, 0):
        docList = get_documents()
        for doc in docList:
            user = get_user_by_id(doc["author_id"])
            authors[str(doc["author_id"])] = user["first_name"] + " " + user["last_name"]
        
    return render_template('index.html', docs=docList, states=STATES, authors=authors, activeNav="index")

@bp.route('/docs/add', methods=('GET', 'POST'))
@login_required
def addDocument():
    if check_state(g.stateint, 1) == False:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part.")
            return redirect(request.url)
        file = request.files['file']
        if upload_file(file, g.user["user_id"]) == True:
            flash("Upload successful!")
            return redirect(url_for('index'))
        
        

    return render_template('docview/addDocument.html', activeNav="docs")

@bp.route('/viewer')
@login_required
def viewer():
    if request.args.get("filename") is None:
        return "Document not specified."
    
    filename = request.args["filename"]

    if ".txt" in filename:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], request.args.get("filename"), mimetype='text/plain')

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], request.args.get("filename"), mimetype='application/pdf')

@bp.route('/docs/view')
@login_required
def viewDocument():
    if request.args.get("docID"):
        doc = get_doc_by_id(request.args.get("docID"))
        
        filename = get_filename(doc)

        return render_template('docview/viewDocument.html', activeNav="docs", filename=filename)
    
    return redirect(url_for('index'))