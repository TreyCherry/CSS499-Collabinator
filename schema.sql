DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Roles;
DROP TABLE IF EXISTS States;
DROP TABLE IF EXISTS RoleStates;
DROP TABLE IF EXISTS Documents;
DROP TABLE IF EXISTS Logs;
DROP TABLE IF EXISTS ResetTokens;

CREATE TABLE States (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE Roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id INTEGER NOT NULL,
    role_name TEXT UNIQUE NOT NULL,
    description TEXT,
    FOREIGN KEY (state_id) REFERENCES States(state_id)
);

CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_registered TEXT NOT NULL,
    last_login INTEGER NOT NULL,
    is_active INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
);

CREATE TABLE RoleStates (
    role_state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    state_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id),
    FOREIGN KEY (state_id) REFERENCES States(state_id)
);

CREATE TABLE Documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id INTEGER NOT NULL,
    document_name TEXT UNIQUE NOT NULL,
    document_filename TEXT UNIQUE NOT NULL,
    FOREIGN KEY (state_id) REFERENCES States(state_id)
);

CREATE TABLE Logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    time TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE ResetTokens (
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    expires INTEGER NOT NULL,
    token TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);