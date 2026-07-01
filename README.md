# Project Management / Profiles Dashboard API

A REST API for managing collaborative projects and their related documents.

## Technology Stack
- Python 3.13
- FastAPI
- SQLAlchemy 2.x (async ORM)
- asyncpg
- PostgreSQL 14
- PyJWT
- Pytest (unit tests)
- Docker & Docker Compose
- AWS S3 (planned)
- AWS Lambda (planned)

## Core Features
- User registration and authentication (JWT)
- Project creation, update and deletion
- Project access via owner and participants
- Project invitations (add user to project)
- Role-based access control (Owner / Member)

## API Overview
### Auth
- `POST /auth` – Register a new user
- `POST /login` – Authenticate user and return JWT token

### Projects
- `POST /projects` – Create project
- `GET /projects` – Get user-accessible projects
- `GET /project/{project_id}/info` – Get project details. Returns full project info (details + documents).  
  *(documents integration is planned and not implemented yet)*
- `PUT /project/{project_id}/info` – Update project
- `DELETE /project/{project_id}` – Delete project
- `POST /project/{project_id}/invite` – Invite user to project

### Documents (planned)
- `GET /project/{project_id}/documents`
- `POST /project/{project_id}/documents`
- `GET /document/{document_id}`
- `PUT /document/{document_id}`
- `DELETE /document/{document_id}`

See API_SPEC.md for the complete API specification.

## Testing
- Unit tests for service logic
- Authentication tests (login, token validation)
- Project-related tests (access control, invitations)
- Pytest used as test framework

## Project Setup
1. Environment Variables
Create a .env file with the following variables:
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=
DATABASE_HOST=
SECRET_KEY=

2. Running the Application
Build and start the containers:
```docker compose up --build```
The API will be available at:
http://localhost:8000

3. Project Structure
.
├── app/
│     ├── dashboard/
│     │     ├── exceptions.py
│     │     ├── repository.py
│     │     ├── routes.py
│     │     ├── routes_auth.py
│     │     ├── schemas.py
│     │     └── service.py
│     └── main.py
├── config/
│     └── config.py
├── database/
│     ├── db.py
│     └── models.py
├── tests/
│     ├── conftest.py
│     ├── test_auth.py
│     ├── test_projects.py
│     └── test_schemas.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── API_SPEC.md
└── .env


## Planned Extensions
AWS S3 integration for documents
AWS Lambda processing
Alembic migrations
CI/CD pipeline
Extended integration tests


## Notes
- All responses are returned in JSON format except file downloads.
- The API structure may evolve while preserving the planned functionality.
- Authentication is required for all project-related endpoints.
- The project is structured using a layered architecture (routes → service → repository).
- Access control is enforced at service level.