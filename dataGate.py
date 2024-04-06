import sqlite3
import os.path.isfile
from urllib.request import pathname2url

databaseName = "collabin.db"
    
    
class DataGate:
    def __init__():
        
        #try to open database, make it if it doesn't exist
        if os.path.isfile(databaseName):
            self.connection = sqlite3.connect(databaseName)
            self.cur = connection.cursor()
        #first time
        else:
            self.connection = sqlite3.connect(databaseName)
            self.cur = connection.cursor()
            self.cur.execute("CREATE TABLE Role(role_id INT PRIMARY KEY, role_name TEXT NOT NULL, upload INT NOT NULL, approved INT NOT NULL, select_reviewers INT NOT NULL,  read_only INT NOT NULL, comment INT NOT NULL, respond INT NOT NULL,resolved INT NOT NULL, upload_update INT NOT NULL, close_comment INT NOT NULL, close_review INT NOT NULL, is_admin INT NOT NULL);")
            self.cur.execute("CREATE TABLE Employee(employee_id INTEGER PRIMARY KEY, employee_username TEXT NOT NULL, employee_hash TEXT NOT NULL, employee_salt TEXT NOT NULL, employee_first_name TEXT NOT NULL, employee_last_name TEXT NOT NULL, employee_role INT NOT NULL, FOREIGN KEY(employee_role) REFERENCES Role(role_id));")           
            self.cur.execute("CREATE TABLE Document(document_id INT PRIMARY KEY, document_file_name TEXT NOT NULL, is_pdf INT NOT NULL, document_stage INT NOT NULL, assigned_employee INT, FOREIGN KEY(assigned_employee) REFERENCES Employee(employee_id));")
            self.cur.execute("CREATE TABLE Comment(comment_id INT PRIMARY KEY, doc_id INT NOT NULL, commenter_id INT NOT NULL, parent_id INT, comment_text TEXT NOT NULL, comment_time TEXT NOT NULL, closed INT NOT NULL, FOREIGN KEY(parent_id) REFERENCES Comment(comment_id),FOREIGN KEY(doc_id) REFERENCES Document(document_id), FOREIGN KEY(commenter_id) REFERENCES Employee(employee_id));")
            self.cur.execute("CREATE TABLE Alert(role_id INT PRIMARY KEY, recepient_id INT NOT NULL, message_cont TEXT NOT NULL, FOREIGN KEY(recepient_id) REFERENCES Employee(employee_id));")
            self.cur.execute("INSERT INTO Role VALUES(\"Admin\",1,1,1,1,1,1,1,1,1,1,1);")
            

            #figure out how we are getting initial account. Need to add hash function here.
            self.cur.execute("INSERT INTO Employee VALUES(\"Admin\",1,1,1,1,1,1,1,1,1,1,1);")
            connection.commit()
            
        
    def addRole(self, name, upload, approved, select_reviewers, read_only, comment, respond,resolved, upload_update, close_comment, close_review, is_admin)
        data = [(name, upload, approved, select_reviewers, read_only, comment, respond,resolved, upload_update, close_comment, close_review, is_admin)]
        self.cur.execute("INSERT INTO Role VALUES(?,?,?,?,?,?,?,?,?,?,?,?);", data)
    
    
    def addRole(self, name, upload, approved, select_reviewers, read_only, comment, respond,resolved, upload_update, close_comment, close_review, is_admin)
        data = [(name, upload, approved, select_reviewers, read_only, comment, respond,resolved, upload_update, close_comment, close_review, is_admin)]
        self.cur.execute("INSERT INTO Role VALUES(?,?,?,?,?,?,?,?,?,?,?,?);", data)    

    


    def execute_query(self, query, value):
        self.cur.execute(query, value)



        