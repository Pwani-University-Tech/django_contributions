# Todo List API

A RESTful API built with Django and Django REST Framework (DRF) for managing todo lists. This API allows users to create, read, update, and delete tasks while ensuring secure, user-specific access via JWT-based authentication.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project provides a simple yet powerful backend for managing your tasks. Whether you’re building a personal organizer or integrating task management into a larger application, this API is designed to be straightforward, secure, and easily extendable.

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

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Contributing
We welcome contributions from everyone! To contribute, please follow these guidelines:

Issues: Check the GitHub project board for tasks listed under "Todo." Feel free to assign yourself or comment if you’re working on a task.
Pull Requests: Submit PRs to the main branch with a clear description of your changes and a reference to the relevant issue.
Coding Standards: Follow PEP 8 for Python code. Use clear, descriptive variable names and include comments as needed.
Commit Messages: Use descriptive messages (e.g., "Add task model with title, description, and status fields").
