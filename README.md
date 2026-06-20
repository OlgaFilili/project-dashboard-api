# Project Management / Profiles Dashboard API

A backend service for creating, managing, sharing, and storing project-related information, including project metadata and attached documents.

# Stack
- Python 3.12+
- FastAPI
- PostgreSQL (optionally with SQLAlchemy ORM)
- Docker
- AWS S3 (file storage)
- AWS Lambda (image processing, file size calculation on S3 events)
- CI/CD: GitHub Actions / GitLab CI (testing, linting, build, deployment)

# Core Features
- User authentication (registration and login)
- Project creation, update, and deletion
- Project metadata management (name, description)
- Document management (upload, update, delete PDF/DOCX files)
- Project sharing via user invitations
- Role-based access control (owner / participant)

# API Overview
POST /auth – Register a new user
POST /login – Authenticate user and receive JWT token
POST /projects – Create a new project
GET /projects – Retrieve all projects accessible to the user
GET /project/{project_id}/info – Get project details
PUT /project/{project_id}/info – Update project details
DELETE /project/{project_id} – Delete project (owner only)
GET /project/{project_id}/documents – List project documents
POST /project/{project_id}/documents – Upload documents
GET /document/{document_id} – Download document
PUT /document/{document_id} – Replace document
DELETE /document/{document_id} – Delete document
POST /project/{project_id}/invite?user={login} – Invite user to project

## Optional Feature
GET /project/{project_id}/share?with={email} – Generate share link for external access

# Phase 2 Extensions
Database normalization / denormalization experiments
ORM vs raw SQL implementation comparison
AWS S3 integration with Lambda-based processing (image resize, file size aggregation, limits)
Automated testing (unit + integration)
CI/CD pipelines
Packaging tools (pyproject.toml, Poetry / uv, tox)
Pydantic validation for all request/response models
JWT-based authorization (1-hour expiration) applied to all protected endpoints

# Implementation Notes
- All responses are in JSON format (except file downloads)
- Two roles:
 - Owner: full control over project
 - Participant: can modify project data and documents, but cannot delete project
- API structure may evolve, as long as functionality is preserved
