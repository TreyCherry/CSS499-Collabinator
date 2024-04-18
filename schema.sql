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

CREATE TABLE Roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    allowed_states INTEGER NOT NULL,
    role_name TEXT UNIQUE NOT NULL,
    description TEXT,
    role_type INTEGER NOT NULL
);

CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_registered INTEGER NOT NULL,
    last_active INTEGER,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
);

CREATE TABLE Documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    document_name TEXT UNIQUE NOT NULL,
    document_type INTEGER NOT NULL,
    date_created INT NOT NULL,
    last_updated INT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE Comments (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    date_created INT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES Documents(document_id),
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE Responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    response TEXT NOT NULL,
    resolved INTEGER NOT NULL,
    date_created INT NOT NULL,
    FOREIGN KEY (comment_id) REFERENCES Comments(comment_id),
    FOREIGN KEY (author_id) REFERENCES Users(user_id)
);

CREATE TABLE DocReviewers (
    combo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    FOREIGN KEY (document_id) REFERENCES Documents(document_id),
    FOREIGN KEY (reviewer_id) REFERENCES Users(user_id)
);

CREATE TABLE Alerts (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    link TEXT NOT NULL,
    time INT NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);