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
- Docker & Docker Compose

## Development Tools
- uv for dependency management and virtual environment synchronization
- Ruff for code linting and quality checks
- Pytest for automated testing
- GitHub Actions for CI pipeline (linting and test execution)

## Core Features
- Data validation and serialization with Pydantic
- JWT-based authentication and authorization
- Project creation, update and deletion
- Project access via owner and participants
- Project invitations (add user to project)
- Role-based access control (Owner / Participant)
- Document management with metadata stored in PostgreSQL and files stored in S3-compatible object storage

## API Overview
### Auth
- `POST /auth` – Create user. (login, password, repeat password) 
- `POST /login` – Login into service (login, password). Authenticate user and return JWT token

### Projects
- `POST /projects` – Create project from details (name, description). Automatically gives access to created project to user, making him the owner.
- `GET /projects` – Get all projects, accessible for a user. Returns list of projects full info(details + documents).
- `GET /project/{project_id}/info` – Return project’s details, if user has access.  
- `PUT /project/{project_id}/info` – Update projects details - name, description. Returns the updated project’s info.
- `DELETE /project/{project_id}` – Delete project, can only be performed by the projects’ owner. Deletes the corresponding  documents.
- `POST /project/{project_id}/invite` – Grant access to the project for a specific user. If the request is not coming from the project's owner, results in error. Granting access gives participant permissions to receiving user

### Documents
- `GET /project/{project_id}/documents` – Return all the project's documents.
- `POST /project/{project_id}/documents` – Generate presigned URLs for direct document/documents upload to storage.
- `POST /project/{project_id}/documents/complete` – Complete document/documents upload for a specific project.
- `GET /document/{document_id}` – Download document, if the user has access to the corresponding project.
- `PUT /document/{document_id}` – Generate a presigned URL for replacing the content of an existing document in storage.
- `PUT /document/{document_id}/complete` – Complete document update.
- `DELETE /document/{document_id}` – Delete document and remove it from the corresponding project. User with participant role can do this. Removes document from system and deletes file from storage (S3).

See API_SPEC.md for the complete API specification.

## Database Design
The database schema is designed to separate entities and avoid unnecessary data duplication.

- User information is stored separately in the `Users` table.
- Project ownership is represented through the `owner_id` field in the `Projects` table. The owner is not duplicated in the project participants table.
- Project participants are stored separately in the `Project_Members` table, which represents user access to projects and supports role-based permissions.
- Documents are linked to projects through the `Documents` table. Only document metadata is stored in PostgreSQL, while the actual files are stored in S3-compatible object storage.
- Foreign key relationships are used to maintain consistency between related entities.

## Testing
Unit tests for the service layer:
- Authentication
- Project management
- Document management
- Service helper functions

Tests are implemented using pytest and pytest-asyncio.

## Project Setup
1. Environment Variables
```text
Create a `.env` file with the following variables:

DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=
DATABASE_HOST=
SECRET_KEY=
MINIO_ENDPOINT=
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
MINIO_BUCKET=
```
Do not commit `.env` files containing real credentials.

2. Running the Application
```text
Build and start the containers:
```docker compose up --build```
The API will be available at:
http://localhost:8000
```

3. Project Structure
```text
.
├── .github/workflows/
│     └── ci.yml
├── app/
│     ├── dashboard/
│     │     ├── routes.py 
│     │     │     ├── auth.py
│     │     │     ├── docs.py
│     │     │     └── projects.py
│     │     └── service.py
│     │     │     ├── docs.py
│     │     │     ├── helpers.py
│     │     │     ├── projects.py
│     │     │     └── secutrity.py
│     │     ├── exceptions.py
│     │     ├── repository.py
│     │     ├── schemas.py
│     │     ├── storage.py
│     │     └── storage_models.py
│     ├── database/
│     │     ├── db.py
│     │     └── models.py
│     ├── object_storage/
│     │     └── client.py
│     ├── config.py
│     ├── logging-config.py
│     └── main.py
├── tests/
│     ├── conftest.py
│     ├── test_auth.py
│     ├── test_docs.py
│     ├── test_projects.py
│     ├── test_schemas.py
│     └── test_service_helpers.py
├── API_SPEC.md
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── uv.lock
└── .env
```

## Notes
- All API responses are returned in JSON format.
- Authentication is required for all project-related endpoints.
- The project follows a layered architecture separating API routes, business logic, database access and object storage operations.
Repository layer exists and is separated from business logic.
Current implementation keeps repository methods grouped in a single module because of small project scale.
- Access control and permission checks are implemented at the service layer.
- Documents metadata is stored in PostgreSQL, while document files are stored in MinIO using the S3-compatible API.
- Document uploads and updates use presigned URLs, allowing clients to upload files directly to MinIO storage without routing file data through the API server.
- GitHub Actions automatically runs linting and tests on pull requests.