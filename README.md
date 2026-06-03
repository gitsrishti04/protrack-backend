# ProTrack AI — Backend

FastAPI backend for the AI-Based Project Progress Tracking and Resource Prediction System.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [ML Models](#ml-models)
- [Running the Server](#running-the-server)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)

---

## Overview

This backend provides:
- REST API for project, task, and user management
- JWT-based authentication with role-based access control
- ML model endpoints for delay risk, completion time, and resource allocation prediction
- AI chatbot endpoint using LangGraph + LangChain + Gemini + RAG
- PostgreSQL database with SQLAlchemy ORM

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI 0.135 |
| Database | PostgreSQL + SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| ML | scikit-learn 1.8, XGBoost 3.2, pandas, numpy, joblib |
| AI Chatbot | LangChain 1.3, LangGraph 1.2, Gemini API (google-genai) |
| Server | Uvicorn |

---

## Prerequisites

- Python 3.11+
- PostgreSQL
- pip
- Homebrew (macOS only, for XGBoost dependency)

---

## Project Structure

```
protrack_backend/
├── app/
│   ├── main.py                  # FastAPI app, router registration, CORS
│   ├── database.py              # SQLAlchemy engine and session
│   ├── dependencies.py          # Shared dependencies
│   ├── models/
│   │   ├── user.py              # User table
│   │   ├── project.py           # Project table
│   │   ├── task.py              # Task table
│   │   ├── project_member.py    # Project members table
│   │   └── progress_history.py  # Progress update history table
│   ├── schemas/
│   │   ├── user.py              # Pydantic user schemas
│   │   ├── project.py           # Pydantic project schemas
│   │   ├── task.py              # Pydantic task schemas
│   │   └── member.py            # Pydantic member schemas
│   ├── routes/
│   │   ├── auth.py              # Login, register, user management
│   │   ├── projects.py          # Project and task CRUD
│   │   ├── dashboard.py         # Dashboard KPIs, workload, utilization
│   │   ├── predictions.py       # ML prediction endpoints
│   │   ├── chat.py              # AI chatbot (LangGraph + Gemini + RAG)
│   │   └── test.py              # Health check
│   ├── ml/
│   │   ├── generate_data.py         # Generate completion prediction training data
│   │   ├── generate_resource_data.py # Generate resource allocation training data
│   │   ├── train.py                 # Train delay + completion models
│   │   ├── train_resource_model.py  # Train XGBoost resource models
│   │   └── predict.py               # Load models and run predictions
│   └── utils/
│       ├── jwt.py               # JWT token creation
│       ├── security.py          # Password hashing
│       └── deps.py              # get_current_user dependency
└── .env                         # Environment variables (gitignored)
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/gitsrishti04/protrack-backend.git
cd protrack-backend
```

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install fastapi==0.135.2 uvicorn==0.42.0 \
  sqlalchemy psycopg2-binary \
  pydantic==2.12.5 \
  passlib[bcrypt]==1.7.4 \
  python-jose==3.5.0 \
  pandas==3.0.2 numpy==2.4.4 \
  scikit-learn==1.8.0 xgboost==3.2.0 joblib==1.5.3 \
  langchain==1.3.4 langchain-google-genai==4.2.4 \
  langgraph==1.2.4 google-genai==2.7.0 \
  python-dotenv==1.2.2
```

> **macOS only** — XGBoost requires OpenMP:
> ```bash
> brew install libomp
> ```

### 4. Create PostgreSQL database

```bash
psql -U postgres
```

```sql
CREATE DATABASE protrack_db;
\q
```

The default database URL in `app/database.py` is:
```
postgresql://srishti@localhost/protrack_db
```

Change this to match your PostgreSQL username:
```python
DATABASE_URL = "postgresql://your_username@localhost/protrack_db"
```

### 5. Create the `.env` file

Create a file named `.env` in the `protrack_backend/` root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=protrack-dev-secret-change-in-prod
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

> `JWT_SECRET_KEY` has a default fallback value. Always set a strong secret in production.

---

## ML Models

The `.pkl` model files are **not included** in the repository. You must generate them locally by running the training scripts.

### Step 1 — Generate training data

```bash
# Generates synthetic_completion.csv (500 rows)
python -m app.ml.generate_data

# Generates synthetic_resources.csv (800 rows)
python -m app.ml.generate_resource_data
```

### Step 2 — Train the models

```bash
# Trains RandomForest (delay risk) + GradientBoosting (completion time)
# Saves: delay_model.pkl, completion_model.pkl
python -m app.ml.train

# Trains XGBoost models for resource allocation
# Saves: resource_devs_model.pkl, resource_days_model.pkl
python -m app.ml.train_resource_model
```

After training, you should have these files in `app/ml/`:
```
app/ml/
├── delay_model.pkl
├── completion_model.pkl
├── resource_devs_model.pkl
└── resource_days_model.pkl
```

---

## Running the Server

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

Server runs at: **http://127.0.0.1:8000**

Interactive API docs (Swagger): **http://127.0.0.1:8000/docs**

ReDoc: **http://127.0.0.1:8000/redoc**

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | None | Register a new user |
| POST | `/login` | None | Login, returns JWT token |
| GET | `/users/me` | JWT | Get current user profile |
| GET | `/users` | Admin+ | List all users (paginated, searchable) |
| POST | `/users` | Admin+ | Create user (role-hierarchy enforced) |
| DELETE | `/users/{id}` | Admin+ | Delete user |

**Login request format:**
```
Content-Type: application/x-www-form-urlencoded
username=email@example.com&password=yourpassword
```

**Login response:**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

---

### Projects

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/projects` | JWT | List projects (paginated, searchable, filterable) |
| POST | `/projects` | Admin+ | Create project |
| GET | `/projects/{id}` | JWT | Get project details |
| PUT | `/projects/{id}/progress` | All roles | Update project progress |
| GET | `/projects/{id}/history` | JWT | Get progress history |
| GET | `/projects/{id}/tasks` | JWT | List tasks |
| POST | `/projects/{id}/tasks` | JWT | Create task |
| DELETE | `/tasks/{id}` | Admin+ | Delete task |
| PUT | `/tasks/{id}/status` | JWT | Update task status |
| GET | `/projects/{id}/members` | JWT | List members |
| POST | `/projects/{id}/members` | Admin+ | Add member |
| DELETE | `/projects/{id}/members/{member_id}` | Admin+ | Remove member |

**Query params for GET /projects:**
- `page` (default: 1)
- `limit` (default: 10)
- `search` (project name search)
- `status` (on_track / delayed / completed / all)

---

### Dashboard

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dashboard` | JWT | KPI summary (total, completed, delayed, on_track) |
| GET | `/workload` | JWT | Task count per team member |
| GET | `/resource-utilization` | JWT | Member count and task breakdown per project |
| GET | `/progress-over-time` | JWT | Average completion % grouped by month |

---

### ML Predictions

All prediction endpoints accept `POST` with JSON body.

#### Delay Risk + Completion Time

**Endpoint:** `POST /api/predictions/full-prediction`

**Request:**
```json
{
  "total_tasks": 20,
  "completed_tasks": 10,
  "delayed_tasks": 2,
  "team_size": 5,
  "completion_pct": 50,
  "task_completion_rate": 0.5,
  "delayed_task_rate": 0.1
}
```

**Response:**
```json
{
  "is_delayed": 0,
  "probability_on_track": 0.85,
  "probability_delayed": 0.15,
  "days_remaining": 15
}
```

Other prediction endpoints:
- `POST /api/predictions/delay-risk` — delay risk only
- `POST /api/predictions/completion-time` — days remaining only

---

#### Resource Allocation

**Endpoint:** `POST /api/predictions/resource-allocation`

**Request:**
```json
{
  "project_type": 0,
  "complexity": 2,
  "total_tasks": 20,
  "deadline_days": 90,
  "has_frontend": 1,
  "has_backend": 1,
  "has_ml": 0,
  "has_mobile": 0,
  "has_devops": 1,
  "has_database": 1
}
```

`project_type`: 0=Web, 1=Mobile, 2=ML/Data, 3=DevOps, 4=Embedded  
`complexity`: 1=Low, 2=Medium, 3=High

**Response:**
```json
{
  "required_developers": 7,
  "estimated_days": 45,
  "required_skill_sets": ["Frontend Development", "Backend Development", "DevOps / Infrastructure", "Database Administration"],
  "project_type_label": "Web Application",
  "complexity_label": "Medium"
}
```

---

### AI Chatbot

**Endpoint:** `POST /chat`  
**Auth:** Super Admin only

**Request:**
```json
{ "message": "Which projects are delayed?" }
```

**Response:**
```json
{ "reply": "Currently 3 projects are delayed: HR Management System (30%), Healthcare Patient Portal (40%), IoT Fleet Management System (25%)..." }
```

The chatbot uses a **LangGraph workflow**:
1. Fetches all project/task/member data from PostgreSQL (RAG context)
2. Injects context into Gemini prompt
3. Returns natural language response

---

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| name | String | Display name |
| email | String (unique) | Login email |
| password | String | bcrypt hash |
| role | String | team_lead / admin / super_admin |

### projects
| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| name | String | Project name |
| description | String | |
| status | String | on_track / delayed / completed |
| completion | Integer | 0–100 |
| deadline | String | Date string |
| team | String | Team name |

### tasks
| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| project_id | FK → projects | |
| title | String | |
| description | String | |
| status | String | pending / in_progress / completed / delayed |
| assigned_to | String | Member name |

### project_members
| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| project_id | FK → projects | |
| name | String | |
| role | String | e.g. Developer, Designer |
| email | String | Login email (optional) |
| created_at | DateTime | |

### progress_history
| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| project_id | FK → projects | |
| progress | Integer | 0–100 |
| task_name | String | What was updated |
| comments | String | Notes |
| status | String | on_track / delayed / completed |
| updated_at | DateTime | Timestamp |

---

## Role Permissions

| Action | Team Lead | Admin | Super Admin |
|--------|-----------|-------|-------------|
| Register / create users | ❌ | ✅ | ✅ |
| View all projects | ❌ | ✅ | ✅ |
| View own projects | ✅ | ✅ | ✅ |
| Create / delete projects | ❌ | ✅ | ✅ |
| Update project progress | ✅ | ✅ | ✅ |
| Manage tasks | ✅ | ✅ | ✅ |
| Add / remove members | ❌ | ✅ | ✅ |
| View dashboard analytics | ❌ | ✅ | ✅ |
| Use AI chatbot | ❌ | ❌ | ✅ |

---

## Notes

- `.env` is gitignored — create it manually after cloning
- `.pkl` model files are gitignored — run training scripts after cloning
- Tables are auto-created on server start via `Base.metadata.create_all()`
- The chatbot requires a valid Gemini API key with available quota
- CORS is configured for `localhost:5173`, `localhost:4173`, and `localhost:8080` — add your frontend URL if different
