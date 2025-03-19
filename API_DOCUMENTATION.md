# Todo List API Documentation

## Table of Contents
- [Authentication](#authentication)
- [User Management](#user-management)
- [Task Management](#task-management)
- [Category Management](#category-management)
- [Task Sharing](#task-sharing)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Authentication

### JWT Authentication
The API uses JWT (JSON Web Token) for authentication. All protected endpoints require a valid JWT token in the Authorization header.

#### Get JWT Token
```http
POST /api/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "access": "your.jwt.token",
    "refresh": "your.refresh.token"
}
```

#### Refresh JWT Token
```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "your.refresh.token"
}
```

Response:
```json
{
    "access": "new.jwt.token"
}
```

## User Management

### Register New User
```http
POST /api/users/
Content-Type: application/json

{
    "username": "newuser",
    "email": "user@example.com",
    "password": "secure_password",
    "password2": "secure_password"
}
```

Response:
```json
{
    "id": 1,
    "username": "newuser",
    "email": "user@example.com"
}
```

### Get Current User Profile
```http
GET /api/users/me/
Authorization: Bearer your.jwt.token
```

Response:
```json
{
    "id": 1,
    "username": "newuser",
    "email": "user@example.com"
}
```

### Change Password
```http
POST /api/users/change_password/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "old_password": "current_password",
    "new_password": "new_password",
    "new_password2": "new_password"
}
```

Response:
```json
{
    "status": "password changed"
}
```

## Task Management

### Create Task
```http
POST /api/tasks/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "title": "Complete project",
    "description": "Finish the todo list API project",
    "completed": false,
    "due_date": "2024-03-20T15:00:00Z",
    "priority": "HIGH",
    "category_id": 1
}
```

Response:
```json
{
    "id": 1,
    "title": "Complete project",
    "description": "Finish the todo list API project",
    "completed": false,
    "due_date": "2024-03-20T15:00:00Z",
    "priority": "HIGH",
    "priority_display": "High",
    "category": {
        "id": 1,
        "name": "Work",
        "description": "Work-related tasks"
    },
    "created_at": "2024-03-19T10:00:00Z",
    "updated_at": "2024-03-19T10:00:00Z"
}
```

### List Tasks
```http
GET /api/tasks/
Authorization: Bearer your.jwt.token
```

Query Parameters:
- `completed`: Filter by completion status (true/false)
- `category`: Filter by category ID
- `priority`: Filter by priority (LOW/MEDIUM/HIGH/URGENT)
- `ordering`: Sort by field (-field for descending)
  - `created_at`
  - `updated_at`
  - `due_date`
  - `priority`

### Get Task Details
```http
GET /api/tasks/{id}/
Authorization: Bearer your.jwt.token
```

### Update Task
```http
PUT /api/tasks/{id}/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "title": "Updated task title",
    "description": "Updated description",
    "completed": true,
    "due_date": "2024-03-21T15:00:00Z",
    "priority": "MEDIUM",
    "category_id": 2
}
```

### Delete Task
```http
DELETE /api/tasks/{id}/
Authorization: Bearer your.jwt.token
```

## Category Management

### Create Category
```http
POST /api/categories/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "name": "Work",
    "description": "Work-related tasks"
}
```

Response:
```json
{
    "id": 1,
    "name": "Work",
    "description": "Work-related tasks",
    "created_at": "2024-03-19T10:00:00Z",
    "updated_at": "2024-03-19T10:00:00Z"
}
```

### List Categories
```http
GET /api/categories/
Authorization: Bearer your.jwt.token
```

Query Parameters:
- `search`: Search categories by name or description

### Get Category Details
```http
GET /api/categories/{id}/
Authorization: Bearer your.jwt.token
```

### Update Category
```http
PUT /api/categories/{id}/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "name": "Updated Category",
    "description": "Updated description"
}
```

### Delete Category
```http
DELETE /api/categories/{id}/
Authorization: Bearer your.jwt.token
```

## Task Sharing

### Share Task
```http
POST /api/tasks/{id}/share/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "user_id": 2,
    "permission": "EDIT"
}
```

Response:
```json
{
    "id": 1,
    "task": 1,
    "task_title": "Complete project",
    "shared_with": 2,
    "shared_with_username": "otheruser",
    "permission": "EDIT",
    "created_at": "2024-03-19T10:00:00Z",
    "updated_at": "2024-03-19T10:00:00Z"
}
```

### Unshare Task
```http
DELETE /api/tasks/{id}/unshare/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "user_id": 2
}
```

## Error Handling

The API uses standard HTTP status codes and returns error messages in the following format:

```json
{
    "error": "Error message description"
}
```

Common Status Codes:
- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Examples

### Complete Workflow Example

1. Register a new user:
```http
POST /api/users/
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password2": "testpass123"
}
```

2. Get JWT token:
```http
POST /api/token/
Content-Type: application/json

{
    "username": "testuser",
    "password": "testpass123"
}
```

3. Create a category:
```http
POST /api/categories/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "name": "Work",
    "description": "Work-related tasks"
}
```

4. Create a task:
```http
POST /api/tasks/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "title": "Complete API Documentation",
    "description": "Write comprehensive API documentation",
    "completed": false,
    "due_date": "2024-03-20T15:00:00Z",
    "priority": "HIGH",
    "category_id": 1
}
```

5. Share the task:
```http
POST /api/tasks/1/share/
Authorization: Bearer your.jwt.token
Content-Type: application/json

{
    "user_id": 2,
    "permission": "EDIT"
}
```

6. Get all tasks:
```http
GET /api/tasks/
Authorization: Bearer your.jwt.token
```

This documentation will be updated as new features are added to the API. 