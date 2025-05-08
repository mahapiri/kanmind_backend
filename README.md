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
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations and run the server
python manage.py migrate
python manage.py runserver
