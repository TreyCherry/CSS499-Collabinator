from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, 
    send_from_directory,current_app
)
from werkzeug.exceptions import abort

from .db import (
    get_db, check_state, upload_file, get_documents, STATES, get_user_by_id,
    get_doc_by_id, get_filename, set_doc_state, add_alert_by_id, add_alert_by_role,
    get_roles_by_states, remove_document, get_users, add_doc_reviewer, check_doc_reviewer,
    add_comment, get_comments, get_comment, add_response, clear_doc_reviewers,
    get_doc_by_name, get_responses, mark_resolved, add_alert_by_doc_reviewers,
    check_all_resolved, check_new_responses, resolve_all, get_doc_reviewers
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
        if check_state(g.stateint, 2): #if moderator show all docs
            docList = get_documents()
        else:
            docList = get_documents(author_id=g.user["user_id"], min_state_id=3) #if not only show approved docs

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
        docName = upload_file(file, g.user["user_id"]) #upload_file uploads the file to the server and returns true if it succeeds false otherwise
        if docName is not None:
            link = url_for('docs.viewDocument') + "?docID=" + str(get_doc_by_name(docName)["document_id"])
            message = make_alert_message("your_doc_upload", document_name=docName) #create an alert messages
            add_alert_by_id(g.user["user_id"], message, link)

            message = make_alert_message("doc_upload", document_name=docName, user_name=g.user["first_name"]) #create an alert messages
            roles = get_roles_by_states(2) #get the roles that have approve permissions
            for role in roles:
                add_alert_by_role(role["role_id"], message, link)
            flash("Upload successful!")
            return redirect(url_for('index')) #if it uploaded successfully take us back to homepage
        

    return render_template('docview/addDocument.html', activeNav="docs") #render the html page for uploading a document

@bp2.route('/update', methods=('GET', 'POST'))
@login_required
def update():
    docID = request.args.get("docID") #check for docID in the url
    if not check_state(g.stateint, 7) or docID is None or not check_doc_reviewer(docID, g.user["user_id"]):
        if docID is not None: #run checks
            flash("You are not allowed to do that.") #if user doesnt have permission say this
        else:
            flash("No document specified.") #if no document is specified say this
        return redirect(url_for('index'))
    doc = get_doc_by_id(docID)
    docName = doc["document_name"]

    if request.method == 'POST':
        if 'file' not in request.files: #check if file is in request
            flash("No file part.")
            return redirect(request.url)
        file = request.files['file']
        docName = upload_file(file, g.user["user_id"], doc)
        if docName is not None:
            link = url_for('docs.viewDocument') + "?docID=" + str(docID)
            message = make_alert_message("doc_updated", document_name=docName)
            add_alert_by_doc_reviewers(docID, message, link)
            flash("Upload successful!")
            return redirect(link)
    
    return render_template('docview/updateDocument.html', docName=docName, activeNav="docs")

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

@bp2.route('/responses', methods=('GET', 'POST'))
@login_required
def viewResponses():
    if not check_state(g.stateint, 0): #if user does not have read permissions
        return redirect(url_for('index')) #take them back to home page
    commentID = request.args.get("commentID")
    if not commentID:
        return redirect(url_for('index'))
    
    comment = get_comment(commentID)
    docID = comment['document_id']
    doc = get_doc_by_id(docID)
    docstate = doc["state_id"]
    users = get_users()
    link = url_for('docs.viewResponses') + "?commentID=" + commentID

    if request.method == 'POST':
        resolveButton = request.form.get("resolve")
        if resolveButton is not None:
            if comment['resolved'] == 2 or not check_doc_reviewer(docID, g.user['user_id']) or not check_state(g.stateint, 6):
                flash("You are not allowed to do that")
                return redirect(link)
            
            mark_resolved(commentID, 2)
            comtext = "%.10s" % comment['comment']
            if comtext != comment['comment']:
                comtext += "..."
            message = make_alert_message("comment_resolved", first_name=get_user_by_id(comment['author_id'])["first_name"], document_name=doc["document_name"], comment_text=comtext)
            docLink = url_for('docs.viewDocument') + "?docID=" + str(docID)
            add_alert_by_doc_reviewers(docID, message, docLink)
            flash("Comment marked as resolved")

            if check_all_resolved(docID): #if all comments resolved
                set_doc_state(docID, 7) #mark document as all resolved
            elif not check_new_responses(docID): #if otherwise no responses on other comments
                set_doc_state(docID, 5) #mark document as comments to view with no responses

            return redirect(docLink)

        if comment['resolved'] == 2 or not check_doc_reviewer(docID, g.user['user_id']) or not check_state(g.stateint, 5):
            flash("Unable to add response")
            return redirect(link)
        
        response = request.form.get("response")
        if not response or response == "":
            flash("Response cannot be empty")
            return redirect(link)
        
        add_response(commentID, g.user["user_id"], response)
        message = make_alert_message("new_response", user_name=g.user["first_name"], document_name=doc["document_name"])
        
        add_alert_by_doc_reviewers(docID, message, link)

        if comment["resolved"] != 1: #if comment not already marked as replied, mark it
            mark_resolved(commentID, 1)

        if docstate != 6: #update doc to stage 6 if it needs it
            set_doc_state(docID, 6)

        flash("Response submitted")
        return redirect(link)
        
    responses = get_responses(commentID) #get all responses associated with comment for doc rendering

    usernames = {}
    for user in users:
        usernames[str(user["user_id"])] = user["first_name"] + " " + user["last_name"]

    return render_template('docview/responses.html', activeNav="docs", comment=comment, usernames=usernames, responses=responses, docstate=docstate)

@bp2.route('/view', methods=('GET', 'POST')) #this is the actual view site
@login_required
def viewDocument():
    if not check_state(g.stateint, 0): #if user does not have read permissions
        return redirect(url_for('index')) #take them back to home page

    if not request.args.get("docID"): #if docID is in the url
        return redirect(url_for('index')) #if docID is not in the url then take them back to home page
    
    docID = request.args.get("docID")
    doc = get_doc_by_id(docID) #get the document from the database
    if doc is None:
        flash("Document not found")
        return redirect(url_for('index'))
    docstate = doc["state_id"]
    docAuthor = get_user_by_id(doc["author_id"])
    isAuthor = doc["author_id"] == g.user["user_id"]
    filename = get_filename(doc) #get the full filename of the document
    
    if not isAuthor and not check_state(g.stateint, 2) and docstate < 3: #check if document is in review stage
            return redirect(url_for('index')) #if user does not have mark for review role then redirect 
        

    selectedReviewers = get_doc_reviewers(docID)
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
                return redirect(link)
            case "reject":
                if docstate != 2 or not check_state(g.stateint, 2): #if user is approver
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                docName = doc["document_name"]
                reject_doc(doc, docID) #reject the document

                flash(f"Document \"{docName}\" marked as rejected and removed from server.")
                return redirect(url_for('index')) #go back to home page
            case "remove":
                if docstate == 2 or not isAuthor and not check_state(g.stateint, 2): #if user is author or doc approver
                    flash("You do not have permission to do that.")
                    return redirect(link)
                    
                docName = doc["document_name"]
                remove_doc(docID, docName)
                
                flash(f"Document \"{docName}\" successfully removed.")
                return redirect(url_for('index')) #go back to home page
            case "markreview":
                if docstate < 3 or not check_state(g.stateint, 3): #if user is not reviewer
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                mark_doc_review(doc, docID, docstate, link) #mark the document for review

                if len(selectedReviewers) > 0: #check if adding new members or not
                    flash("Document review updated!")
                else:
                    flash("Document review started!")

                return redirect(link)
            case "comment":
                if docstate <= 3 or docstate > 8 or not check_doc_reviewer(docID, g.user["user_id"]) or not check_state(g.stateint, 4): #check user allowed to comment
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
                if not check_state(g.stateint, 8) or not check_doc_reviewer(docID, g.user["user_id"]) or docstate > 8:
                    flash("You do not have permission to do that.")
                    return redirect(link)
                
                close_comments(doc, docID, link)
                
                flash("Comments closed!")
                return redirect(link)
            case "close review for":
                if not check_state(g.stateint, 9) or not check_doc_reviewer(docID, g.user["user_id"]) or docstate == 10:
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

def remove_doc(docID, docName):
    message = make_alert_message("doc_removed", document_name=docName) #create an alert message
    add_alert_by_doc_reviewers(docID, message) #alert the reviewers
    clear_doc_reviewers(docID) #clear any reviewers from the list
    remove_document(docID) #remove the document

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
    message = make_alert_message("new_comment", document_name=doc["document_name"]) #create an alert message
    add_alert_by_doc_reviewers(docID, message, link)
    if docstate != 5:
        set_doc_state(docID, 5) #set the state of the document to comments added

def close_comments(doc, docID, link):
    resolve_all(docID)
    set_doc_state(docID, 9)
    message = make_alert_message("comments_closed", document_name=doc["document_name"])
    add_alert_by_doc_reviewers(docID, message, link)

def close_review(doc, docID, link):
    set_doc_state(docID, 10)
    message = make_alert_message("review_closed", document_name=doc["document_name"])
    add_alert_by_doc_reviewers(docID, message, link)
    clear_doc_reviewers(docID)
