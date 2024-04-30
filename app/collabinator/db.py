import sqlite3

import click
from flask import current_app, g, flash
from werkzeug.security import generate_password_hash, gen_salt
from werkzeug.utils import secure_filename


import subprocess

import os
from sys import platform

from dataclasses import dataclass
import datetime

# this file is for handling all database operations
# functions for each table in order of table definition in schema.sql following general db commands at top

@dataclass
class State: #dataclass for storing important information associated with states. 
    id: int
    name: str
    docStage: str
    description: str

    
# list of states for documents and roles
# this is a constant list and only needs to be defined here
# id matches index which is useful for jinja templates
STATES = [
    State(0, "Read", "Read Only", "Read Documents"),
    State(1, "Upload", "Upload", "Upload Documents"),
    State(2, "Approve", "Awaiting Approval", "Approve Documents For Review"),
    State(3, "Select", "Select Reviewers", "Select Reviewers"),
    State(4, "Comment", "Ready for Review", "Comment on Documents"),
    State(5, "Respond", "Comments to View", "Respond to Comments"),
    State(6, "Resolve", "New Responses to Comments", "Resolve Comments"),
    State(7, "Upload Update", "Resolved", "Upload Updates to Documents"),
    State(8, "Close Comments", "Document Updated", "Close Comments"),
    State(9, "Close Review", "Comments Closed", "Close Document Review"),
    State(10, "Manage Users", "Review Closed", "Manage Users")
]

ALLOWED_EXTENSIONS = {'docx', 'pdf', 'doc', 'rtf', 'ppt', 'pptx', 'txt'} #this constant is used to determine if a file is allowed to be uploaded by its extension

#start general section

def get_db(): #get the database connection
    if 'db' not in g: #check if db is already stored
        g.db = sqlite3.connect( #if not connect to it
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row #set row factory to sqlite3 row

    return g.db #return the database connection

def close_db(e=None): #close db
    db = g.pop('db', None) #pop db from global context

    if db is not None: #if db existed
        db.close() #close it

def init_db(): #initialize database to default values, deleting old information if necessary
    db = get_db()

    with current_app.open_resource('schema.sql') as f: #run schema.sql which defines the tables for the database
        db.executescript(f.read().decode('utf8'))

    if os.path.exists(current_app.config['UPLOAD_FOLDER']): #check if file upload folder exists
        for file in os.listdir(current_app.config['UPLOAD_FOLDER']): #if so clear all files in it
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file))

    add_role("Admin", [i for i in range(11)], "Administrator", 0) #add the admin role with all permissions, type 0 is root admin
    add_role("None", [], "No Role", 2) #add none role with no permissions. Type 2 is no role and cannot be seen in role editor

    email = 'admin@collab.inator' #default admin user settings
    password = 'admin'
    role_id = 1 #role 1 is admin
    first_name = 'Admin'
    last_name = 'Admin'
    date_registered = new_date() #get date integer from current time

    add_user(email, password, role_id, first_name, last_name, date_registered) #add admin user to database
    add_user("none", "none", 2, "Deleted User", "", 0) #add hidden user to be displayed when a user is removed

@click.command('init-db') #add init_db function as a command to be run in terminal with init-db
def init_db_command():
    #Clear the existing data and create new tables.
    init_db() #run init_db
    click.echo('Initialized the database.') #echo to console that it has initialized the database

def init_app(app): #init_app function to be called in __init__.py to ensure database closes when app shuts down and click command is added
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command) #add init_db_command as a command line option for the app

#end general section
#start role section

def get_role(id): #search database for role by id
    db = get_db()
    return db.execute('SELECT * FROM Roles WHERE role_id = ?', (id,)).fetchone() #get one role

def get_roles(type = None, invert = False): #get roles, optionally filter by type. Invert is used to change filter from whitelist to blacklist of types
    query = 'SELECT * FROM Roles' #initial query
    if type is not None: #if a type is specified
        query += ' WHERE ' #add where clause
        if invert:
            query += 'NOT ' #if inverted add not
        query += 'role_type = ' + str(type) #add type specification
    query +=  ' ORDER BY role_type, role_name' #order by type first then name
    db = get_db()
    return db.execute(query).fetchall() #get all values that match

def get_roles_by_states(*states): #get roles by allowed states
    allRoles = get_roles() #get all roles
    if allRoles is None:
        return None
    validRoles = [] #initially empty
    for state in states:
        for role in allRoles: #for each role
            if role in validRoles: #do not double add roles
                continue
            if check_state(role["allowed_states"], state): #if role is allowed
                validRoles.append(role) #add role to list
    return validRoles #return list

#end role section
#start user section

def get_user_by_id(id): #search database for user by id
    db = get_db()
    return db.execute('SELECT * FROM Users WHERE user_id = ?', (id,)).fetchone() #get one user

def get_user_by_email(email: str): #search database for user by email
    db = get_db()
    return db.execute('SELECT * FROM Users WHERE email = ?', (email.lower(),)).fetchone() #get one user

def get_users(role=None, excludeHidden=True): #get all users in database
    db = get_db()
    query = 'SELECT * FROM Users' #initial query excluding hidden user
    condition = ''
    if excludeHidden:
        condition = 'user_id != 2' #exclude hidden user
    if role is not None:
        if condition != '':
            condition += ' AND '
        condition += 'role_id = ' + str(role) #add role filter
    
    if condition != '':
        query += ' WHERE ' + condition

    return db.execute(query).fetchall()

def add_user(email: str, password, role_id, first_name: str, last_name: str, date_registered): #add a user to database
    salt = gen_salt(16) #generate random salt for password
    
    db = get_db()
    db.execute( #insert the values into the database
        'INSERT INTO Users (email, password, salt, role_id, first_name, last_name, date_registered) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (email.lower(), generate_password_hash(password+salt), salt, role_id, first_name.title(), last_name.title(), date_registered)
    ) #email should be lower case, names should be title case. password is hashed with salt and salt is stored for checking
    db.commit() #commit to database

def update_user(user_id, new_details): #update a user in database, new_details is a dictionary of values to update
    columns = "email = ?, first_name = ?, last_name = ?, role_id = ?" #initial columns to update
    role = int(new_details["role_id"]) #get role id
    if int(user_id) == 1 and role != 1: #if admin user is being changed and a new role is specified override it and restore value to admin role (1)
        role = 1
        flash("Default admin account role cannot be changed") #flash error of editing root account role
    values = [new_details["email"].lower(), new_details["first_name"].title(), new_details["last_name"].title(), role] #initial values to update
    if new_details["password"] != "": #only change password if new one specified, empty means no change
        columns += ", password = ?, salt = ?" #add password and salt columns
        salt = gen_salt(16) #generate random salt for password
        values.append(generate_password_hash(new_details["password"]+salt)) #password is hashed with salt and salt is stored for checking
        values.append(salt)
    values.append(user_id) #lastly add user id as this is how we know which user to update
    db = get_db()
    query = "UPDATE Users SET " + columns + " WHERE user_id = ?" #update specified columns where user id matches
    db.execute(query, tuple(values)) #execute query
    db.commit() #commit to db

def allowed_file(filename): #checks a string filename for if it is in the allowed_extensions list
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(file, author_id, existingDoc=None): #handle uploading a file from file input
    if file.filename == '': #if no file is input this will be blank
        flash('No selected file') #set error message and return false
        return None #false returns when failed to upload file, true if succeeds
    if not allowed_file(file.filename): #check if file type is allowed
        flash('File type not allowed')
        return None #if not return false
    filename = secure_filename(file.filename) #secure filename removes potentially dangerous characters

    name, type = get_name_type(filename) #get name and type of file
    if (existingDoc != None): #if existingName is set then use it
        name = existingDoc["document_name"] #set name and filename to existing values
        filename = get_filename(existingDoc)
        ext = filename.rsplit('.', 1)[1].lower() #keep new uploaded file name extention for use later
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)) #try to remove the old file that it is replacing
        except:
            flash("Old file failed to remove") #if it fails to remove flash error
        filename = name + '.' + ext #set new filename to be the old name with new extension

    if (existingDoc is None and get_doc_by_name(name) is not None): #check if document already has this name in database and its not supposed to
        flash('Document already exists')
        return None
    
    #enter filetype conversion here. File has been uploaded and type checked. We know it's an accepted type and we know if it already exists. Now see if it needs to be converted
    #if not type == "txt" or not type == "pdf":


    try:
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)) #save the unconverted file to the configured folder
    except:
        flash('File could not be saved') #flash error if fail
        return None
    
    if type == 2: #file needs to be converted. use libreoffice to do so
        outroute = current_app.config['UPLOAD_FOLDER'] #format file output path string
        fileroute = os.path.join(current_app.config['UPLOAD_FOLDER'], filename) #format file input path string. Libreoffice needs a path to the unconverted file
        try:
            subprocess.run(f'export HOME=/tmp && libreoffice --headless --convert-to pdf:writer_pdf_Export {fileroute} --outdir {outroute}', shell=True) #run linux terminal command to convert file
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)) #delete unconverted file as it is no longer needed
            except:
                flash("Old file failed to remove") #if it fails to remove flash error
        except:
            flash('File could not be converted') #flash error if fail and quit
            return None
    
    if (existingDoc is None):
        update_document(name, type, author_id) #update document will add a new document or update an existing one
    else:
        update_document(name, type, author_id, existingDoc["document_id"], existingDoc["state_id"]) #update document will add a new document or update an existing one
    return name #file upload succeeded

def get_name_type(filename): #get both name without extension and 2 value file type
    name, ext = filename.rsplit('.', 1) #split filename by last '.'
    if ext == 'txt':
        type = 0 # 0 is txt
    elif ext == 'pdf':
        type = 1 # 1 is pdf
    else:
        type = 2 # 2 is other extension
    return name, type #return both

def get_filename(doc): #get file name and type from returned database row of document
    name = doc['document_name']
    type = (doc['document_type'] == 0 and 'txt') or 'pdf' #type extension is txt for 0 and pdf for 1 or 2

    return name + '.' + type #return it in usual format

def get_doc_by_name(name): #search database for document by name
    db = get_db()
    return db.execute(
        'SELECT * FROM Documents WHERE document_name = ?', (name,)
    ).fetchone() #return one result

def get_doc_by_id(id): #search database for document by id
    db = get_db()
    return db.execute(
        'SELECT * FROM Documents WHERE document_id = ?', (id,)
    ).fetchone() #return one result

def get_documents(author_id = None, min_state_id = None): #get all documents in database with optional filters
    query = 'SELECT * FROM Documents' #initial query
    addon = "" #empty addon for filtering
    if min_state_id is not None: #if a min state id is specified
        addon = 'state_id >= ' + str(min_state_id) #specify state id must be at least min state
    if author_id is not None: #if an author id is specified
        if addon != "": #check if previous filter set already
            addon += " OR " #if so add OR, as the filters are a whitelist if set (min state id or author of document)
        addon += 'author_id = ' + str(author_id) #add clause for user id
    if addon != "": #check if filter set
        query += ' WHERE ' #add where clause
        query += addon #add filter
    query += ' ORDER BY last_updated DESC' #order by last updated
    db = get_db()
    return db.execute(query).fetchall() #get all documents that match

def remove_document(id): #remove a document by id
    db = get_db()
    filename = get_filename(get_doc_by_id(id)) #get the filename of the document
    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)) #remove the file from the uploads folder
    except:
        flash("Could not find file to remove")
    clear_comments(id) #clear comments on doc (this also clears responses on the comments)
    clear_doc_reviewers(id) #clear doc reviewers
    db.execute('DELETE FROM Documents WHERE document_id = ?', (id,)) #delete the document reference in the db
    db.commit() #commit the update

def update_document(name, type, author_id, docID=None, docstate=0): #update document will add a new document or update an existing one
    db = get_db()

    if docID is None and get_doc_by_name(name) is not None: #search database to see if any documents already have same name
        return #docID being set is the trigger for allowing this to continue even if matching name
    

    if docID is None: #if not updating existing doc, insert new doc info to db
        query = 'INSERT INTO Documents (document_name, document_type, state_id, author_id, date_created, last_updated) VALUES (?, ?, ?, ?, ?, ?)' 
        values = (name, type, 2, author_id, new_date(), new_date())
    else: #otherwise just update the existing document, replacing the doc type with the new files doc type
        if docstate < 9: #if document state is not "comments closed"
            docstate = 8 #set document state to "new update" 
        query = 'UPDATE Documents SET document_name = ?, document_type = ?, state_id = ?, author_id = ?, last_updated = ? WHERE document_id = ?'
        values = (name, type, docstate, author_id, new_date(), docID)

    db.execute(query, values) #execute query
    db.commit() #commit the update to the database

def set_doc_state(doc_id, state_id): #set the state of a document
    db = get_db()
    query = 'UPDATE Documents SET state_id = ? WHERE document_id = ?'
    db.execute(query, (state_id, doc_id))
    db.commit()

def add_doc_reviewer(doc_id, reviewer_id): #add a reviewer to a document
    if check_doc_reviewer(doc_id, reviewer_id): #do not add reviewer if already on list
        return
    db = get_db()
    db.execute('INSERT INTO DocReviewers (document_id, reviewer_id) VALUES (?, ?)', (doc_id, reviewer_id))
    db.commit()

def check_doc_reviewer(doc_id, reviewer_id): #check if a reviewer is on the list for the document review (boolean)
    db = get_db()
    return db.execute('SELECT * FROM DocReviewers WHERE document_id = ? AND reviewer_id = ?', (doc_id, reviewer_id)).fetchone() is not None

def get_doc_reviewers(doc_id): #get all reviewers for a document
    db = get_db()
    return db.execute('SELECT * FROM DocReviewers WHERE document_id = ?', (doc_id,)).fetchall()

def clear_doc_reviewers(doc_id): #clear all reviewers for a document
    db = get_db()
    db.execute('DELETE FROM DocReviewers WHERE document_id = ?', (doc_id,))
    db.commit()

def add_comment(doc_id, author_id, comment): #add a new comment to a document
    db = get_db()
    now = new_date()
    db.execute('INSERT INTO Comments (document_id, author_id, comment, resolved, date_created) VALUES (?, ?, ?, ?, ?)', (doc_id, author_id, comment, 0, now))
    db.commit()

def get_comments(doc_id, resolved=None): #get all comments on document
    db = get_db()
    query = 'SELECT * FROM Comments WHERE document_id = ?'
    values = [doc_id]
    if resolved is not None: #optional filter for resolved level (0 = not resolved, 1 = responses added, 2 = resolved)
        query += ' AND resolved = ?'
        values.append(resolved)
    query += ' ORDER BY date_created'
    return db.execute(query, tuple(values)).fetchall()

def check_new_responses(doc_id): #check if there are any new responses to any comments on doc
    comments = get_comments(doc_id, resolved=1) #get comments with responses
    return len(comments) > 0 #if list is non zero, there are new responses

def get_comment(comment_id): #get a comment by its comment id
    db = get_db()
    return db.execute('SELECT * FROM Comments WHERE comment_id = ?', (comment_id,)).fetchone()

def clear_comments(doc_id): #clear all comments on a document
    db = get_db()
    clear_responses(db, doc_id) #clear comment's responses first
    db.execute('DELETE FROM Comments WHERE document_id = ?', (doc_id,))
    db.commit()

def clear_responses(db, doc_id): #clear all responses to a comment
    comments = get_comments(doc_id) #get all comments for doc
    for comment in comments: #for each comment
        comment_id = comment['comment_id'] 
        db.execute('DELETE FROM Responses WHERE comment_id = ?', (comment_id,)) #delete the responses that match the comment id
        db.commit()

def add_response(comment_id, author_id, response): #add a new response to comment
    db = get_db()
    now = new_date()
    db.execute('INSERT INTO Responses (comment_id, author_id, response, date_created) VALUES (?, ?, ?, ?)', (comment_id, author_id, response, now))
    db.commit()

def get_responses(comment_id): #get all responses to a comment
    db = get_db()
    return db.execute('SELECT * FROM Responses WHERE comment_id = ? ORDER BY date_created', (comment_id,)).fetchall()

def mark_resolved(comment_id, resolved): #mark a comment as resolved
    db = get_db()
    db.execute('UPDATE Comments SET resolved = ? WHERE comment_id = ?', (resolved, comment_id))
    db.commit()
    
def check_all_resolved(doc_id): #check if all comments on a document are resolved (boolean)
    db = get_db()
    return db.execute('SELECT * FROM Comments WHERE document_id = ? AND resolved < 2', (doc_id,)).fetchone() is None

def resolve_all(doc_id): #mark all comments on a document as resolved
    db = get_db()
    db.execute('UPDATE Comments SET resolved = 2 WHERE document_id = ?', (doc_id,))
    db.commit()

def get_states(stateint): #get a list of allowed states based on stateint
    states = []
    i=0
    while stateint > 0 and i < len(STATES): #repeat until stateint is shifted down to 0 (no more bits to check) or until there are no more states to check
        if stateint & 1: # bitwise & 1 checks if bit furthest to right is set
            states.append(STATES[i]) #if bit is set, append state with id equal to current index to list
        stateint = stateint >> 1 #shift bits to the right by one so that next bit is furthest right to check again
        i += 1 #increment index tracker by 1
    return states #return list of states (the dataclass)

def check_state(stateint, id): #check if a specific state is allowed from a stateint
    try: return bool(stateint >> id & 1) #shift bits to right by id to get index of id to be checked then & 1 checks if bit is set
    except: return False #if stateint is none then also return false
    

def make_stateint(ids): #take a list of integer state ids and make a stateint for storage in db
    stateint = 0 #start at 0
    for id in ids: #for each id in list
        stateint += 1 << id #add the bit at index of id to stateint
    return stateint #return final stateint

def flip_states(stateint, ids): #flip the values of the bits of a stateint at the specified ids
    newstates = make_stateint(ids) #make a new stateint out of the specified ids
    return stateint ^ newstates #bitwise exclusive or flips the bits at the specified indexes by id

def new_date(): #return a new date in the format YYYYMMDDHHMMSS as an integer
    return int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

def date_format(date): #take a formatted date integer and return a readable string with format "YYYY-MM-DD HH:MM:SS"
    components = []
    for _ in range(5):
        components.append(date % 100) #mod 100 gets the last two digits and stores it
        date = date // 100 #set date int to get rid of last two digits
    components.append(date) #add the last four digits for the year
    components.reverse() #reverse the list so that it is in the correct order
    return "%04d-%02d-%02d %02d:%02d:%02d" % tuple(components) #return formatted string

def date_delta(date): #get the difference in time between now and specified date as a deltatime object
    oldDate = datetime.datetime(date//100**5, date//100**4%100, date//100**3%100, date//100**2%100, date//100%100, date%100) #convert old date int to datetime object
    now = datetime.datetime.now() #get current time for comparison
    return now - oldDate #return datetime difference

def date_concise(date): #return a shortened version of date_format that only specifies based on relative time
    relativeTime = date_delta(date) #get the datetime difference
    
    if relativeTime.days > 7: #if time difference is > 1 week
        datepart = relativeTime.days // 7 #get number of weeks it has been since date
        i = 4 #set time unit to weeks
    elif relativeTime.days > 0: #if time difference > 1 day
        datepart = relativeTime.days #get number of days since date
        i = 3 #set time unit to days
    elif relativeTime.seconds > 3600: #if time difference > 1 hour
        datepart = relativeTime.seconds // 3600 #get number of hours since date
        i = 2 #set time unit to hours
    elif relativeTime.seconds > 60: #if time difference > 1 minute
        datepart = relativeTime.seconds // 60 #get number of minutes
        i = 1 #set time unit to minutes
    else: #otherwise seconds
        datepart = relativeTime.seconds
        i = 0

    if i==0 and datepart < 10: #if time difference is less than 10 seconds
        return "Just Now" #say "just now"
    
    timeUnits = ["Second", "Minute", "Hour", "Day", "Week"] #list of time units 

    return f"{datepart} {timeUnits[i]}" + (datepart > 1 and 's' or '') + " ago" #return relative concise time difference






def update_activity(user_id): #reset last active time to current time
    if user_id is not None: #if user id is not none
        db = get_db()
        db.execute(
            'UPDATE Users SET last_active = ? WHERE user_id = ?', (new_date(), user_id) #update user with new time
        )
        db.commit() #commit to db

def remove_user(user_id): #remove user by their id
    db = get_db()
    db.execute('UPDATE Responses SET author_id = 2 WHERE author_id = ?', (user_id,)) #set all responses by this user to be by deleted user
    db.execute('UPDATE Comments SET author_id = 2 WHERE author_id = ?', (user_id,)) #set all comments by this user to be by deleted user
    db.execute('UPDATE Documents SET author_id = 2 WHERE author_id = ?', (user_id,)) #set all documents by this user to be by deleted user
    db.execute('DELETE FROM DocReviewers WHERE reviewer_id = ?', (user_id,)) #delete all keys in docReviewers
    db.execute('DELETE FROM Users WHERE user_id = ?', (user_id,)) #delete user
    db.commit() #commit to db

def add_role(name, allowedStates, description, type=1): #add a new role to database
    columns = "role_name, allowed_states, role_type" #initial collumns
    qMarks = "?, ?, ?" #initial number of question marks
    values = [name.title(), make_stateint(allowedStates), type] #initial values
    if description.strip() != "": #if description is not empty when stripped of whitespace
        columns += ", description" #add description column
        qMarks += ", ?" #add extra question mark for inserting extra value
        values.append(description.strip()) #add description to values
    db = get_db()
    db.execute(
        'INSERT INTO Roles (' + columns + ') VALUES (' + qMarks + ')',
        tuple(values) #insert new role into database
    )
    db.commit() #commit to db

def update_role(id, name=None, states=None, description=None): #update role by id, name and description are both strings, states is a list of int ids
    db = get_db()
    
    columns = "" #initially empty
    values = []
    
    if name is not None: #check each value to see if it needs to be updated
        columns += "role_name = ?"
        values.append(name)
    if states is not None:
        stateint = db.execute('SELECT allowed_states FROM Roles WHERE role_id = ?', (id,)).fetchone()["allowed_states"]
        if columns != "":
            columns += ", " #only add comma if something came before it
        columns += "allowed_states = ?"
        values.append(flip_states(stateint, states)) #get new stateint by flipping values of all states marked as changed
    if description is not None:
        if columns != "":
            columns += ", "
        columns += "description = ?"
        values.append(description)
    
    if columns == "": #if nothing was updated
        return False #return false

    values.append(id) #add role id to values for where clause

    db.execute(
        'UPDATE Roles SET ' + columns + ' WHERE role_id = ?', #update user with new values
        tuple(values)
    )
    db.commit()

    return True #return true if succeeded

def remove_role(id): #remove role by id
    db = get_db()

    db.execute('UPDATE Users SET role_id = 2 WHERE role_id = ?', (id,)) #first make sure all users with this role are changed to no role (role 2)
    db.commit()

    db.execute('DELETE FROM Roles WHERE role_id = ?', (id,)) #then delete the role
    db.commit()
    
    #alerts.py functions 
    

def get_alerts_by_id(id):
    db = get_db()
    return db.execute(
        'SELECT * FROM Alerts WHERE user_id = ? ORDER BY date_created DESC', (id,)
    ).fetchall()

def add_alert_by_id(for_user, message, link=None):
    columns = "user_id, message, date_created"
    qmarks = "?, ?, ?"
    values = [for_user, message, new_date()]
    if link is not None:
        columns += ", link"
        qmarks += ", ?"
        values.append(link)

    db = get_db()
    db.execute(
        'INSERT INTO Alerts (' + columns + ') VALUES (' + qmarks + ')',
        tuple(values)
    )
    db.commit()

def add_alert_by_role(role_id, message, link=None):
    users = get_users(role_id)
    for user in users:
        add_alert_by_id(user["user_id"], message, link)

def add_alert_by_doc_reviewers(docID, message, link=None):
    reviewers = get_doc_reviewers(docID)
    for reviewer in reviewers:
        add_alert_by_id(reviewer["reviewer_id"], message, link)

