# CSS499-Collabinator
## Description
* Local web server for collaborating on various documents.
* Configure different members and roles for different states of each document
### User Permissions and Document States
* **Read** - User has access to read documents on the site
* **Upload** - User has permission to upload a new document
* **Approve** - User has permission to approve/reject documents that have been uploaded
  - Documents will not be visible to other users until they are **Approved**
* **Select** - User can select which Users will take part in the document review
  - Individual permissions for interacting with any document are still bound by the User's Role
  - Role Permissions likewise do not immediately allow exercising their permissions on a document unless the specific user is marked as a reviewer for the document
* **Comment** - User may add comments to the document
* **Respond** - User may respond to existing comments
* **Resolve** - User may mark a comment as resolved
  - Resolved comments may not receive new responses
* **Update** - User may update an existing document with a new upload
  - Updated documents will retain the same name as it had when first uploaded
  - Existing comments and responses will remain on the document
  - Upload Document may be a different document type than original upload
* **Close Comments** - Disable adding any additional comments to the document
  - Existing comments may still be commented on until all comments are resolved or the review is closed
* **Close Review** - Finalize the document marking all comments as resolved and removing all reviewers from the document
  - Document will still be visible to those with read permissions but no further changes can be made in comments or document updates
* **Manage Users** - Add and Edit Roles and Users
  - Users can only have their password changed by a user manager
  - User managers can create custom roles to tailor custom permissions for the Company's desired Document Workflow
###  Using the Web App
* Default admin account email login
  - **_Email_: admin@collab.inator
  - _Password_: admin**
* To change the default name and email of the root admin account
  - Go To **Members** Page
  - Select Admin User
  - Edit Email, Password, and First and Last Name to liking
  - **Submit** Changes
* New users are added via registering a new account in the **Register** Tab
  - New users by default have no role, and must be given a role to have permission to use any of the sites features including seeing documents
  - Admins can add a role to a user via the **Members** Tab
## Prerequisites 
* Docker Desktop Client installed and running
* Stable Internet Connection
## Setup
* Clone the repository into a local directory
* Run INIT.bat to configure the server for local docker client
* Run START.bat to launch the server
### Server runs on localhost port 8082
### **NOTE:** Running INIT.bat again will reinitialize the database, wiping its previous contents
