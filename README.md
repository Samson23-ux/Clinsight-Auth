# Clinsight Auth

---

## Description 📝

A secure Authentication service built for Clinsight platform. Supports email/password and Google OAuth sign-in with a focus on security and performance.

---

## Technology Stack 🛠️

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2C3E50?style=for-the-badge&logo=pydantic&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)

---

## Features ✨

#### Students:
- Sign up with email and password with OTP-based email verification
- Sign in using Google account
- Store and manage short-lived JWT tokens
- Argon2 password hashing

## Technical Highlights ⚙️

- **JWT** for authentication
- **Argon2** password hashing
- **Rate limiting** with SlowAPI
- **Background processing** of tasks with Celery

---

## Ways to Run Application 🚀

1. Run application Locally

### Prerequisites 📋

- Install Python 3.14. [Installation link](https://www.python.org/downloads/)
- Install uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Install Redis [Installation link](https://redis.io/downloads/)
- Install and set up RabbitMQ on your machine. [Installation link](https://www.rabbitmq.com/docs/download)
- Install and set up PgAdmin. [Installation link](https://www.pgadmin.org/download/)

---

### Steps 🛠️

#### Clone the repository:
```bash
git clone `https://github.com/Samson23-ux/Clinsight-Auth`
```

#### Navigate to the project directory:
```bash
cd "Clinsight-Auth"
```

#### Create and activate virtual environment:

**Install dependencies:**
```bash
uv sync
```

- **Copy and configure variables:**
```bash
cp .env.example .env
```

#### Create API database using PgAdmin.

#### Start Celery worker:
```bash
uv run celery -A app.tasks.celery_app worker -l info -P gevent
```

#### Run the application:
```bash
uv run uvicorn app.main:app --reload
```

#### Test API endpoints via docs:
Open your browser and navigate to [http://localhost:8000/docs](http://localhost:8000/docs).

---

2. Test endpoints via live URL:

- [Live App](######).

---

## Testing 🧪

### Run tests:
```bash
pytest
```

### Run a particular test module:
```bash
pytest tests/<preferred_test_module.py>
```
