# Mini Project Management API

A RESTful API for project management with role-based access control, built with Django REST Framework.

## Project Overview

This API provides a comprehensive system for managing projects and tasks with different user roles and permissions:

- **Admin**: Full access to all features and data
- **Project Manager**: Can create/manage tasks and view projects
- **Developer**: Can update task status of assigned tasks

## Tech Stack

- **Backend Framework**: Django 5.0 with Django REST Framework
- **Authentication**: JWT (JSON Web Tokens) with SimpleJWT
- **Database**: PostgreSQL
- **API Documentation**: Swagger/OpenAPI (via drf-spectacular)
- **Testing**: Django Test Framework with APITestCase

## Features

- **User Authentication** with JWT tokens
- **Role-Based Access Control**: 
  - Admin (role=1): Full system access
  - Project Manager (role=2): Task management and project viewing
  - Developer (role=3): Task status updates for assigned tasks
- **Project Management**: 
  - CRUD operations (Create, Read, Update, Delete)
  - Filtering by title, creator, dates
- **Task Management**: 
  - CRUD operations
  - Status tracking (To-Do, In Progress, Done)
  - Priority levels (Low, Medium, High)
  - Deadlines with start/end dates
- **Task Assignment**: Assign tasks to developers by ID or email
- **Comprehensive Filtering**:
  - Tasks by project, status, priority, and due date
  - Projects by title, creator, start date, and end date
- **Pagination**: All list endpoints (10 items per page)

## Architecture Decisions

### 1. Authentication & Security
- **JWT-based Authentication**: Used djangorestframework-simplejwt for secure, stateless authentication
- **Custom User Model**: Implemented email-based authentication rather than username
- **Permission Classes**: Created custom permission classes for fine-grained access control

### 2. API Design
- **RESTful Architecture**: Followed REST principles for consistent resource-based URLs
- **Serializer Pattern**: Used DRF serializers for data validation, conversion, and presentation
- **Generic Views**: Leveraged DRF generic views for standard CRUD operations
- **OpenAPI Documentation**: Auto-generated interactive API documentation

### 3. Database Design
- **PostgreSQL**: Selected for robustness, transactions, and advanced querying capabilities
- **Relational Model**: Properly structured relationships between User, Project, and Task models
- **Data Integrity**: Implemented proper constraints and validations at model level

### 4. Code Organization
- **Modular Structure**: Separated models, views, serializers, and permissions for maintainability
- **Reusable Components**: Created reusable permission classes and serializers
- **Test Coverage**: Comprehensive test suite with unit and API tests

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL

### Installation

1. Clone the repository
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Unix/MacOS
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your PostgreSQL database in `Task_managment/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'Managment',  # Your database name
           'USER': 'postgres',   # Your database user
           'PASSWORD': '2311',   # Your database password
           'HOST': 'localhost',
           'PORT': '5432'
       }
   }
   ```

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser (admin):
   ```bash
   python manage.py createsuperuser
   ```

7. Run the server:
   ```bash
   python manage.py runserver
   ```

8. Access the API at http://127.0.0.1:8000/
9. Access Swagger documentation at http://127.0.0.1:8000/swagger/

## Authentication

The API uses JWT tokens for authentication:

- **Token Format**: `JWT your_token_here` (note: uses 'JWT' prefix, not 'Bearer')
- **Token Lifetime**: Access tokens expire after 25 minutes
- **Header Format**: `Authorization: JWT your_token_here`

## API Endpoints

### Authentication

- `POST /register/`: Register a new user
- `POST /login/`: Login and get JWT tokens
- `POST /token/refresh/`: Refresh an expired token
- `POST /token/obtain/`: Directly obtain a token pair

### Users

- `GET /users/`: List all users (admin only)
- `PUT /users/{email}/role/`: Update user role (admin only)

### Projects

- `GET /projects/`: List all projects with filtering
- `POST /projects/`: Create a new project (admin only)
- `GET /projects/{id}/`: Get project details
- `PUT/PATCH /projects/{id}/`: Update a project (admin only)
- `DELETE /projects/{id}/`: Delete a project (admin only)

### Tasks

- `GET /tasks/`: List all tasks with filtering
- `POST /tasks/`: Create a new task (admin & project manager)
- `GET /tasks/{id}/`: Get task details
- `PUT/PATCH /tasks/{id}/`: Update a task (role-based permissions)
- `DELETE /tasks/{id}/`: Delete a task (admin & project manager)
- `PUT /tasks/{id}/assign/`: Assign a task to a developer

## Filtering Examples

- **Tasks by project**: `/tasks/?project=1`
- **Tasks by status**: `/tasks/?status=In Progress`
- **Tasks by priority**: `/tasks/?priority=High`
- **Tasks by due date**: `/tasks/?due_date=2025-05-15`
- **Projects by title**: `/projects/?title=Frontend`
- **Combined filters**: `/tasks/?project=1&status=In Progress&priority=High`

## Pagination

All list endpoints are paginated with 10 items per page. Access different pages with:
- `/tasks/?page=2`
- `/projects/?page=3`

## Role-Based Permissions

### Admin (role=1):
- Full CRUD access to all projects and tasks
- Can manage user roles
- Can assign tasks to developers

### Project Manager (role=2):
- Can view all projects (read-only)
- Can create, update and delete tasks
- Can assign tasks to developers

### Developer (role=3):
- Can view tasks assigned to them
- Can update the status of their assigned tasks (using PATCH)
- Can view projects where they have assigned tasks

## Running Tests

The project includes a comprehensive test suite that verifies all API functionality:

```bash
python manage.py test user_board
```

Test coverage includes:
- User registration and authentication
- Role-based access control
- Project CRUD operations
- Task management
- Filtering and pagination
- JWT authentication
