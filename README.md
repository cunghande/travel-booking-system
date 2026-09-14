# 🌍 Travel Booking System

> Tour Management & Booking System with AI Integration

**Developer:** Đỗ Văn Cung  
**Architecture:** Clean Architecture (FastAPI + PostgreSQL + Redis)  
**Status:** Week 1 / Sprint 1 — Core + Auth/RBAC ✅

---

## 🏗️ Architecture

```
Presentation (API Routes)     ← Thin controllers
       ↓
Application (Services/DTOs)   ← Business logic
       ↓
Domain (Entities/Enums)        ← Core rules
       ↓
Infrastructure (DB/Redis/Repos) ← Data access
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd Travel-Booking-System
cp .env.example .env
# Edit .env with your values
```

### 2. Start with Docker

```bash
docker compose up -d
```

### 3. Run Migrations

```bash
# Inside the api container
docker compose exec api alembic upgrade head

# Seed initial data (roles + admin user)
docker compose exec api python -m app.infrastructure.db.seed
```

### 4. Access

- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🔐 Default Admin Credentials

| Field | Value |
|-------|-------|
| Email | `admin@travelbooking.com` |
| Password | `Admin@123456` |

> ⚠️ Change these in `.env` for production!

---

## 📡 API Endpoints (Week 1)

### Authentication
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/v1/auth/register` | Public | Register new user |
| POST | `/api/v1/auth/login` | Public | Login, get JWT tokens |
| POST | `/api/v1/auth/refresh` | Public | Refresh access token |
| GET | `/api/v1/auth/me` | Authenticated | Get current user profile |

### User Management (Admin Only)
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/v1/users` | Admin | List all users (paginated) |
| GET | `/api/v1/users/{id}` | Admin | Get user by ID |
| PUT | `/api/v1/users/{id}` | Admin | Update user |
| POST | `/api/v1/users/{id}/roles` | Admin | Assign role to user |
| DELETE | `/api/v1/users/{id}/roles` | Admin | Remove role from user |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only
pytest tests/unit/ -v

# Integration tests (requires DB)
pytest tests/integration/ -v

# With coverage report
pytest --cov=app --cov-report=html
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.115 |
| Language | Python 3.11+ |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7.2 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic 1.13 |
| Auth | JWT (python-jose) + bcrypt |
| Workers | Celery 5.4 |
| Logging | Loguru |
| Testing | Pytest + httpx |
| Container | Docker + Docker Compose |

---

## 📁 Project Structure

```
app/
├── main.py                    # FastAPI application factory
├── api/v1/                    # API routes (thin controllers)
│   ├── auth.py
│   ├── users.py
│   └── router.py
├── application/               # Business logic layer
│   ├── services/              # Service classes
│   └── dto/                   # Pydantic schemas
├── domain/                    # Domain layer
│   ├── entities/              # SQLAlchemy models
│   └── value_objects/         # Enums, value objects
├── infrastructure/            # Infrastructure layer
│   ├── db/                    # Database config
│   ├── redis/                 # Redis client
│   └── repositories/         # Data access
├── workers/                   # Celery (placeholder)
└── core/                      # Cross-cutting concerns
    ├── config.py              # Settings
    ├── security.py            # JWT + hashing
    ├── dependencies.py        # DI + RBAC
    ├── exceptions.py          # Error handling
    └── logging.py             # Loguru config
```

---

## 📋 Roadmap

- [x] **Week 1:** Core Architecture + Auth/RBAC
- [ ] **Week 2:** Tour Catalog + Itinerary + Search
- [ ] **Week 3-4:** Booking Engine + Payment
- [ ] **Week 5-6:** Refund/Voucher + AI (Recommendation + RAG)
- [ ] **Week 7-8:** Reviews/Dashboard + Testing + Release
