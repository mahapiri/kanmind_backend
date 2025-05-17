# KanMind Backend – Django REST API

KanMind Backend is a RESTful API built with **Django** and **Django REST Framework (DRF)**. It powers the KanMind project – a lightweight Kanban-style task manager designed to help students learn full-stack development.

This repository is intended to work alongside the [KanMind Frontend](https://github.com/mahapiri/kanmind_frontend.git), and provides all necessary backend functionality.

---

## 🧠 Special Aspects

- 🔄 **API-First Design**: Cleanly structured endpoints make it easy to connect any frontend technology (React, Angular, Vue, or Vanilla JS).
- 🔐 **User Authentication**: Supports basic user auth (login, registration).
- 🔄 **Task Workflow Management**: Enables task state transitions similar to Kanban (e.g., To Do → In Progress → Review → Done).
- 📦 **Simple Database Setup**: Uses SQLite by default for quick local development, easily switchable to PostgreSQL for production.

---

## 📦 Installation & Setup

```bash
# Clone the repository
git clone https://github.com/mahapiri/kanmind_backend.git
cd kanmind_backend

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: "env/Scripts/activate"

# Install dependencies
pip install -r requirements.txt
```

### 🔐 Environment Setup

This project uses environment variables for configuration. Create a `.env` 
file in the project's root directory with the following content:

```bash
# Create .env-file with Secret_Key
echo SECRET_KEY="Key" > .env
```

Replace "Key" with the actual secret key value that will be provided to you.

### 🛢️ Database and Static Files Setup

```bash
# Apply migrations
python manage.py migrate

# Run the server
python manage.py runserver
```

### 👑 Admin Access Setup

Once the project is running, you can register as an admin user to access the Django admin interface:

1. Create a superuser account:
```bash
python manage.py createsuperuser
```

2. Follow the prompts to enter your username, email, and password.

3. Access the admin interface by navigating to:
```
http://127.0.0.1:8000/admin/
```

4. Log in with the superuser credentials you just created.

---

## 🚀 API Documentation

API documentation is available once the server is running at:
```
http://localhost:8000/api/schema/redoc/
```