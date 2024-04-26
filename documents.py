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

bp = Blueprint('index', __name__) #first blueprint is only for index so it can be routed at root

@bp.route('/') #home page route
def index():
    docList = None #initialize doclist to None for checking in index.html
    authors = {} #set authors to an empty dictionary
    if check_state(g.stateint, 0): #check if user has read permissions
        docList = get_documents()
        if docList is not None:
            for doc in docList:
                user = get_user_by_id(doc["author_id"]) #get author info from db
                authors[str(doc["author_id"])] = user["first_name"] + " " + user["last_name"] #set authors dictionary at key of author id to author's full name
        
    return render_template('index.html', docs=docList, states=STATES, authors=authors, activeNav="index") #render index.html with variables passed to it

bp2 = Blueprint('docs', __name__, url_prefix='/docs') #docs will be url wrapper of every other interface with documents

@bp2.route('/add', methods=('GET', 'POST')) #this will be at /docs/add
@login_required
def addDocument():
    if check_state(g.stateint, 1) == False: #if user does not have upload permissions
        return redirect(url_for('index')) #take them back to home page
    
    if request.method == 'POST': #if the form is submitted
        if 'file' not in request.files: #check if file is in request
            flash("No file part.") #if not flash error
            return redirect(request.url)
        file = request.files['file'] #get the file from the request
        if upload_file(file, g.user["user_id"]): #upload_file uploads the file to the server and returns true if it succeeds false otherwise
            flash("Upload successful!")
            return redirect(url_for('index')) #if it uploaded successfully take us back to homepage
        
        

    return render_template('docview/addDocument.html', activeNav="docs") #render the html page for uploading a document

@bp2.route('/viewer') #this is used for displaying the file itself. Best to call this in an iframe on another page than to go to it directly
@login_required
def viewer():
    if not check_state(g.stateint, 0): #if user does not have read permissions
        abort(403) #abort with 403 forbidden

    if request.args.get("filename") is None:
        return "Document not specified." #viewer does not work without specified filename
    
    filename = request.args["filename"] #get filename from url

    if not os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)): #if the file does not exist then say so
        return "Document not found."

    type = (filename.rsplit('.', 1)[1] == 'txt' and 'text/plain') or 'application/pdf' #check if file needs to be rendered as a pdf or txt

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], request.args.get("filename"), mimetype=type) #send the file with the specified mimetype

@bp2.route('/view')
@login_required
def viewDocument():
    if not check_state(g.stateint, 0): #if user does not have read permissions
        return redirect(url_for('index')) #take them back to home page

    if request.args.get("docID"): #if docID is in the url
        doc = get_doc_by_id(request.args.get("docID")) #get the document from the database
        docstate = doc["state_id"]
        if docstate == 2 and not check_state(g.stateint, 2): #check if document is in review stage
            return redirect(url_for('index')) #if user does not have mark for review role then redirect 
        
        filename = get_filename(doc) #get the full filename of the document

        return render_template('docview/viewDocument.html', activeNav="docs", filename=filename, docstate=docstate) #render the html page with the filename passed to it
    
    return redirect(url_for('index')) #if docID is not in the url then take them back to home page