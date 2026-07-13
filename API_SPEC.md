# Project management/profiles dashboard API Spec

## Scope
- Service to create, update, share, and delete projects information (details, attached documents)
- Retrieval of project details and attached documents
- Two types of access – owner (creator of the project, can do anything) and participant (user invited to the project, can modify everything (including documents), cannot delete project (but can delete attached documents)
- Participant access is granted by project owner through the invite endpoint.

## Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /auth | Create user (login, password, repeat password) |
| POST | /login | Login into service (login, password) |
| POST | /projects | Create project from details (name, description). Automatically gives access to created project to user, making him the owner (project's admin) |
| GET | /projects | Get all projects, accessible for a user. Returns list of projects full info(details + documents) |
| GET | /project/{project_id}/info | Return project’s details, if user has access |
| PUT | /project/{project_id}/info | Update projects details - name, description. Returns the updated project’s info |
| DELETE | /project/{project_id} | Delete project, can only be performed by the projects’ owner. Deletes the corresponding  documents |
| GET | /project/{project_id}/documents | Return all the project's documents |
| POST | /project/{project_id}/documents | Upload document/documents for a specific project |
| GET | /document/{document_id} | Download document, if the user has access to the corresponding project |
| PUT | /document/{document_id} | Update document |
| DELETE | /document/{document_id} | Delete document and remove it from the corresponding project. User with participant role can do this. Removes document from system and deletes file from storage (S3) |
| POST | /project/{project_id}/invite | Grant access to the project for a specific user. If the request is not coming from the project's owner, results in error. Granting access gives participant permissions to receiving user |

## API Contracts
1. POST /auth

Request:
{
  "login": "Olga",
  "password": "password",
  "repeat_password": "password"
}
Response: 201 Created
{
  "user_id": 1, 
  "login": "Olga", 
  "created_at": "2026-06-18T15:32:29Z"
}
Errors:
422 Unprocessable Content - Username and password required.
422 Unprocessable Content - Passwords do not match.
409 Conflict - User already exists.


2. POST /login

Request: 
{
  "login": "Olga",
  "password": "password"
}
Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer"
}
Errors:
401 Unauthorized - Invalid credentials.


3. POST /projects

Authorization header:
Bearer <access_token>

Request:
{
  "name": "Project’s name", 
  "description": "Project’s description"
}

Response: 201 Created
{
  "project_id": 1, 
  "name": "Project’s name", 
  "created_at": "2026-06-18T16:22:56Z"
  "owner_id": 1
}

Errors:
401 Unauthorized - Invalid or expired token.
422 Unprocessable Content - Project’s name is required.


4. GET /projects

Authorization header:
Bearer <access_token>

Response: 200 OK
{
  "projects":[
    {
      "project_id": 1,
      "name": "Project’s name",
      "description": "Project’s description",
      "created_at": "2026-06-18T16:22:56Z",
	  "owner_id": 1,
      "documents": [
		{
		  "document_id": 15,
		  "filename": "report.pdf",
		  "size": 2048,
		  "uploaded_at": "2026-06-19T12:38:19Z"
		}
	  ]
    }
  ]
}

Errors:
401 Unauthorized - Invalid or expired token.


5. GET /project/{project_id}/info

Authorization header:
Bearer <access_token>

Response: 200 OK
{
  "project_id": <project_id>,
  "name": "Project’s name",
  "description": "Project’s description",
  "created_at": "2026-06-18T16:22:56Z",
  "owner_id": 1
}

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User has no access to the project.
404 Not Found - Project not found.


6. PUT /project/{project_id}/info

Authorization header:
Bearer <access_token>

Request:
{
  "name": "New project's name"
}
or
{
  "description": "New project's description"
}

or both fields.

Response: 200 OK
{
  "project_id": <project_id>,
  "name": "New project’s name",
  "description": "New project’s description",
  "created_at": "2026-06-18T16:22:56Z",
  "owner_id": 1
}

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User has no access to the project.
404 Not Found - Project not found.


7. DELETE /project/{project_id}

Authorization header:
Bearer <access_token>

Response: 204 No Content

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User is not the project owner.
404 Not Found - Project not found.

8. GET /project/{project_id}/documents

Authorization header:
Bearer <access_token>

Response: 200 OK
{
  "documents": [
	{
	  "document_id": 15,
	  "filename": "report.pdf",
	  "size": 2048,
	  "uploaded_at": "2026-06-19T12:38:19Z"
	}
  ]
}

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User has no access to the project.
404 Not Found - Project not found.

9. POST /project/{project_id}/documents

Authorization header:
Bearer <access_token>

Content-Type: multipart/form-data
files: spec.pdf
files: report.docx

Constraints:
- Only .pdf and .docx files are allowed


Response: 201 Created
{
  "documents": [
    {
	  "document_id": 2, 
	  "filename": "spec.pdf",
	  "size": 2048
	  "uploaded_at": "2026-06-19T17:16:23Z"
    },
	{
	  "document_id": 3, 
	  "filename": "report.docx",
	  "size": 8192
	  "uploaded_at": "2026-06-19T17:16:57Z"
    }
  ]
}

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User has no access to the project.
404 Not Found - Project not found.
415 Unsupported Media Type - File type not supported.


10. GET /document/{document_id} - Download document, if the user has access to the corresponding project

Authorization header:
Bearer <access_token>

Response: 200 Ok
Binary stream
Headers: Content-Type, Content-Disposition

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User has no access to the corresponding project.
404 Not Found - Document not found.


11. PUT /document/{document_id} - Update document

Authorization header:
Bearer <access_token>

Content-Type: multipart/form-data
files: spec.pdf

Constraints:
- Only .pdf and .docx files are allowed

Response: 200 OK
{
  "document_id": <document_id>, 
  "filename": "spec_new.pdf",
  "size": 4096
  "uploaded_at": "2026-06-19T18:08:37Z"
}

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User has no access to the corresponding project.
404 Not Found - Document not found.
415 Unsupported Media Type - File type not supported.

12. DELETE /document/{document_id}

Authorization header:
Bearer <access_token>

Response: 204 No Content

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User has no access to the corresponding project.
404 Not Found - Document not found.


13. POST /project/{project_id}/invite - Grant access to the project for a specific user. If the request is not coming from the project's owner, results in error. Granting access gives participant permissions to receiving user.

Authorization header:
Bearer <access_token>

Request:
{
  "login": "Olga"
}

Response: 200 Ok

Errors:
401 Unauthorized - Invalid or expired token.
403 Forbidden - User is not the project owner.
404 Not Found - Project not found.
404 Not Found - User with <login> does not exist.
409 Conflict - Cannot invite the project owner.
409 Conflict - User with <login> already has access.
