from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, 
    send_from_directory,current_app
)
from werkzeug.exceptions import abort

from . import db

from .db import STATES
from .auth import login_required
from .alerts import make_alert_message
import os

bp = Blueprint('index', __name__) #first blueprint is only for index so it can be routed at root

@bp.route('/') #home page route
def index():
    docList = None #initialize doclist to None for checking in index.html
    authors = {} #set authors to an empty dictionary
    if db.check_state(g.stateint, 0): #check if user has read permissions
        if db.check_state(g.stateint, 2): #if moderator show all docs
            docList = db.get_documents()
        else: #if not only show approved docs
            docList = db.get_documents(author_id=g.user["user_id"], min_state_id=3) #approved docs are those that passed approval (state > 3) or docs the user uploaded themselves

        if docList is not None: #if doclist is not None
            for doc in docList: #store the authors name in a dictionary by their id
                user = db.get_user_by_id(doc["author_id"]) #get author info from db
                authors[str(doc["author_id"])] = user["first_name"] + " " + user["last_name"] #set authors dictionary at key of author id to author's full name
        
    return render_template('index.html', docs=docList, states=STATES, authors=authors, activeNav="index") #render index.html with variables passed to it

bp2 = Blueprint('docs', __name__, url_prefix='/docs') #docs will be url wrapper of every other interface with documents

@bp2.route('/add', methods=('GET', 'POST')) #this will be at /docs/add
@login_required
def addDocument():
    if db.check_state(g.stateint, 1) == False: #if user does not have upload permissions
        return redirect(url_for('index')) #take them back to home page
    
    if request.method == 'POST': #if the form is submitted
        if 'file' not in request.files: #check if file is in request
            flash("No file part.") #if not flash error
            return redirect(request.url)
        file = request.files['file'] #get the file from the request
        docName = db.upload_file(file, g.user["user_id"]) #upload_file uploads the file to the server and returns true if it succeeds false otherwise
        if docName is not None:
            link = url_for('docs.viewDocument') + "?docID=" + str(db.get_doc_by_name(docName)["document_id"])
            message = make_alert_message("your_doc_upload", document_name=docName) #create an alert messages
            db.add_alert_by_id(g.user["user_id"], message, link)

            message = make_alert_message("doc_upload", document_name=docName, user_name=g.user["first_name"]) #create an alert messages
            roles = db.get_roles_by_states(2) #get the roles that have approve permissions
            for role in roles:
                db.add_alert_by_role(role["role_id"], message, link)
            flash("Upload successful!")
            return redirect(url_for('index')) #if it uploaded successfully take us back to homepage
        

    return render_template('docview/addDocument.html', activeNav="docs") #render the html page for uploading a document

@bp2.route('/update', methods=('GET', 'POST'))
@login_required
def update():
    docID = request.args.get("docID") #check for docID in the url
    if not db.check_state(g.stateint, 7) or docID is None or not db.check_doc_reviewer(docID, g.user["user_id"]):
        if docID is not None: #run checks
            flash("You are not allowed to do that.") #if user doesnt have permission say this
        else:
            flash("No document specified.") #if no document is specified say this
        return redirect(url_for('index'))
    doc = db.get_doc_by_id(docID) #get the requested doc
    if doc is None: #if doc doesnt exist then redirect home
        flash("Document not found.")
        return redirect(url_for('index'))
    docName = doc["document_name"] #save doc name

    if request.method == 'POST': #if form submitted
        if 'file' not in request.files: #check if file is in request
            flash("No file part.")
            return redirect(request.url) #if not flash error and refresh
        file = request.files['file'] #get the file
        docName = db.upload_file(file, g.user["user_id"], doc) #upload file returns the name of the doc if it succeeds and returns none if it fails
        if docName is not None: #if doc uploaded successfully
            link = url_for('docs.viewDocument') + "?docID=" + str(docID) #get link to the docment
            message = make_alert_message("doc_updated", document_name=docName) #generate the message for the alert
            db.add_alert_by_doc_reviewers(docID, message, link) #send the alert to doc reviewers
            flash("Upload successful!")
            return redirect(link) #redirect to the document
    
    return render_template('docview/updateDocument.html', docName=docName, activeNav="docs")

@bp2.route('/viewer') #this is used for displaying the file itself. Best to call this in an iframe on another page than to go to it directly
@login_required
def viewer():
    if not db.check_state(g.stateint, 0): #if user does not have read permissions
        abort(403) #abort with 403 forbidden

    filename = request.args["filename"] #get filename from url

    if filename is None: #if no filename
        return "Document not specified." #viewer does not work so just print doc not found

    if not os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)): #if the file does not exist then say so
        return "Document not found."

    type = (filename.rsplit('.', 1)[1] == 'txt' and 'text/plain') or 'application/pdf' #check if file needs to be rendered as text or pdf

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, mimetype=type) #send the file with the specified mimetype

@bp2.route('/responses', methods=('GET', 'POST')) #page for responses to comments
@login_required
def viewResponses():
    if not db.check_state(g.stateint, 0): #if user does not have read permissions
        return redirect(url_for('index')) #take them back to home page
    commentID = request.args.get("commentID") #get the comment id from the url
    if not commentID:
        return redirect(url_for('index')) #if no comment id specified go home
    
    comment = db.get_comment(commentID) #get the comment
    if comment is None: #if comment doesnt actually exist
        flash("Comment not found")
        return redirect(url_for('index')) #go home
    docID = comment['document_id'] #get doc id from comment
    doc = db.get_doc_by_id(docID) #get the doc itself
    if doc is None: #if doc doesnt exist then also return home
        flash("Document not found")
        return redirect(url_for('index'))
    docstate = doc["state_id"] #get doc's current state
    users = db.get_users(excludeHidden=False) #get list of all users (including hidden user for user deleted case)
    link = url_for('docs.viewResponses') + "?commentID=" + commentID #make link for the comment

    if request.method == 'POST': #if the form is submitted
        resolveButton = request.form.get("resolve") #check if the form containing the resolve button was submitted
        if resolveButton is not None: #if the post was from the resolve button
            if comment['resolved'] == 2 or not db.check_doc_reviewer(docID, g.user['user_id']) or not db.check_state(g.stateint, 6):
                flash("You are not allowed to do that") #do not allow this if not allowed
                return redirect(link)
            
            db.mark_resolved(commentID, 2) #mark the comment as resolved
            comtext = "%.10s" % comment['comment'] #get the first 10 characters of the comment
            if comtext != comment['comment']: #if the comment is longer than 10 characters
                comtext += "..." #add ellipses
            message = make_alert_message("comment_resolved", first_name=db.get_user_by_id(comment['author_id'])["first_name"], \
                document_name=doc["document_name"], comment_text=comtext) #generate the message for the alert based on the comment
            docLink = url_for('docs.viewDocument') + "?docID=" + str(docID) #get link to the docment
            db.add_alert_by_doc_reviewers(docID, message, docLink) #send the alert to doc reviewers
            flash("Comment marked as resolved") #flash success

            if db.check_all_resolved(docID): #if all comments resolved
                db.set_doc_state(docID, 7) #mark document as all resolved
            elif not db.check_new_responses(docID): #if otherwise no responses on other comments
                db.set_doc_state(docID, 5) #mark document as comments to view with no responses

            return redirect(docLink)

        #otherwise this form is for adding a response

        if comment['resolved'] == 2 or not db.check_doc_reviewer(docID, g.user['user_id']) or not db.check_state(g.stateint, 5):
            flash("Unable to add response") #do not allow this if not allowed (no perms or comment resolved)
            return redirect(link)
        
        response = request.form.get("response") #get new response being submitted
        if not response or response == "":
            flash("Response cannot be empty") #do not allow empty or nonexistent responses
            return redirect(link)
        
        db.add_response(commentID, g.user["user_id"], response) #add the response
        message = make_alert_message("new_response", user_name=g.user["first_name"], document_name=doc["document_name"]) 
        
        db.add_alert_by_doc_reviewers(docID, message, link) #make an alert for the response to doc reviewers

        if comment["resolved"] != 1: #if comment not already marked as replied, mark it
            db.mark_resolved(commentID, 1)

        if docstate != 6: #update doc to stage 6 if it needs it
            db.set_doc_state(docID, 6)

        flash("Response submitted")
        return redirect(link)
        
    responses = db.get_responses(commentID) #get all responses associated with comment for doc rendering

    usernames = {}
    for user in users:
        usernames[str(user["user_id"])] = user["first_name"] + " " + user["last_name"]

    return render_template('docview/responses.html', activeNav="docs", comment=comment, usernames=usernames, responses=responses, docstate=docstate)

@bp2.route('/view', methods=('GET', 'POST')) #this is the actual view site
@login_required
def viewDocument():
    if not db.check_state(g.stateint, 0): #if user does not have read permissions
        return redirect(url_for('index')) #take them back to home page

    if not request.args.get("docID"): #if docID is in the url
        return redirect(url_for('index')) #if docID is not in the url then take them back to home page
    
    docID = request.args.get("docID")
    doc = db.get_doc_by_id(docID) #get the document from the database
    if doc is None:
        flash("Document not found")
        return redirect(url_for('index'))
    docstate = doc["state_id"]
    docAuthor = db.get_user_by_id(doc["author_id"])
    isAuthor = doc["author_id"] == g.user["user_id"]
    filename = db.get_filename(doc) #get the full filename of the document
    
    if not isAuthor and not db.check_state(g.stateint, 2) and docstate < 3: #check if document is in review stage
            return redirect(url_for('index')) #if user does not have mark for review role then redirect 
        

    selectedReviewers = db.get_doc_reviewers(docID)
    reviewers = None
    roleNames = None
    if docstate >= 3: #if document is at least approved for review
        reviewRoles = db.get_roles_by_states(*range(4,10)) #roles with permissions 4-9
        reviewers = set() #use a set so that there are no duplicates
        roleNames = {} #dictionary where key=roleid and value=users full name
        for reviewRole in reviewRoles: #fill the set and dictionary
            roleId = reviewRole["role_id"]
            roleNames[str(roleId)] = reviewRole["role_name"]
            users = db.get_users(roleId)
            for user in users:
                reviewers.add(user)
    comments = None #initialize to none for doc rendering
    usernames = None
    if docstate > 3: #if doc has had review started
        comments = db.get_comments(docID) #get the comments for the doc
        if comments is not None: #if there are comments
            usernames = {}
            for comment in comments: #get the usernames associated with each comment
                authorUser = db.get_user_by_id(comment["author_id"])
                usernames[str(comment["author_id"])] = authorUser["first_name"] + " " + authorUser["last_name"]

    if request.method == 'POST': #if the form is submitted
        action = request.form.get("action") #get the action from the form
        link=url_for("docs.viewDocument")+"?docID="+docID #link to view the document
        match action: #if the action is approve
            case "approve":
                if docstate != 2 or not db.check_state(g.stateint, 2): #if user is not author and not reviewer
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                approve_doc(doc, docID, docAuthor, link) #approve the document
                
                flash("Document approved!")
                return redirect(link)
            case "reject":
                if docstate != 2 or not db.check_state(g.stateint, 2): #if user is approver
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                docName = doc["document_name"]
                reject_doc(doc, docID) #reject the document

                flash(f"Document \"{docName}\" marked as rejected and removed from server.")
                return redirect(url_for('index')) #go back to home page
            case "remove":
                if docstate == 2 or not isAuthor and not db.check_state(g.stateint, 2): #if user is author or doc approver
                    flash("You do not have permission to do that.")
                    return redirect(link)
                    
                docName = doc["document_name"]
                remove_doc(docID, docName)
                
                flash(f"Document \"{docName}\" successfully removed.")
                return redirect(url_for('index')) #go back to home page
            case "markreview":
                if docstate < 3 or not db.check_state(g.stateint, 3): #if user is not reviewer
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                mark_doc_review(doc, docID, docstate, link) #mark the document for review

                if len(selectedReviewers) > 0: #check if adding new members or not
                    flash("Document review updated!")
                else:
                    flash("Document review started!")

                return redirect(link)
            case "comment":
                if docstate <= 3 or docstate > 8 or not db.check_doc_reviewer(docID, g.user["user_id"]) or not db.check_state(g.stateint, 4): #check user allowed to comment
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
            case "close comments on": #writing it this way is easier for the confirm function
                if not db.check_state(g.stateint, 8) or not db.check_doc_reviewer(docID, g.user["user_id"]) or docstate > 8:
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                close_comments(doc, docID, link)
                
                flash("Comments closed!")
                return redirect(link)
            case "close review for":
                if not db.check_state(g.stateint, 9) or not db.check_doc_reviewer(docID, g.user["user_id"]) or docstate == 10:
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                close_review(doc, docID, link)

                flash("Review closed!")
                return redirect(link)
            case _:
                flash("Invalid action.")
                return redirect(link)

    return render_template('docview/viewDocument.html', activeNav="docs", filename=filename, docstate=docstate, reviewers=reviewers, selectedReviewers=selectedReviewers, roles=roleNames, comments=comments, usernames=usernames) #render the html page with the filename passed to it

def approve_doc(doc, docID, docAuthor, link):
    db.set_doc_state(docID, 3) #set the state of the document to ready to select reviewers
    message = make_alert_message("doc_approved", document_name=doc["document_name"]) #create an alert message
    roles = db.get_roles_by_states(3) #get the roles that have select reviewer permissions
    authorDone = False #initialize to false
    for role in roles: #alert each role
        db.add_alert_by_role(role["role_id"], message, link)
        if docAuthor["role_id"] == role["role_id"]:
            authorDone = True #if author role can select viewers they already received alert
    if not authorDone: #if author hasnt already gotten an alert
        db.add_alert_by_id(doc["author_id"], message, link) #add an alert to the author of the document

def reject_doc(doc, docID):
    docName = doc["document_name"]
    db.remove_document(docID) #remove the document
    message = make_alert_message("doc_rejected", document_name=docName) #create an alert message
    db.add_alert_by_id(doc['author_id'], message) #alert the author

def remove_doc(docID, docName):
    message = make_alert_message("doc_removed", document_name=docName) #create an alert message
    db.add_alert_by_doc_reviewers(docID, message) #alert the reviewers
    db.remove_document(docID) #remove the document

def mark_doc_review(doc, docID, docstate, link):
    userIDs = request.form.getlist("reviewerIDs") #get user ids that were checked
    message = make_alert_message("doc_user_added", document_name=doc["document_name"]) #create an alert message
    for userID in userIDs: #for each user id
        db.add_doc_reviewer(docID, userID) #add the user to the document reviewers
        db.add_alert_by_id(userID, message, link) #alert the user they have been added
    if docstate == 3:
        db.set_doc_state(docID, 4) #set the state of the document to comment ready

def upload_comment(doc, docID, docstate, comment, link): #upload a comment
    db.add_comment(docID, g.user["user_id"], comment) #add comment to database
    message = make_alert_message("new_comment", document_name=doc["document_name"]) #create an alert message
    db.add_alert_by_doc_reviewers(docID, message, link)
    if docstate != 5:
        db.set_doc_state(docID, 5) #set the state of the document to comments added

def close_comments(doc, docID, link): #close comments
    db.resolve_all(docID) #resolve all comments on the doc 
    db.set_doc_state(docID, 9) #move the docstate to comments closed
    message = make_alert_message("comments_closed", document_name=doc["document_name"]) 
    db.add_alert_by_doc_reviewers(docID, message, link) #alert doc reviewers that the comments have been closed

def close_review(doc, docID, link): #close doc review
    db.set_doc_state(docID, 10) #move doc state to 10
    message = make_alert_message("review_closed", document_name=doc["document_name"])
    db.add_alert_by_doc_reviewers(docID, message, link) #alert the doc reviewers
    db.clear_doc_reviewers(docID) #remove all doc reviewers for the document from the review
