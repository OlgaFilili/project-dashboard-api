# Project Management / Profiles Dashboard API

A REST API for managing collaborative projects and their related documents.

## Technology Stack
- Python 3.13
- FastAPI
- SQLAlchemy 2.x (async ORM)
- asyncpg
- PostgreSQL 14
- MinIO (S3-compatible object storage)
- PyJWT
- Pytest (unit tests)
- Docker & Docker Compose
- AWS S3 (planned deployment)
- AWS Lambda (planned)

## Core Features
- Data validation and serialization with Pydantic
- JWT-based authentication and authorization
- Project creation, update and deletion
- Project access via owner and participants
- Project invitations (add user to project)
- Role-based access control (Owner / Participant)
- Document upload, download, update and deletion via S3-compatible object storage

## API Overview
### Auth
- `POST /auth` – Register a new user
- `POST /login` – Authenticate user and return JWT token

### Projects
- `POST /projects` – Create project
- `GET /projects` – Get user-accessible projects
- `GET /project/{project_id}/info` – Get project details. Returns full project info (details + documents).  
- `PUT /project/{project_id}/info` – Update project
- `DELETE /project/{project_id}` – Delete project
- `POST /project/{project_id}/invite` – Invite user to project

### Documents
- `GET /project/{project_id}/documents` – List project documents
- `POST /project/{project_id}/documents` – Upload documents
- `GET /document/{document_id}` – Download document
- `PUT /document/{document_id}` – Replace document
- `DELETE /document/{document_id}` – Delete document

See API_SPEC.md for the complete API specification.

## Testing
Unit tests for the service layer:
- Authentication
- Project management
- Document management
- Service helper functions

Pytest used as test framework

## Project Setup
1. Environment Variables
Create a .env file with the following variables:
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=
DATABASE_HOST=
SECRET_KEY=
MINIO_ENDPOINT=
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
MINIO_BUCKET=

2. Running the Application
Build and start the containers:
```docker compose up --build```
The API will be available at:
http://localhost:8000

3. Project Structure
.
├── app/
│     ├── dashboard/
│     │     ├── routes.py 
│     │     │     ├── routes_auth.py
│     │     │     ├── routes_docs.py
│     │     │     └── routes_projects.py
│     │     └── service.py
│     │     │     ├── helpers.py
│     │     │     ├── security.py
│     │     │     ├── service_core.py
│     │     │     └── service_docs.py
│     │     ├── exceptions.py
│     │     ├── repository.py
│     │     ├── schemas.py
│     │     ├── storage.py
│     │     └── storage_models.py
│     ├── logging-config.py
│     └── main.py
├── config/
│     └── config.py
├── database/
│     ├── db.py
│     └── models.py
├── object_storage/
│     └── client.py
├── tests/
│     ├── conftest.py
│     ├── test_auth.py
│     ├── test_docs.py
│     ├── test_projects.py
│     ├── test_schemas.py
│     └── test_service_helpers.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── API_SPEC.md
└── .env


## Planned Extensions
- AWS S3 deployment (replace MinIO with AWS S3)
- AWS Lambda processing
- Alembic migrations
- CI/CD pipeline


## Notes
- All responses are returned in JSON format except file downloads.
- The API structure may evolve while preserving the planned functionality.
- Authentication is required for all project-related endpoints.
- The project follows a layered architecture separating API, business logic, database access and object storage.
- Access control is enforced at service level.
- Documents are stored in MinIO using the S3-compatible API.