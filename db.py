import sqlite3

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

from dataclasses import dataclass

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



@click.command('init-db')
def init_db_command():
    #Clear the existing data and create new tables.
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)