# functionbundles.py

import hashlib # For hashing passwords
import sqlite3
import os
from database import DatabaseInterface # assuming db and db_interface are the names of the database and the database interface objects respectively

# Comment Management
class CommentManager:
    def __init__(self, db):
        self.db = db

    def add_comment(self, doc_id, commenter_id, parent_id, comment_text, comment_time, closed):
        query = '''INSERT INTO Comment(doc_id, commenter_id, parent_id, comment_text, comment_time, closed)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        self.db.execute_query(query, (doc_id, commenter_id, parent_id, comment_text, comment_time, closed))

    def edit_comment(self, comment_id, new_text): # Assuming new_text is the new comment text
        query = '''UPDATE Comment SET comment_text = ? WHERE comment_id = ?'''
        self.db.execute_query(query, (new_text, comment_id))

    def resolve_comment(self, comment_id): 
        query = '''UPDATE Comment SET closed = 1 WHERE comment_id = ?'''
        self.db.execute_query(query, (comment_id,))

    def delete_comment(self, comment_id): 
        query = '''DELETE FROM Comment WHERE comment_id = ?'''
        self.db.execute_query(query, (comment_id,))



# Role and Permission Management.     
class RolePermissionManager: 
    def __init__(self, db_interface):
        self.db_interface = db_interface

    def create_role(self, role_name, permissions):
        query = '''INSERT INTO Role(role_name, upload, approved, select_reviewers, read_only, comment, respond, resolved, upload_update, close_comment, close_review, is_admin)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        self.db_interface.execute_query(query, (
            role_name, 
            permissions['upload'], permissions['approved'], permissions['select_reviewers'], 
            permissions['read_only'], permissions['comment'], permissions['respond'], 
            permissions['resolved'], permissions['upload_update'], permissions['close_comment'], 
            permissions['close_review'], permissions['is_admin']
        ))

    def update_role_permissions(self, role_id, new_permissions):
        query = '''UPDATE Role SET      
                   upload = ?, approved = ?, select_reviewers = ?, read_only = ?, comment = ?, 
                   respond = ?, resolved = ?, upload_update = ?, close_comment = ?, 
                   close_review = ?, is_admin = ?
                   WHERE role_id = ?'''
        self.db_interface.execute_query(query, ( # Assuming new_permissions is a dict
            new_permissions['upload'], new_permissions['approved'], new_permissions['select_reviewers'], 
            new_permissions['read_only'], new_permissions['comment'], new_permissions['respond'], 
            new_permissions['resolved'], new_permissions['upload_update'], new_permissions['close_comment'], 
            new_permissions['close_review'], new_permissions['is_admin'],
            role_id 
        ))

    def assign_role_to_user(self, user_id, role_id):
        query = '''UPDATE Employee SET employee_role = ? WHERE employee_id = ?'''
        self.db_interface.execute_query(query, (role_id, user_id))


# User Management
class UserManager:
    def __init__(self, db_interface):
        self.db_interface = db_interface

    def hash_password(self, password): 
        salt = os.urandom(16) # Generate a random 16-byte salt
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000) # Hash the password
        return salt + pwdhash

    def add_user(self, username, password, first_name, last_name, role_id):
        hashed_password = self.hash_password(password)
        query = '''INSERT INTO Employee(employee_username, employee_hash, employee_first_name, employee_last_name, employee_role)
                   VALUES (?, ?, ?, ?, ?)'''
        self.db_interface.execute_query(query, (username, hashed_password, first_name, last_name, role_id))

    def update_user(self, user_id, new_details):
        # Assuming new_details is a dict containing what needs to be updated
        updates = ', '.join(f"{key} = ?" for key in new_details.keys())
        query = f'''UPDATE Employee SET {updates} WHERE employee_id = ?'''
        params = tuple(new_details.values()) + (user_id,)
        self.db_interface.execute_query(query, params)

    def remove_user(self, user_id):
        query = '''DELETE FROM Employee WHERE employee_id = ?'''
        self.db_interface.execute_query(query, (user_id,))




