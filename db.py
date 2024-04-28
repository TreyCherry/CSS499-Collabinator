import sqlite3

import click
from flask import current_app, g, flash
from werkzeug.security import generate_password_hash, gen_salt
from werkzeug.utils import secure_filename

import comtypes.client #needed for docx conversion

import os

from dataclasses import dataclass
import datetime

# this file is for handling all database operations

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
    State(6, "Resolve", "Responded", "Resolve Comments"),
    State(7, "Upload Update", "Resolved", "Upload Updates to Documents"),
    State(8, "Close Comments", "Comments Closed", "Close Comments"),
    State(9, "Close Review", "Review Closed", "Close Document Review"),
    State(10, "Manage Users", "none", "Manage Users")
]

ALLOWED_EXTENSIONS = {'docx', 'pdf', 'doc', 'rtf', 'ppt', 'pptx', 'txt'} #this constant is used to determine if a file is allowed to be uploaded by its extension

def allowed_file(filename): #checks a string filename for if it is in the allowed_extensions list
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(file, author_id): #handle uploading a file from file input
    if file.filename == '': #if no file is input this will be blank
        flash('No selected file') #set error message and return false
        return False #false returns when failed to upload file, true if succeeds
    if not allowed_file(file.filename): #check if file type is allowed
        flash('File type not allowed')
        return False #if not return false
    filename = secure_filename(file.filename) #secure filename removes potentially dangerous characters

    name, type = get_name_type(filename) #get name and type of file
    if (get_doc_by_name(name) is not None): #check if document already has this name in database
        flash('Document already exists')
        return False
    
    try:
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)) #save the file to the configured folder
    except:
        flash('File could not be saved')
        return False
    
    update_document(name, type, author_id) #update document will add a new document or update an existing one
    return True #file upload succeeded

def get_name_type(filename): #get both name without extension and 2 value file type
    name, ext = filename.rsplit('.', 1) #split filename by last '.'
    if ext == 'txt':
        type = 0 # 0 is txt
    else:
        type = 1 # 1 is pdf
    return name, type #return both

def get_filename(doc): #get file name and type from returned database row of document
    name = doc['document_name']
    type = (doc['document_type'] == 0 and 'txt') or 'pdf'

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

def get_documents(): #get all documents in database
    db = get_db()
    return db.execute(
        'SELECT * FROM Documents ORDER BY last_updated DESC'
    ).fetchall()

def remove_document(id): #remove a document by id
    db = get_db()
    filename = get_filename(get_doc_by_id(id)) #get the filename of the document
    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)) #remove the file from the uploads folder
    db.execute('DELETE FROM Documents WHERE document_id = ?', (id,)) #delete the document reference in the db
    db.commit() #commit the update

def update_document(name, type, author_id): #update document will add a new document or update an existing one
    db = get_db()

    existing = get_doc_by_name(name) #search database to see if any documents already have same name


    if existing is None: #if no document with same name insert new document to database
        query = 'INSERT INTO Documents (document_name, document_type, state_id, author_id, date_created, last_updated) VALUES (?, ?, ?, ?, ?, ?)' 
        values = (name, type, 2, author_id, new_date(), new_date())
    else: #otherwise just update the existing document, replacing the type if necessary
        query = 'UPDATE Documents SET document_type = ?, state_id = ?, author_id = ?, last_updated = ? WHERE document_name = ?'
        values = (type, 7, author_id, new_date(), name)

    db.execute(query, values) #execute query
    db.commit() #commit the update to the database

def set_doc_state(doc_id, state_id): #set the state of a document
    db = get_db()
    query = 'UPDATE Documents SET state_id = ? WHERE document_id = ?'
    db.execute(query, (state_id, doc_id))
    db.commit()

def add_doc_reviewer(doc_id, reviewer_id): #add a reviewer to a document
    if check_doc_reviewer(doc_id, reviewer_id):
        return
    db = get_db()
    db.execute('INSERT INTO DocReviewers (document_id, reviewer_id) VALUES (?, ?)', (doc_id, reviewer_id))
    db.commit()

def check_doc_reviewer(doc_id, reviewer_id): #check if a reviewer is on the list for the document review
    db = get_db()
    return db.execute('SELECT * FROM DocReviewers WHERE document_id = ? AND reviewer_id = ?', (doc_id, reviewer_id)).fetchone() is not None

def get_doc_reviewers(doc_id): #get all reviewers for a document
    db = get_db()
    return db.execute('SELECT reviewer_id FROM DocReviewers WHERE document_id = ?', (doc_id,)).fetchall()

def add_comment(doc_id, author_id, comment):
    db = get_db()
    now = new_date()
    db.execute('INSERT INTO Comments (document_id, author_id, comment, resolved, date_created) VALUES (?, ?, ?, ?, ?)', (doc_id, author_id, comment, 0, now))
    db.commit()

def get_comments(doc_id):
    db = get_db()
    return db.execute('SELECT * FROM Comments WHERE document_id = ? ORDER BY date_created', (doc_id,)).fetchall()

def get_states(stateint): #get a list of allowed states based on stateint
    states = []
    i=0
    while stateint > 0 and i < len(STATES): #repeat until stateint is shifted down to 0 or until there are no more states to check
        if stateint & 1: # bitwise and 1 checks if bit furthest to right is set
            states.append(STATES[i]) #if so append state to list
        stateint = stateint >> 1 #shift bits to the right so that next bit is furthest right
        i += 1 #increment count by 1
    return states #return list of states (the dataclass)

def check_state(stateint, id): #check if a specific state is allowed from a stateint
    try: return bool(stateint >> id & 1) #shift bits to right by id to get index of id to be checked. try statement allows this to be run without knowing if stateint is actually set
    except: return False
    

def make_stateint(ids): #take a list of integer ids for states and make a stateint
    stateint = 0 #start at 0
    for id in ids: #for each id
        stateint += 1 << id #add the bit at index of id to stateint
    return stateint #return final stateint

def flip_states(stateint, ids): #flip the values of the bits of a stateint at the specified ids
    newstates = make_stateint(ids) #make a new stateint out of the specified ids
    return stateint ^ newstates #exclusive or flips the bits specified

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

def date_delta(date):
    oldDate = datetime.datetime(date//100**5, date//100**4%100, date//100**3%100, date//100**2%100, date//100%100, date%100)
    now = datetime.datetime.now() #get current time for comparison
    return now - oldDate #return time difference

def date_concise(date): #return a shortened version of date_format that only specifies based on relative time
    relativeTime = date_delta(date)
    
    if relativeTime.days > 7:
        datepart = relativeTime.days // 7
        i = 4
    elif relativeTime.days > 0:
        datepart = relativeTime.days
        i = 3
    elif relativeTime.seconds > 3600:
        datepart = relativeTime.seconds // 3600
        i = 2
    elif relativeTime.seconds > 60:
        datepart = relativeTime.seconds // 60
        i = 1
    else:
        datepart = relativeTime.seconds
        i = 0

    if i==0 and datepart < 10: #if time difference is less than 10 seconds
        return "Just Now" #say "just now"
    
    timeUnits = ["Second", "Minute", "Hour", "Day", "Week"] #list of time units 

    return f"{datepart} {timeUnits[i]}" + (datepart > 1 and 's' or '') + " ago" #return relative concise time difference



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

@click.command('init-db') #add init_db function as a command to be run in terminal with init-db
def init_db_command():
    #Clear the existing data and create new tables.
    init_db() #run init_db
    click.echo('Initialized the database.') #echo to console that it has initialized the database

def init_app(app): #init_app function to be called in __init__.py to ensure database closes when app shuts down and click command is added
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def get_role(id): #search database for role by id
    db = get_db()
    return db.execute('SELECT * FROM Roles WHERE role_id = ?', (id,)).fetchone() #get one role

def get_user_by_id(id): #search database for user by id
    db = get_db()
    return db.execute('SELECT * FROM Users WHERE user_id = ?', (id,)).fetchone() #get one user

def get_user_by_email(email: str): #search database for user by email
    db = get_db()
    return db.execute('SELECT * FROM Users WHERE email = ?', (email.lower(),)).fetchone() #get one user

def get_users(role=None): #get all users in database
    db = get_db()
    query = 'SELECT * FROM Users' #initial query
    if role is not None:
        query += ' WHERE role_id = ' + str(role) #add where clause
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

def update_activity(user_id): #reset last active time to current time
    if user_id is not None: #if user id is not none
        db = get_db()
        db.execute(
            'UPDATE Users SET last_active = ? WHERE user_id = ?', (new_date(), user_id) #update user with new time
        )
        db.commit() #commit to db

def remove_user(user_id): #remove user by their id
    db = get_db()
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

def convert_to_pdf(input_file):
    file_extension = os.path.splitext(input_file)[1].lower()
    abs_input_file = os.path.abspath(input_file)
    abs_output_file = os.path.splitext(abs_input_file)[0] + '.pdf'

    if file_extension in ['.doc', '.docx', '.rtf']:  # Handle Word and RTF files
        app = comtypes.client.CreateObject('Word.Application')
        doc = app.Documents.Open(abs_input_file)
        doc.SaveAs(abs_output_file, FileFormat=17)  # wdFormatPDF
        doc.Close()
        app.Quit()
    elif file_extension in ['.ppt', '.pptx']:  # Handle PowerPoint files
        app = comtypes.client.CreateObject('PowerPoint.Application')
        presentation = app.Presentations.Open(abs_input_file)
        presentation.SaveAs(abs_output_file, FileFormat=32)  # ppSaveAsPDF
        presentation.Close()
        app.Quit()
    else:
        raise ValueError("Unsupported file type.")

    return abs_output_file