# Project Management / Profiles Dashboard API

A REST API for managing collaborative projects and their related documents.

## Technology Stack
Python 3.13
FastAPI
SQLAlchemy 2.x (async ORM)
asyncpg
PostgreSQL 14
Docker & Docker Compose
AWS S3 (planned)
AWS Lambda (planned)

## Core Features
User registration and authentication
Project creation, update and deletion
Project metadata management
Document upload, download, replacement and deletion
Project sharing via invitations
Role-based access control (Owner / Participant)

## API Overview
POST /auth – Register a new user
POST /login – Authenticate user and receive JWT token
POST /projects – Create a new project
GET /projects – Retrieve all accessible projects
GET /project/{project_id}/info – Get project details
PUT /project/{project_id}/info – Update project details
DELETE /project/{project_id} – Delete project
GET /project/{project_id}/documents – List project documents
POST /project/{project_id}/documents – Upload documents
GET /document/{document_id} – Download a document
PUT /document/{document_id} – Replace a document
DELETE /document/{document_id} – Delete a document
POST /project/{project_id}/invite – Invite a user to the project

See API_SPEC.md for the complete API specification.

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
│     └── main.py
├── config/
│     └── config.py
├── database/
│     ├── db.py
│     └── models.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── API_SPEC.md
└── .env


## Planned Extensions
JWT authorization
AWS S3 integration
AWS Lambda processing
Unit and integration tests
CI/CD pipelines
Alembic migrations
Pydantic request/response models

## Notes
- All responses are returned in JSON format except file downloads.
- The API structure may evolve while preserving the planned functionality.