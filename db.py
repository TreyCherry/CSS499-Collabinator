import sqlite3

import click
from flask import current_app, g, flash
from werkzeug.security import generate_password_hash, gen_salt
from werkzeug.utils import secure_filename

import os

from dataclasses import dataclass
import datetime

@dataclass
class State:
    id: int
    name: str
    docStage: str
    description: str

    
# list of states for documents
STATES = [
    State(0, "Read", "Read Only", "Read Documents"),
    State(1, "Upload", "Updated", "Upload Documents"),
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

ALLOWED_EXTENSIONS = {'docx', 'pdf', 'doc', 'rtf', 'ppt', 'pptx', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(file, author_id):
    if file.filename == '':
        flash('No selected file')
        return False
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)

        name, type = get_name_type(filename)
        if (get_doc_by_name(name) is not None):
            flash('Document already exists')
            return False
        
        update_document(name, type, author_id)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
    return True

def get_name_type(filename):
    name, ext = filename.rsplit('.', 1)
    if ext == 'txt':
        type = 0
    else:
        type = 1 
    return name, type

def get_filename(doc):
    name = doc['document_name']
    type = (doc['document_type'] == 0 and 'txt') or 'pdf'

    return name + '.' + type

def get_doc_by_name(name):
    db = get_db()
    return db.execute(
        'SELECT * FROM Documents WHERE document_name = ?', (name,)
    ).fetchone()

def get_doc_by_id(id):
    db = get_db()
    return db.execute(
        'SELECT * FROM Documents WHERE document_id = ?', (id,)
    ).fetchone()

def get_documents():
    db = get_db()
    return db.execute(
        'SELECT * FROM Documents ORDER BY document_name'
    ).fetchall()

def update_document(name, type, author_id):
    db = get_db()

    existing = get_doc_by_name(name)


    if existing is None:
        query = 'INSERT INTO Documents (document_name, document_type, state_id, author_id, date_created, last_updated) VALUES (?, ?, ?, ?, ?, ?)'
        values = (name, type, 2, author_id, new_date(), new_date())
    else:
        query = 'UPDATE Documents SET document_type = ?, state_id = ?, author_id = ?, last_updated = ? WHERE document_name = ?'
        values = (type, 7, author_id, new_date(), name)

    db.execute(query, values)
    db.commit()

def get_states(stateint):
    states = []
    i=0
    while stateint > 0 and i < len(STATES):
        if stateint & 1:
            states.append(STATES[i])
        stateint = stateint >> 1
        i += 1
    return states

def check_state(stateint, id):
    return bool(stateint >> id & 1)

def make_stateint(ids):
    stateint = 0
    for id in ids:
        stateint += 1 << id
    return stateint

def flip_states(stateint, ids):
    newstates = make_stateint(ids)
    return stateint ^ newstates

def new_date():
    return int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

def date_format(date):
    components = []
    for _ in range(5):
        components.append(date % 100)
        date = date // 100
    components.append(date)
    components.reverse()
    return "%04d-%02d-%02d %02d:%02d:%02d" % tuple(components)

def date_concise(date):
    newdate = date//100*100
    datestring = date_format(date)
    while newdate > 0 and newdate != date:
        newdate=newdate//100
        datestring = datestring[:-3]
    return datestring

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    if os.path.exists(current_app.config['UPLOAD_FOLDER']):
        for file in os.listdir(current_app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file))

    add_role("Admin", [i for i in range(11)], "Administrator", 0)
    add_role("None", [], "No Role", 2)

    email = 'admin@collab.inator'
    password = 'admin'
    role_id = 1
    first_name = 'Admin'
    last_name = 'Admin'
    date_registered = new_date()

    add_user(email, password, role_id, first_name, last_name, date_registered)

def get_role(id):
    db = get_db()
    return db.execute('SELECT * FROM Roles WHERE role_id = ?', (id,)).fetchone()

@click.command('init-db')
def init_db_command():
    #Clear the existing data and create new tables.
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def get_user_by_id(id):
    db = get_db()
    return db.execute('SELECT * FROM Users WHERE user_id = ?', (id,)).fetchone()

def get_user_by_email(email: str):
    db = get_db()
    return db.execute('SELECT * FROM Users WHERE email = ?', (email.lower(),)).fetchone()

def get_users():
    db = get_db()
    return db.execute('SELECT * FROM Users').fetchall()

def add_user(email: str, password, role_id, first_name: str, last_name: str, date_registered):
    salt = gen_salt(16)
    
    db = get_db()
    db.execute(
        'INSERT INTO Users (email, password, salt, role_id, first_name, last_name, date_registered) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (email.lower(), generate_password_hash(password+salt), salt, role_id, first_name.title(), last_name.title(), date_registered)
    )
    db.commit()

def update_user(user_id, new_details):
    columns = "email = ?, first_name = ?, last_name = ?, role_id = ?"
    role = int(new_details["role_id"])
    if int(user_id) == 1 and role != 1:
        role = 1
        flash("Default admin account role cannot be changed")
    values = [new_details["email"].lower(), new_details["first_name"].title(), new_details["last_name"].title(), role]
    if new_details["password"] != "":
        columns += ", password = ?, salt = ?"
        salt = gen_salt(16)
        values.append(generate_password_hash(new_details["password"]+salt))
        values.append(salt)
    values.append(user_id)
    db = get_db()
    query = "UPDATE Users SET " + columns + " WHERE user_id = ?"
    db.execute(query, tuple(values))
    db.commit()

def get_roles(type = None, invert = False):
    query = 'SELECT * FROM Roles' 
    if type is not None:
        query += ' WHERE '
        if invert:
            query += 'NOT '
        query += 'role_type = ' + str(type)
    query +=  ' ORDER BY role_type, role_name'
    db = get_db()
    return db.execute(query).fetchall()

def update_activity(user_id):
    if user_id is not None:
        db = get_db()
        db.execute(
            'UPDATE Users SET last_active = ? WHERE user_id = ?', (new_date(), user_id)
        )
        db.commit()

def remove_user(user_id):
    db = get_db()
    db.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
    db.commit()

def add_role(name, allowedStates, description, type=1):
    collumns = "role_name, allowed_states, role_type"
    qMarks = "?, ?, ?"
    values = [name.title(), make_stateint(allowedStates), type]
    if description.strip() != "":
        collumns += ", description"
        qMarks += ", ?"
        values.append(description.strip())
    db = get_db()
    db.execute(
        'INSERT INTO Roles (' + collumns + ') VALUES (' + qMarks + ')',
        tuple(values)
    )
    db.commit()

def update_role(id, name=None, states=None, description=None):
    db = get_db()
    
    collums = ""
    values = []
    
    if name is not None:
        collums += "role_name = ?"
        values.append(name)
    if states is not None:
        stateint = db.execute('SELECT allowed_states FROM Roles WHERE role_id = ?', (id,)).fetchone()["allowed_states"]
        if collums != "":
            collums += ", "
        collums += "allowed_states = ?"
        values.append(flip_states(stateint, states))
    if description is not None:
        if collums != "":
            collums += ", "
        collums += "description = ?"
        values.append(description)
    
    if collums == "":
        return False

    values.append(id)

    db.execute(
        'UPDATE Roles SET ' + collums + ' WHERE role_id = ?',
        tuple(values)
    )
    db.commit()

    return True

def remove_role(id):
    db = get_db()

    db.execute('UPDATE Users SET role_id = 2 WHERE role_id = ?', (id,))
    db.commit()

    db.execute('DELETE FROM Roles WHERE role_id = ?', (id,))
    db.commit()