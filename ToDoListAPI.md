Todo List API


This is a RESTful API built with Django and Django REST Framework (DRF) for managing todo lists. It allows users to create, read, update, and delete tasks, with JWT-based authentication to ensure secure access to user-specific data.


Table of Contents

Tech Stack

Setup Instructions

Contributing

API Endpoints

Testing


Tech Stack

Backend: Django, Django REST Framework

Authentication: JSON Web Tokens (JWT)

Database: SQLite (default; can be configured for other databases)

Testing Tools: Postman, curl


Setup Instructions

Follow these steps to set up the project locally:

1.Clone the Repository

git clone https://github.com/your-username/todo-list-api.git

cd ToDoListAPI

2. Set Up a virtual Environment

 python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate  


Contributing

We welcome contributions from all collaborators! To ensure smooth collaboration:

Issues: Check the GitHub project board for tasks in "Todo." Assign yourself or comment if you’re working on something.

Pull Requests: Submit PRs to the main branch. Include a clear description of your changes and link to the relevant issue.

Coding Standards: Follow PEP 8 for Python and use meaningful variable names. Add comments where necessary.
Commit Messages: Use descriptive messages (e.g., "Add task model with title, description, and status fields").
