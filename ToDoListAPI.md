# Todo List API

A RESTful API built with Django and Django REST Framework (DRF) for managing todo lists. This API allows users to create, read, update, and delete tasks while ensuring secure, user-specific access via JWT-based authentication.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project provides a simple yet powerful backend for managing your tasks. Whether you're building a personal organizer or integrating task management into a larger application, this API is designed to be straightforward, secure, and easily extendable.

## Tech Stack

- **Backend:** Django, Django REST Framework  
- **Authentication:** JSON Web Tokens (JWT)  
- **Database:** SQLite (default; configurable for other databases)  
- **Testing Tools:** Postman, curl  

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/todo-list-api.git
cd todo-list-api
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

## Features

### Authentication
- JWT-based authentication
- User registration and login
- Password change functionality
- Token refresh mechanism

### Task Management
- Create, read, update, and delete tasks
- Mark tasks as completed
- Set due dates for tasks
- Priority levels (Low, Medium, High, Urgent)
- Filter tasks by completion status
- Sort tasks by various criteria

### Category Management
- Create, read, update, and delete categories
- Associate tasks with categories
- Filter tasks by category
- Search categories

### Priority Management
- Set task priorities (Low, Medium, High, Urgent)
- Filter tasks by priority
- Sort tasks by priority
- Priority-based task organization

## API Endpoints

### Authentication Endpoints

- `POST /api/token/` - Get JWT token
- `POST /api/token/refresh/` - Refresh JWT token

### User Management Endpoints

- `POST /api/users/` - Register new user
- `GET /api/users/me/` - Get current user profile
- `PUT /api/users/{id}/` - Update user profile
- `POST /api/users/change_password/` - Change user password

### Task Endpoints

- `GET /api/tasks/` - List all tasks
- `POST /api/tasks/` - Create new task
- `GET /api/tasks/{id}/` - Get task details
- `PUT /api/tasks/{id}/` - Update task
- `DELETE /api/tasks/{id}/` - Delete task
- `GET /api/tasks/completed_tasks/` - Get completed tasks
- `GET /api/tasks/pending_tasks/` - Get pending tasks
- `GET /api/tasks/tasks_by_category/` - Get tasks by category
- `GET /api/tasks/tasks_by_priority/` - Get tasks by priority

### Category Endpoints

- `GET /api/categories/` - List all categories
- `POST /api/categories/` - Create new category
- `GET /api/categories/{id}/` - Get category details
- `PUT /api/categories/{id}/` - Update category
- `DELETE /api/categories/{id}/` - Delete category

### Filtering and Sorting

Tasks can be filtered and sorted using query parameters:
- Filter by completion: `?completed=true/false`
- Filter by category: `?category=1`
- Filter by priority: `?priority=URGENT`
- Sort by priority: `?ordering=priority` or `?ordering=-priority`
- Sort by due date: `?ordering=due_date` or `?ordering=-due_date`
- Sort by creation date: `?ordering=created_at` or `?ordering=-created_at`

## Testing

The API can be tested using the provided `api.rest` file or any REST client like Postman. The `api.rest` file includes examples of all available endpoints with proper authentication headers.

## Contributing

We welcome contributions from everyone! To contribute, please follow these guidelines:

1. **Issues**: Check the GitHub project board for tasks listed under "Todo." Feel free to assign yourself or comment if you're working on a task.
2. **Pull Requests**: Submit PRs to the main branch with a clear description of your changes and a reference to the relevant issue.
3. **Coding Standards**: Follow PEP 8 for Python code. Use clear, descriptive variable names and include comments as needed.
4. **Commit Messages**: Use descriptive messages (e.g., "Add task model with title, description, and status fields").

## License

This project is licensed under the MIT License - see the LICENSE file for details.
