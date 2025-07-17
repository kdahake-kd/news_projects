# 📰 News Search Web Application

A **Django-powered web application** for searching, viewing, and managing news articles with user authentication, admin quotas, and background refresh via **Celery**.

---

## 🚦 Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Admin & Background Tasks](#admin--background-tasks)
- [License](#license)

---

## ⚙️ Features

- 🔐 **User Registration & Login**  
  Secure authentication using Django's built-in system.

- 🔍 **Keyword-Based News Search**  
  Search headlines and articles via [NewsAPI](https://newsapi.org).

- 🧠 **User-specific Search History**  
  Each user can view and manage their search logs.

- 🛡 **Admin Panel**  
  - View all users  
  - Set quota (max search keywords) per user  
  - Monitor user activity logs

- 🔁 **Automatic News Refresh**  
  Celery integration for background tasking (e.g., periodic news refresh).

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository

```bash
git clone git@github.com:kdahake-kd/news_projects.git
cd news_projects
```

### 2️⃣ Create and Activate Virtual Environment

```bash
virtualenv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables

Create a `.env` file in the project root:

```env
NEWS_API_KEY=your_actual_api_key
```

> **Note:**  
> - Never share your API key.  
> - `.env` is included in `.gitignore`.

---

### 🧩 Running the Project

#### ✅ Apply Migrations and Start Server

```bash
python manage.py migrate
python manage.py runserver
```

#### ✅ Start Celery Worker

Ensure [Redis](https://redis.io/) server is running (`redis-server`):

```bash
celery -A news_project worker --loglevel=info
```

#### 🔄 Trigger Background Task

In Django shell:

```python
from news.tasks import refresh_articles_task
refresh_articles_task.delay()
```

---

## 🔐 Admin & Background Tasks

### Admin Panel

- URL: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

Create a superuser:

```bash
python manage.py createsuperuser
```

Admin Features:
- View/manage users
- Set per-user keyword quota
- Monitor search logs

---

### 🧪 Test Celery Setup

In Django shell:

```python
from news.tasks import test_celery_task
test_celery_task.delay()
```

If Celery worker is running, you'll see output from the task execution.

---

## 🧠 Tech Stack

- **Backend:** Django, Django REST Framework
- **Task Queue:** Celery with Redis
- **Auth:** Django built-in authentication
- **API:** [NewsAPI.org](https://newsapi.org)
- **Database:** SQLite (swap for PostgreSQL if desired)
- **Environment Management:** python-dotenv

---

## 📂 Project Structure

```
news_project/
├── news/                # Main app
├── users/               # Auth app
├── templates/           # HTML templates
├── static/              # Static files
├── news_project/        # Django settings
├── .env                 # API keys and secrets
├── requirements.txt
├── README.md
```

---

## 📑 License

This project is for educational and demonstration purposes.

---

**Happy News Searching!** 🚀
