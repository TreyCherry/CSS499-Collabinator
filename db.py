import sqlite3

import click
from flask import current_app, g, flash
from werkzeug.security import generate_password_hash, gen_salt

from dataclasses import dataclass
import datetime

@dataclass
class State:
    id: int
    name: str
    description: str

    
# list of states for documents
STATES = [
    State(0, "Read Only", "read document"),
    State(1, "Upload", "upload documents"),
    State(2, "Approve", "approve documents for review"),
    State(3, "Select", "select reviewers"),
    State(4, "Comment", "comment on documents"),
    State(5, "Respond", "respond to comments"),
    State(6, "Resolve", "resolve comments"),
    State(7, "Upload Update", "upload updates to documents"),
    State(8, "Close Comments", "close comments"),
    State(9, "Close Review", "close document review"),
    State(10, "Manage Users", "approve new member requests")
]

def get_states(stateint):
    states = []
    i=0
    while stateint > 0 and i < len(STATES):
        if stateint & 1:
            states.append(STATES[stateint])
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

    from .auth import new_salt, new_date

    email = 'admin@collab.inator'
    password = 'admin'
    salt = new_salt()
    role_id = 1
    first_name = 'Admin'
    last_name = 'Admin'
    date_registered = new_date()

    db.execute(
        'INSERT INTO Users (email, password, salt, role_id, first_name, last_name, date_registered) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (email, generate_password_hash(password+salt), salt, role_id, first_name, last_name, date_registered)
    )
    db.commit()

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

def add_user(email: str, password, salt, role_id, first_name: str, last_name: str, date_registered):
    db = get_db()
    db.execute(
        'INSERT INTO Users (email, password, salt, role_id, first_name, last_name, date_registered) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (email.lower(), generate_password_hash(password+salt), salt, role_id, first_name.title(), last_name.title(), date_registered)
    )
    db.commit()

def update_user(user_id, new_details):
    collumns = "email = ?, first_name = ?, last_name = ?, role_id = ?"
    role = int(new_details["role_id"])
    if int(user_id) == 1 and role != 1:
        role = 1
        flash("Default admin account role cannot be changed")
    values = [new_details["email"].lower(), new_details["first_name"].title(), new_details["last_name"].title(), role]
    if new_details["password"] != "":
        collumns += ", password = ?, salt = ?"
        salt = gen_salt()
        values.append(generate_password_hash(new_details["password"]+salt))
        values.append(salt)
    values.append(user_id)
    db = get_db()
    query = "UPDATE Users SET " + collumns + " WHERE user_id = ?"
    db.execute(query, tuple(values))
    db.commit()

def new_user(user_details):
    if not user_details["email"]:
        error = "Email is required"
    elif not user_details["password"]:
        error = "Password is required"
    elif not user_details["first_name"]:
        error = "First name is required"
    elif not user_details["last_name"]:
        error = "Last name is required"

    salt = gen_salt()

    collumns = "email, password, salt, role_id, first_name, last_name, date_registered"
    collumnVals = [
        user_details["email"].lower(), 
        generate_password_hash(user_details["password"]+salt), 
        salt, 2, user_details["first_name"].title(),  # role_id = 2 (None role)
        user_details["last_name"].title(), new_date()
    ]
    delim = ", "
    values = delim.join(str(val) for val in collumnVals)

    if error is None:
        try:
            db = get_db()
            db.execute(
                'INSERT INTO Users (' + collumns + ') VALUES ' + values
            )
            db.commit()
        except db.IntegrityError:
            error = f"User {user_details['email']} is already registered."
        else:
            return error
    return None

def get_roles(type = None):
    query = 'SELECT * FROM Roles ORDER BY role_type, role_name'
    if type is not None:
        query += ' WHERE role_type = ' + str(type)
    db = get_db()
    return db.execute(query).fetchall()

def update_activity(user_id):
    if user_id is not None:
        db = get_db()
        db.execute(
            'UPDATE Users SET last_active = ? WHERE user_id = ?', (new_date(), user_id)
        )
        db.commit()