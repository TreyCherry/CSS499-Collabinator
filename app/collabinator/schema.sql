DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Roles;
DROP TABLE IF EXISTS Documents;
DROP TABLE IF EXISTS Comments;
DROP TABLE IF EXISTS Responses;
DROP TABLE IF EXISTS DocRoleStates;
DROP TABLE IF EXISTS DocReviewers;
DROP TABLE IF EXISTS Alerts;

VACUUM;
PRAGMA INTEGRITY_CHECK;
-- reset all tables


CREATE TABLE Roles ( --table of roles
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    allowed_states INTEGER NOT NULL, --stored in db.py as an integer representation of a list of booleans
    role_name TEXT UNIQUE NOT NULL, --name of the role
    description TEXT, --optional role description
    role_type INTEGER NOT NULL -- 0 = root admin, 1 = normal, 2 = none
);

CREATE TABLE Users ( --table of users
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL, --role of the user by id
    email TEXT UNIQUE NOT NULL, --email of the user
    password TEXT NOT NULL, --hashed password with salt
    salt TEXT NOT NULL, --salt for password
    first_name TEXT NOT NULL, --first name of the user
    last_name TEXT NOT NULL, --last name of the user
    date_registered INTEGER NOT NULL, --date the user was registered
    last_active INTEGER, --keeps track of last time user activity was updated
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
);

CREATE TABLE Documents ( --table of document information
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id INTEGER NOT NULL, --current state of the document by state id
    author_id INTEGER NOT NULL, --author of the document by user id
    document_name TEXT UNIQUE NOT NULL, --filename of the document without extension
    document_type INTEGER NOT NULL, -- 0 = txt, 1 = pdf
    date_created INT NOT NULL, --date the document was created
    last_updated INT NOT NULL, --date the document was last updated
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE DocReviewers ( --table of document reviewers
    combo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL, --document the reviewer is for by id
    reviewer_id INTEGER NOT NULL, --reviewer by user id
    FOREIGN KEY (document_id) REFERENCES Documents(document_id),
    FOREIGN KEY (reviewer_id) REFERENCES Users(user_id)
);

CREATE TABLE Comments ( --table of comments on documents
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL, --document the comment is for by id
    author_id INTEGER NOT NULL, --author of the comment by user id
    comment TEXT NOT NULL, --comment text
    resolved INTEGER NOT NULL, -- 2 = resolved, 1 = response, 0 = not resolved
    date_created INT NOT NULL, --date the comment was created
    FOREIGN KEY (document_id) REFERENCES Documents(document_id),
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE Responses ( --table of responses to comments
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER NOT NULL, --comment the response is for by id
    author_id INTEGER NOT NULL, --author of the response by user id
    response TEXT NOT NULL, --response text
    date_created INT NOT NULL, --date the response was created
    FOREIGN KEY (comment_id) REFERENCES Comments(comment_id),
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE Alerts ( --table of alerts
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, --user the alert is for by id
    message TEXT NOT NULL, --message of the alert
    link TEXT, --link attached to alert
    date_created INT NOT NULL, --date the alert was created
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);