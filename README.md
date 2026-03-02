# 🔐 TEACHVERSE Auth - Production-Ready Microservice Authentication for FastAPI 

[![PyPI version](https://badge.fury.io/py/teachverse-auth.svg)](https://badge.fury.io/py/teachverse-auth)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A complete, authentication package for FastAPI with hierarchical permissions like AWS IAM.**

---

## ✨ Features

- 🔐 **OAuth2 Password Flow** - Standard OAuth2 authentication with JWT
- 🎫 **JWT Tokens** - Access & Refresh tokens with automatic rotation
- 🏛️ **Hierarchical Permissions** - Like AWS IAM (`service:resource_type:resource_id:action`)
- 🔄 **Wildcard Support** - `*` for any resource or action (automatic hierarchy)
- 👥 **Multi-tenant Ready** - Built-in organization support
- 🔌 **Service Discovery** - Microservices auto-register themselves
- 🚀 **FastAPI Integration** - Simple, intuitive dependencies
- 📦 **CLI Tools** - Migration, superuser creation, service registration
- 🛡️ **Security First** - Password hashing, token blacklisting, rate limiting ready
- 🔧 **Extensible** - Easy to add custom permissions and services

---

## 📦 Installation

```bash
# Basic installation
pip install teachverse-auth

# With Redis support (for token blacklisting)
pip install teachverse-auth[redis]

# For development
pip install teachverse-auth[dev]

# Create database tables
teachverse-auth migrate

# Initialize default services and permissions
teachverse-auth init-services

# Create a superuser (admin)
teachverse-auth createsuperuser
```
---

# 🚀 Quick Start - 5 Minutes
## 1. Initialize Database
```
# Run setup - will create .env interactively
teachverse-auth setup

# Create database tables
teachverse-auth migrate

# Initialize default services and permissions
teachverse-auth init-services

# Create a superuser (admin)
teachverse-auth createsuperuser

# Run server
teachverse-auth runserver

```

## 2. Configure Environment
Create a .env file (auto-generated on first run):
```
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/teachverse

# Security - CHANGE THIS IN PRODUCTION!
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (optional - for token blacklisting)
REDIS_URL=redis://localhost:6379/0

```
## 3. Add to Your FastAPI App

```
# main.py
from fastapi import FastAPI, Depends
from teachverse_auth.api import router as auth_router
from teachverse_auth.dependencies import (
    get_current_user,
    require_permission,
    require_resource_permission
)

app = FastAPI()

# Include all auth routes
app.include_router(auth_router)

# ========== Example Protected Endpoints ==========

@app.get("/api/v1/public")
async def public_endpoint():
    """No authentication required"""
    return {"message": "Public data"}

@app.get("/api/v1/me")
async def get_my_profile(
    current_user = Depends(get_current_user)  # Any authenticated user
):
    """Requires valid JWT token"""
    return {"user": current_user.user_data}

@app.post("/api/v1/courses")
async def create_course(
    course_data: dict,
    current_user = Depends(require_permission("course", "course", "create"))
):
    """Requires permission to create any course"""
    return {"message": "Course created"}

@app.get("/api/v1/courses/{course_id}")
async def get_course(
    course_id: str,
    current_user = Depends(require_resource_permission(
        "course", "course", course_id, "read"
    ))
):
    """Requires read permission on specific course"""
    return {"course_id": course_id, "data": {}}

@app.delete("/api/v1/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(require_permission("user", "user", "delete"))
):
    """Requires user:delete permission (admin only)"""
    return {"message": f"User {user_id} deleted"}

```

## 4. Run the Server
```
# Development server with auto-reload
teachverse-auth runserver --reload

# Production server
teachverse-auth runserver --host 0.0.0.0 --port 8000



```

# 🔐 TEACHVERSE Auth

A production-ready, authentication & authorization service for microservices and SaaS platforms built with FastAPI.

It provides JWT authentication, RBAC, fine-grained permissions, and multi-tenant service integration — all in one modular package.

---

## 🚀 Features

- JWT-based authentication (access + refresh tokens)
- AWS IAM-style granular permission system
- Role-Based Access Control (RBAC)
- Multi-tenant organization support
- Microservice auto-registration
- CLI for migrations, setup, and management
- Redis token blacklisting (optional)
- PostgreSQL support with Alembic migrations
- Docker-ready deployment

---

# ⚡ Quick Start

### 1️⃣ Install
```bash
pip install teachverse-auth

# Run setup - will create .env interactively
teachverse-auth setup

```

### 2. Configure environment
cp .env.example .env

Update .env:
DATABASE_URL=postgresql://user:pass@localhost:5432/teachverse
SECRET_KEY=your-super-secret-key

### 3. Initialize defaults
```bash
teachverse-auth init-services
teachverse-auth init-permissions
```

### 4. Create admin user
```bash
teachverse-auth createsuperuser
```
### 5.  Start server
```bash
teachverse-auth runserver --reload
```

# Understanding Permissions 
Permission format:
```css

{service}:{resource_type}:{resource_id}:{action}
```

| Component     | Description            | Example               |
| ------------- | ---------------------- | --------------------- |
| service       | Top-level service      | course, user, payment |
| resource_type | Type of resource       | course, profile       |
| resource_id   | Specific instance or * | 123, user-456, *      |
| action        | Operation              | read, update, delete  |

Examples
```python
"course:course:*:read"        # Read any course
"course:course:123:update"    # Update specific course
"user:profile:*:*"            # All actions on profiles
"payment:*:*:*"               # Full payment access
"*:*:*:*"                     # Super admin
```

# Automatic Permission Hierarchy

| Granted Permission       | Implied Permissions                            |
| ------------------------ | ---------------------------------------------- |
| `course:course:*:manage` | create, read, update, delete, publish, archive |
| `payment:*:*:*`          | All actions on all payment resources           |
| `user:profile:123:*`     | All actions on that user profile               |
You don't need to create all combinations - the system handles it!

## 🎯 Available Actions Guide

### Core CRUD Actions

| Action | When to Use | Example Permission |
|--------|-------------|-------------------|
| create | Creating new resources | `course:course:*:create` |
| read | Viewing/reading resources | `course:course:123:read` |
| update | Modifying existing resources | `course:course:123:update` |
| delete | Removing resources | `course:course:123:delete` |
| list | Listing multiple resources | `course:course:*:list` |

### Management Actions

| Action | When to Use | Example Permission |
|--------|-------------|-------------------|
| manage | Full control (includes all CRUD) | `course:course:*:manage` |
| approve | Review and approve pending items | `teacher:application:*:approve` |
| reject | Reject pending items | `teacher:application:123:reject` |
| publish | Make content public/live | `course:course:123:publish` |
| archive | Move to archive | `course:course:123:archive` |
| restore | Restore from archive | `course:course:123:restore` |
| export | Export data | `analytics:report:*:export` |

### Administrative Actions

| Action | When to Use | Example Permission |
|--------|-------------|-------------------|
| assign | Assign roles/permissions | `role:role:*:assign` |
| revoke | Revoke roles/permissions | `permission:permission:*:revoke` |
| suspend | Temporarily disable user | `user:user:123:suspend` |
| activate | Re-enable suspended user | `user:user:123:activate` |
| verify | Verify authenticity | `teacher:profile:123:verify` |

### Financial Actions

| Action | When to Use | Example Permission |
|--------|-------------|-------------------|
| process | Process payments | `payment:transaction:*:process` |
| refund | Issue refunds | `payment:transaction:123:refund` |
| payout | Process payouts | `payment:payout:*:process` |
| invoice | Generate invoices | `payment:invoice:*:create` |

---

## 🔌 Registering Your Microservice

Each microservice should register itself on startup:

```python
# course-service/main.py
from fastapi import FastAPI
from teachverse_auth.services import register_service

app = FastAPI()

@app.on_event("startup")
async def register_with_auth():
    """Register this service with the auth service"""
    await register_service(
        service_name="course",
        display_name="Course Management Service",
        resource_types=["course", "module", "lesson", "quiz", "assignment"],
        actions=["create", "read", "update", "delete", "list", "publish", "archive"],
        base_url="http://course-service:8000"
    )
    print("✅ Registered course service with auth")

# 📋 API Reference
## 🔐 Authentication Endpoints
| Method | Endpoint                      | Description        | Request Body                     |
| ------ | ----------------------------- | ------------------ | -------------------------------- |
| POST   | `/api/v1/auth/register`       | Register new user  | `{email, password, full_name}`   |
| POST   | `/api/v1/auth/token`          | Login (OAuth2)     | `username, password (form data)` |
| POST   | `/api/v1/auth/refresh`        | Refresh token      | `{refresh_token}`                |
| GET    | `/api/v1/auth/me`             | Get current user   | `-`                              |
| GET    | `/api/v1/auth/me/permissions` | Get my permissions | `-`                              |

## 🛡 Permission Endpoints

| Method | Endpoint                       | Description       | Required Permission              |
| ------ | ------------------------------ | ----------------- | -------------------------------- |
| POST   | `/api/v1/permissions`          | Create permission | `permission:permission:*:create` |
| GET    | `/api/v1/permissions/check`    | Check permission  | Authentication only              |
| GET    | `/api/v1/permissions/my`       | My permissions    | Authentication only              |
| GET    | `/api/v1/permissions/services` | List services     | `permission:service:*:list`      |

## 👑 Admin Endpoints
| Method | Endpoint                                  | Description    | Required Permission    |
| ------ | ----------------------------------------- | -------------- | ---------------------- |
| GET    | `/api/v1/admin/stats`                     | Platform stats | `system:stats:*:read`  |
| GET    | `/api/v1/admin/users`                     | List all users | `user:user:*:list`     |
| POST   | `/api/v1/admin/users/{id}/suspend`        | Suspend user   | `user:user:*:suspend`  |
| POST   | `/api/v1/admin/users/{id}/activate`       | Activate user  | `user:user:*:activate` |
| POST   | `/api/v1/admin/users/{id}/reset-password` | Reset password | `user:user:*:update`   |

## 🛠️ CLI Commands
```bash
# Database Commands
teachverse-auth migrate              # Create database tables
teachverse-auth init-services        # Initialize default services
teachverse-auth init-permissions     # Initialize permissions

# User Management
teachverse-auth createsuperuser      # Create admin user

# Resource Management
teachverse-auth create-resource course course 123 "Physics 101"

# Development
teachverse-auth runserver            # Start dev server (default: 127.0.0.1:8000)
teachverse-auth runserver --host 0.0.0.0 --port 9000 --reload
teachverse-auth shell                # Open Python shell with context

# Configuration
teachverse-auth configure            # Interactive configuration wizard
teachverse-auth check                # Check configuration and connections
```

## ⚙️ Configuration
### Environment Variables
Create a .env file (auto-generated on first run):
```env
# =============================================
# TEACHVERSE Auth - Required Configuration
# =============================================

# Database - PostgreSQL is required
DATABASE_URL=postgresql://user:pass@localhost:5432/teachverse

# Security - CHANGE THESE IN PRODUCTION!
SECRET_KEY=your-super-secret-key-at-least-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (optional - for token blacklisting)
REDIS_URL=redis://localhost:6379/0

# API Settings
API_PREFIX=/api/v1
DEBUG=false

# =============================================
# Service-Specific Configuration
# Add any settings for your services here
# =============================================

# Course Service Example
# COURSE_STORAGE_PATH=/data/courses
# COURSE_VIDEO_ENCODING_QUEUE=video-queue

# Payment Service Example
# BKASH_APP_KEY=your-key
# BKASH_APP_SECRET=your-secret

# Notification Service Example
# SMTP_HOST=smtp.gmail.com
# SMTP_USER=your-email@gmail.com
```

# 🐳 Docker Example
# Dockerfile
```Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install package
RUN pip install teachverse-auth

# Copy your app
COPY . .

# Use environment variables for configuration
ENV DATABASE_URL=postgresql://user:pass@db:5432/teachverse
ENV SECRET_KEY=${SECRET_KEY}
ENV REDIS_URL=redis://redis:6379/0

# Run migrations on startup
CMD teachverse-auth migrate && \
    teachverse-auth init-services && \
    teachverse-auth runserver --host 0.0.0.0

```
# docker-compose.yml
```yaml
version: '3.8'

services:
  auth:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/teachverse
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=teachverse
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

# 📊 Real-World Examples
## Example 1: E-Learning Platform
```python
# Teacher permissions
teacher_permissions = [
    "course:course:*:create",      # Can create courses
    "course:course:123:update",    # Can update own course
    "course:lesson:*:create",      # Can create lessons
    "student:student:*:read",      # Can view students
]

# Student permissions
student_permissions = [
    "course:course:*:read",          # Can view courses
    "user:profile:self:update",      # Can update own profile
    "payment:transaction:self:read", # Can view own payments
]

# Admin permissions
admin_permissions = [
    "user:user:*:*",                 # Full user management
    "organization:*:*:*",            # Full organization control
    "system:*:*:*",                  # System access
]

```
# Example 2: Multi-tenant SaaS
```python
# Organization admin
org_admin_permissions = [
    f"organization:{org_id}:*:*",    # Full org access
    "user:profile:*:read",           # View all users
    "user:profile:*:update",         # Update users
]

# Department head
dept_head_permissions = [
    f"course:{dept_id}:*:*",         # All course actions in dept
    "teacher:application:*:approve", # Approve teachers
]

```

# 🧪 Testing
```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=teachverse_auth tests/ --cov-report=html

# Test specific file
pytest tests/test_permissions.py -v
```

# 🔒 Security Best Practices
Change SECRET_KEY in production (use a long random string)

Use HTTPS always in production

Enable Redis for token blacklisting

Set DEBUG=False in production

Enforce strong password policies

Rotate SECRET_KEY periodically

Enable audit logs and monitor suspicious activity