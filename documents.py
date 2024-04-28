from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, 
    send_from_directory,current_app
)
from werkzeug.exceptions import abort

from .db import (
    get_db, check_state, upload_file, get_documents, STATES, get_user_by_id,
    get_doc_by_id, get_filename, set_doc_state, add_alert_by_id, add_alert_by_role,
    get_roles_by_states, remove_document, get_users, add_doc_reviewer, check_doc_reviewer,
    add_comment, get_doc_reviewers, get_comments
)
from .auth import login_required
from .alerts import make_alert_message
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

@bp2.route('/view', methods=('GET', 'POST')) #this is the actual view site
@login_required
def viewDocument():
    if not check_state(g.stateint, 0): #if user does not have read permissions
        return redirect(url_for('index')) #take them back to home page

    if not request.args.get("docID"): #if docID is in the url
        return redirect(url_for('index')) #if docID is not in the url then take them back to home page
    
    docID = request.args.get("docID")
    doc = get_doc_by_id(docID) #get the document from the database
    docstate = doc["state_id"]
    docAuthor = get_user_by_id(doc["author_id"])
    isAuthor = doc["author_id"] == g.user["user_id"]
    filename = get_filename(doc) #get the full filename of the document
    
    if not isAuthor:
        if not check_state(g.stateint, 2): #check if document is in review stage
            if docstate <= 3 and not check_state(g.stateint, 3): #check if document is in review stage
                return redirect(url_for('index')) #if user does not have mark for review role then redirect 
        
    reviewers = None
    roleNames = None
    if docstate >= 3:
        reviewRoles = get_roles_by_states(*range(4,10)) #roles with permissions 4-9
        reviewers = set()
        roleNames = {}
        for reviewRole in reviewRoles:
            roleId = reviewRole["role_id"]
            roleNames[str(roleId)] = reviewRole["role_name"]
            users = get_users(roleId)
            for user in users:
                reviewers.add(user)
    comments = None
    usernames = None
    if docstate > 3:
        comments = get_comments(docID)
        if comments is not None:
            usernames = {}
            for comment in comments:
                authorUser = get_user_by_id(comment["author_id"])
                usernames[str(comment["author_id"])] = authorUser["first_name"] + " " + authorUser["last_name"]

    if request.method == 'POST': #if the form is submitted
        action = request.form.get("action") #get the action from the form
        link=url_for("docs.viewDocument")+"?docID="+docID #link to view the document
        match action: #if the action is approve
            case "approve":
                if docstate != 2 or not check_state(g.stateint, 2): #if user is not author and not reviewer
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                approve_doc(doc, docID, docAuthor, link) #approve the document
                
                flash("Document approved!")
                return redirect(url_for('index'))
            case "reject":
                if docstate != 2 or not check_state(g.stateint, 2): #if user is approver
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                reject_doc(doc, docID) #reject the document

                flash(f"Document \"{docName}\" marked as rejected and removed from server.")
                return redirect(url_for('index')) #go back to home page
            case "remove":
                if docstate == 2 or not isAuthor and not check_state(g.stateint, 2): #if user is author or doc approver
                    flash("You do not have permission to do that.")
                    return redirect(link)
                    
                docName = doc["document_name"]
                remove_doc(doc, docID, docName)
                
                flash(f"Document \"{docName}\" successfully removed.")
                return redirect(url_for('index')) #go back to home page
            case "update":
                pass
            case "markreview":
                if docstate < 3 or not check_state(g.stateint, 3): #if user is not reviewer
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                mark_doc_review(doc, docID, docstate, link) #mark the document for review

                flash("Document review started!")
                return redirect(url_for('index'))
            case "comment":
                if docstate <= 3 or docstate >= 8 or not check_doc_reviewer(docID, g.user["user_id"]) or not check_state(g.stateint, 4): #if user is not reviewer
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                comment = request.form.get("comment")
                if comment is not None and comment != "":
                    upload_comment(doc, docID, docstate, comment, link) #upload the comment
                else:
                    flash("Comment cannot be empty!")
                    return redirect(link)
                

                flash("Comment added!")
                return redirect(link)
            case _:
                return redirect(link)

    return render_template('docview/viewDocument.html', activeNav="docs", filename=filename, docstate=docstate, reviewers=reviewers, roles=roleNames, comments=comments, usernames=usernames) #render the html page with the filename passed to it

def approve_doc(doc, docID, docAuthor, link):
    set_doc_state(docID, 3) #set the state of the document to ready to select reviewers
    message = make_alert_message("doc_approved", document_name=doc["document_name"]) #create an alert message
    roles = get_roles_by_states(3) #get the roles that have select reviewer permissions
    authorDone = False #initialize to false
    for role in roles: #alert each role
        add_alert_by_role(role["role_id"], message, link)
        if docAuthor["role_id"] == role["role_id"]:
            authorDone = True #if author role can select viewers they already received alert
    if not authorDone: #if author hasnt already gotten an alert
        add_alert_by_id(doc["author_id"], message, link) #add an alert to the author of the document

def reject_doc(doc, docID):
    docName = doc["document_name"]
    remove_document(docID) #remove the document
    message = make_alert_message("doc_rejected", document_name=docName) #create an alert message
    add_alert_by_id(doc['author_id'], message) #alert the author

def remove_doc(doc, docID, docName):
    remove_document(docID) #remove the document
    message = make_alert_message("doc_removed", document_name=docName) #create an alert message
    add_alert_by_id(doc["author_id"], message) #alert the author

def mark_doc_review(doc, docID, docstate, link):
    userIDs = request.form.getlist("reviewerIDs") #get user ids that were checked
    message = make_alert_message("doc_user_added", document_name=doc["document_name"]) #create an alert message
    for userID in userIDs: #for each user id
        add_doc_reviewer(docID, userID) #add the user to the document reviewers
        add_alert_by_id(userID, message, link) #alert the user they have been added
    if docstate == 3:
        set_doc_state(docID, 4) #set the state of the document to comment ready

def upload_comment(doc, docID, docstate, comment, link): #upload a comment
    add_comment(docID, g.user["user_id"], comment) #add comment to database
    reviewers = get_doc_reviewers(docID)
    message = make_alert_message("new_comment", document_name=doc["document_name"]) #create an alert message
    for reviewer in reviewers: #alert all reviewers
        add_alert_by_id(reviewer["reviewer_id"], message, link)
    if docstate == 4:
        set_doc_state(docID, 5) #set the state of the document to comments added