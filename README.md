
# English Learning Platform – FastAPI Backend

## Project Overview

An English Learning Platform backend developed using Python and FastAPI.

The application provides backend functionality for managing English-learning resources, user accounts, study activities, quizzes, progress reports, and free discussion sessions.

This is an independently developed personal project.

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Pydantic
- Alembic
- PyJWT
- APScheduler
- Pytest

## Main Features

- User registration and authentication using JWT.
- Role-based authorization for administrators.
- Course and lesson management.
- Vocabulary and exercise management.
- Questions and answer options.
- User profiles and course enrollment.
- Study-session management and study-time reports.
- Quiz performance reporting.
- Discussion sessions, topic assignment, registration and voting.
- Automatic discussion-topic winner selection using APScheduler.

## Project Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file by copying `.env.example`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your own:

- Development database URL.
- Test database URL.
- JWT secret key.
- JWT signing algorithm.

Never publish your actual `.env` file.

### 4. Configure PostgreSQL

Install PostgreSQL and create two databases:

- `learning_english` (development database)
- `english_learning_platform_test` (test database)

Configure both database URLs in your local `.env` file.

### 5. Run database migrations

Apply the database migrations to the development database:

```powershell
alembic upgrade head
```

### 6. Start the application

```powershell
uvicorn main:app --reload
```

The interactive API documentation is available at:

http://127.0.0.1:8000/docs

### 7. Running tests

Tests are written using Pytest and use a separate PostgreSQL test database.

Run the tests using:

```powershell
python -m pytest -v -s
```

**Testing status:** Automated tests are currently being developed and expanded. Some tests may depend on existing test database records. Test-data isolation and reproducibility are still being improved.

## Project Status

The application is under active development.

Automated testing, deployment, and additional improvements are ongoing.
