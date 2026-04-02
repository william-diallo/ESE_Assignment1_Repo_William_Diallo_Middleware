# IMS Backend — Middleware (Django REST API)

**Inventory Management System — Enterprise Middleware Layer**  
William Diallo · BSc. Apprenticeship in Digital & Technology Solutions · ESE Assignment 1/2

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Application Structure](#4-application-structure)
5. [API Reference](#5-api-reference)
   - 5.1 [Authentication Endpoints](#51-authentication-endpoints)
   - 5.2 [Inventory Endpoints](#52-inventory-endpoints)
6. [Authentication & Authorisation](#6-authentication--authorisation)
7. [Business Logic & Domain Rules](#7-business-logic--domain-rules)
8. [Email Notification System](#8-email-notification-system)
9. [Security Design](#9-security-design)
10. [Rate Limiting (Throttling)](#10-rate-limiting-throttling)
11. [Settings & Environment Configuration](#11-settings--environment-configuration)
12. [Local Development Setup](#12-local-development-setup)
13. [Running Tests](#13-running-tests)
14. [Deployment (Render)](#14-deployment-render)
15. [Key Technical Decisions](#15-key-technical-decisions)
16. [Use of Generative AI](#16-use-of-generative-ai)

---

## 1. Project Overview

This repository contains the **middleware layer** of a three-tier enterprise Inventory Management System (IMS). It is a RESTful API built with Django and Django REST Framework, and acts as the sole intermediary between the React frontend and the PostgreSQL database. No client application ever accesses the database directly.

**Core capabilities:**

| Area | Features |
|---|---|
| User management | Registration, JWT login, token refresh, profile retrieval, password reset via email code |
| Inventory CRUD | Create, list, retrieve, update, partial update, delete inventory items |
| Role-based access | `ADMIN` and `STAFF` roles gate write operations; reads are open to all authenticated users |
| Email notifications | Low-stock alerts to all staff/admin users; password reset code delivery; password reset success confirmation — all via SendGrid |
| Audit logging | Signal-driven audit trail on every inventory item create, update, and delete |
| Security | JWT authentication, bcrypt password hashing, HSTS, per-endpoint rate limiting, anti-enumeration on password reset |

---

## 2. Architecture

This project follows a **three-layer enterprise architecture**:

```
┌──────────────────────────────────┐
│          React Frontend          │  (separate repository)
│  communicates only via REST API  │
└────────────────┬─────────────────┘
                 │ HTTPS / JSON
┌────────────────▼─────────────────┐
│     Django REST API (this repo)  │
│                                  │
│  ┌─────────────────────────────┐ │
│  │  accounts app               │ │
│  │  Auth, User model, Roles,   │ │
│  │  Password Reset, Throttles, │ │
│  │  Request Logging Middleware │ │
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │  inventory app              │ │
│  │  CRUD, Services, Signals,   │ │
│  │  Stock Status, Audit log    │ │
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │  notifications app          │ │
│  │  Email workflows, SendGrid  │ │
│  │  transport, HTML templates  │ │
│  └─────────────────────────────┘ │
└────────────────┬─────────────────┘
                 │ psycopg2
┌────────────────▼─────────────────┐
│         PostgreSQL Database      │
│  (accessed only via middleware)  │
└──────────────────────────────────┘
```

**Separation of concerns** is enforced at every layer:

- **Views** handle HTTP request/response only — no business logic.
- **Serialisers** handle validation and data transformation only.
- **Services** contain all business logic and are the only place that writes to the database.
- **Signals** handle side-effects (audit logging, email alerts) in reaction to model lifecycle events.
- **Notifications** is a dedicated app responsible solely for email delivery, with sub-modules for workflows, templates, transport, and recipient resolution.

**Request middleware stack (in order):**

```
CorsMiddleware → SecurityMiddleware → WhiteNoiseMiddleware → SessionMiddleware
→ CsrfViewMiddleware → AuthenticationMiddleware → RequestLoggingMiddleware
→ MessageMiddleware → XFrameOptionsMiddleware
```

`RequestLoggingMiddleware` (custom) logs every inbound request method, path, and client IP at `DEBUG` level, and echoes a client-supplied `X-Request-ID` header back in the response for distributed tracing.

---

## 3. Technology Stack

| Component | Technology | Version |
|---|---|---|
| Web framework | Django | 6.0.3 |
| REST API | Django REST Framework | 3.17.1 |
| Authentication | djangorestframework-simplejwt | 5.5.1 |
| Database | PostgreSQL via psycopg2-binary | 2.9.11 |
| Email | SendGrid (`django-sendgrid-v5` + `sendgrid`) | 1.3.1 / 6.12.5 |
| Static files | WhiteNoise (with Brotli) | ≥ 6.6.0 |
| WSGI server | Gunicorn | ≥ 23.0.0 |
| API documentation | drf-yasg (Swagger/OpenAPI) | 1.21.15 |
| CORS | django-cors-headers | 4.9.0 |
| DB URL parsing | dj-database-url | ≥ 2.1.0 |
| Environment loading | python-dotenv | 1.2.2 |

---

## 4. Application Structure

```
ims_backend/         # Django project configuration
│  settings.py           # Environment selector
│  settings_common.py    # Shared settings for all environments
│  settings_dev.py       # Development overrides (DEBUG=True)
│  settings_prod.py      # Production overrides (HSTS, SSL, cookies)
│  settings_test.py      # Test overrides (hardcoded keys, no SSL)
│  urls.py               # Root URL configuration

accounts/            # User management app
│  models.py             # Custom User model (email-based), PasswordResetCode
│  views.py              # Auth views (register, login, profile, password reset)
│  serialisers.py        # RegisterSerializer, CaseInsensitiveTokenObtainPairSerializer, etc.
│  services.py           # password reset business logic (request, confirm)
│  middleware.py         # RequestLoggingMiddleware
│  permissions.py        # IsStaffOrReadOnly, AllowAnonymousCreate
│  roles.py              # Role constants and helper functions
│  throttles.py          # Per-endpoint rate limit classes
│  urls.py               # Auth route definitions

inventory/           # Inventory domain app
│  models.py             # InventoryItem model with stock_status computed property
│  views.py              # InventoryItemViewSet (full CRUD, search, filtering)
│  serialisers.py        # Read and update serialisers
│  services.py           # CRUD business logic with role and validation checks
│  signals.py            # Audit logging and low-stock alert triggers
│  urls.py               # Router-based URL registration

notifications/       # Email delivery app
│  workflows.py          # Orchestration: low-stock alert, password reset emails
│  templates.py          # HTML and plain-text email template generators
│  transports.py         # SendGrid API client wrapper
│  recipients.py         # Admin/staff email address resolver
│  email_service.py      # Backward-compatibility re-export shim
```

---

## 5. API Reference

All endpoints are prefixed with `/api/`.

### 5.1 Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | No | Create a new user account |
| `POST` | `/api/auth/login/` | No | Obtain JWT access + refresh tokens |
| `POST` | `/api/auth/refresh/` | No (refresh token) | Obtain a new access token |
| `GET` | `/api/auth/me/` | Yes | Retrieve the authenticated user's profile |
| `POST` | `/api/auth/password-reset/request/` | No | Send a 6-digit reset code to the user's email |
| `POST` | `/api/auth/password-reset/confirm/` | No | Verify the code and set a new password |

#### Register — `POST /api/auth/register/`

```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

// Response 201
{
  "id": 1,
  "email": "user@example.com",
  "role": "STAFF",
  "is_active": true,
  "is_staff": false,
  "date_joined": "2026-03-01T10:00:00Z"
}
```

#### Login — `POST /api/auth/login/`

Email matching is **case-insensitive**.

```json
// Request
{ "email": "User@Example.COM", "password": "SecurePass123!" }

// Response 200
{ "access": "<jwt_access_token>", "refresh": "<jwt_refresh_token>" }
```

#### Password Reset Request — `POST /api/auth/password-reset/request/`

Always returns HTTP 200 regardless of whether the email exists, to prevent user enumeration.

```json
// Request
{ "email": "user@example.com" }

// Response 200 (production)
{ "detail": "If this email is registered, a reset code has been sent." }
```

#### Password Reset Confirm — `POST /api/auth/password-reset/confirm/`

```json
// Request
{ "email": "user@example.com", "code": "482910", "new_password": "NewSecurePass456!" }

// Response 200
{ "detail": "Password reset successful." }
```

---

### 5.2 Inventory Endpoints

All inventory endpoints require a valid JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

| Method | Endpoint | Roles Allowed | Description |
|---|---|---|---|
| `GET` | `/api/inventory/items/` | All authenticated | List all inventory items |
| `POST` | `/api/inventory/items/` | ADMIN, STAFF | Create a new inventory item |
| `GET` | `/api/inventory/items/{id}/` | All authenticated | Retrieve a single item |
| `PUT` | `/api/inventory/items/{id}/` | ADMIN, STAFF | Replace an inventory item |
| `PATCH` | `/api/inventory/items/{id}/` | ADMIN, STAFF | Partially update an inventory item |
| `DELETE` | `/api/inventory/items/{id}/` | ADMIN, STAFF | Delete an inventory item |

#### Query Parameters (List endpoint)

| Parameter | Filter Applied |
|---|---|
| `?name=` | Case-insensitive name contains |
| `?category=` | Case-insensitive category contains |
| `?description=` | Case-insensitive description contains |
| `?search=` | Searches across name, description, category, and item ID |

#### Inventory Item Schema

```json
{
  "id": 12,
  "name": "USB-C Dock",
  "description": "7-port USB-C hub with power delivery",
  "quantity": 4,
  "category": "Electronics",
  "status": "LOW_STOCK",
  "created_at": "2026-03-15T09:30:00Z",
  "updated_at": "2026-03-20T14:00:00Z",
  "created_by": "admin@company.com"
}
```

**`status` field values:**

| Value | Condition |
|---|---|
| `AVAILABLE` | `quantity >= 10` (configurable threshold) |
| `LOW_STOCK` | `0 < quantity < 10` |
| `OUT_OF_STOCK` | `quantity == 0` |

The `status` field is computed server-side and is read-only. It cannot be set directly.

---

## 6. Authentication & Authorisation

### JWT Authentication

This API uses **JSON Web Token (JWT)** authentication via `djangorestframework-simplejwt`. Sessions and cookies are not used for API authentication.

- Access tokens are short-lived and sent as a `Bearer` token in the `Authorization` header.
- Refresh tokens are used to obtain new access tokens without re-entering credentials.
- The only authentication class configured globally is `JWTAuthentication`; session auth is not enabled for the API.

### Custom User Model

The project uses a **custom `User` model** (`accounts.User`) that replaces Django's default:

- `email` is the login identifier (`USERNAME_FIELD = "email"`); `username` is removed entirely.
- Email login is **case-insensitive** — the serialiser normalises the email before lookup.
- Two roles are available: `ADMIN` and `STAFF`. Both are treated as privileged for write operations.

### Permission Classes

| Class | Behaviour |
|---|---|
| `IsStaffOrReadOnly` | `GET`/`HEAD`/`OPTIONS` allowed for any authenticated user. Write methods (`POST`, `PUT`, `PATCH`, `DELETE`) require the user to have the `ADMIN` or `STAFF` role, `is_staff=True`, or `is_superuser=True`. |
| `AllowAnonymousCreate` | `POST` is permitted without authentication (for user registration). All other methods require a valid JWT. |

The `has_privileged_role()` helper in `accounts/roles.py` centralises role evaluation and is reused by both the permission classes and the service layer, ensuring consistent enforcement.

---

## 7. Business Logic & Domain Rules

All write operations are delegated to **service functions** in `accounts/services.py` and `inventory/services.py`. Views call services; services own the business rules.

### Password Reset Flow

1. Client POSTs email to `/api/auth/password-reset/request/`.
2. Service invalidates all existing unused reset codes for that user.
3. A new cryptographically random 6-digit code is generated and stored with an expiry timestamp (default: 10 minutes, configured via `PASSWORD_RESET_CODE_EXPIRY_MINUTES`).
4. A SendGrid email is dispatched with the code.
5. Client submits email + code + new password to `/api/auth/password-reset/confirm/`.
6. Serialiser validates the code is unexpired and unused; service sets the new password and marks all reset codes for that user as used.
7. A confirmation email is sent on success.

### Inventory Business Rules

- **Quantity** must be a non-negative integer (`min_value=0`). The serialiser rejects negative values on create and update.
- **Stock status** (`AVAILABLE`, `LOW_STOCK`, `OUT_OF_STOCK`) is computed automatically from the quantity field. `LOW_STOCK_THRESHOLD` defaults to 10.
- **Low-stock alert emails** are sent to all admin/staff users when an item's status transitions *into* `LOW_STOCK` from any other state. This is trigger once per transition, not on every update.
- `created_by` is automatically set to the requesting user's email on creation; it cannot be set by the client.
- **Unknown fields** on update are rejected with a 400 error by the service layer.

### Signal-Driven Audit Log

Three Django signal handlers provide a full audit trail for inventory items:

| Event | Handler | Action |
|---|---|---|
| Item created | `post_save` | Logs a structured JSON snapshot of the new item |
| Item updated | `post_save` | Logs before/after JSON snapshots; fires low-stock email if threshold crossed |
| Item deleted | `post_delete` | Logs a structured JSON snapshot of the deleted item |

The `pre_save` signal caches the item's previous state from the database before it is overwritten, making before/after comparison possible.

---

## 8. Email Notification System

Emails are sent via **SendGrid** and are handled exclusively by the `notifications` app. The service layer and signal handlers call workflow functions; the workflow functions orchestrate template generation and transport. No other part of the codebase sends email directly.

### Email Types

| Email | Trigger | Recipients |
|---|---|---|
| Password reset code | User requests a reset | The requesting user |
| Password reset success | Reset confirmed | The requesting user |
| Low-stock alert | Item transitions into `LOW_STOCK` | All users with `ADMIN`/`STAFF` role, `is_staff=True`, or `is_superuser=True` |

### Email Module Structure

| Module | Responsibility |
|---|---|
| `workflows.py` | Orchestration — checks API key, selects recipients, calls template and transport |
| `templates.py` | Generates HTML and plain-text email bodies |
| `transports.py` | Wraps the SendGrid Python SDK; returns `True` on HTTP 202; logs errors without raising |
| `recipients.py` | Queries the database for all admin/staff email addresses |
| `email_service.py` | Re-export shim for backward compatibility |

If `SENDGRID_API_KEY` is not set, all email functions return `False` with a warning log entry — the application continues to function normally.

---

## 9. Security Design

| Concern | Implementation |
|---|---|
| Password storage | Django's `PBKDF2PasswordHasher` (default); `validate_password` enforced in `RegisterSerializer` |
| Authentication | JWT Bearer tokens; no session-based auth for the API |
| Transport security | `SECURE_SSL_REDIRECT=True` and `SECURE_HSTS_SECONDS=31536000` (1 year) in production |
| Cookie hardening | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `__Host-` cookie prefix in production |
| User enumeration prevention | Password reset request always returns HTTP 200 with a generic message; debug information (`email_matched`, `email_sent`) is only exposed when `DEBUG=True` |
| Rate limiting | Per-endpoint throttles prevent brute-force attacks on login, registration, and password reset (see §10) |
| CORS | `CORS_ALLOW_ALL_ORIGINS=True` in development; production restricts to the explicit frontend origin via `FRONTEND_ORIGIN` environment variable |
| Secret management | All secrets (`SECRET_KEY`, `SENDGRID_API_KEY`, database credentials) are loaded exclusively from environment variables — never hardcoded |
| Static files | Served by WhiteNoise; no user-uploaded file handling on the server |
| Input validation | DRF serialiser validation on all inputs; service layer performs a second validation pass for business rules |

---

## 10. Rate Limiting (Throttling)

Custom throttle classes in `accounts/throttles.py` apply per-endpoint limits to protect against abuse:

| Throttle Class | Applies To | Limit |
|---|---|---|
| `LoginRateThrottle` | `POST /api/auth/login/` | 5 requests / minute (by IP) |
| `RegisterRateThrottle` | `POST /api/auth/register/` | 10 requests / hour (by IP) |
| `PasswordResetRateThrottle` | Both password reset endpoints | 5 requests / hour (by IP) |
| `TokenRefreshRateThrottle` | `POST /api/auth/refresh/` | 30 requests / minute (by IP) |
| `InventoryWriteRateThrottle` | Create / update / delete inventory | 60 requests / hour (by user) |
| `ProfileRateThrottle` | `GET /api/auth/me/` | 120 requests / hour (by user) |

Global fallback limits: anonymous users 100/hour, authenticated users 1000/hour.

---

## 11. Settings & Environment Configuration

The settings module is split by environment. The active environment is selected by the `DJANGO_ENV` environment variable at startup:

| `DJANGO_ENV` | Module loaded | Use case |
|---|---|---|
| *(unset)* | `settings_dev` | Local development |
| `prod` | `settings_prod` | Production (Render) |
| *(test runner detected)* | `settings_test` | Automated testing |

All shared configuration lives in `settings_common.py`. Environment-specific files only override what differs.

### Required Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `exv13d3ywo$*(#id_3=...` |
| `POSTGRES_DB` | Database name | `ims_db` |
| `POSTGRES_USER` | Database user | `ims_user` |
| `POSTGRES_PASSWORD` | Database password | `ims_password` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `SENDGRID_API_KEY` | SendGrid API key | `SG.xxx...` |
| `DEFAULT_FROM_EMAIL` | Sender email address | `admin@example.com` |

### Optional Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ADMIN_PANEL_URL` | URL embedded in low-stock alert emails | `http://localhost:8000/admin/...` |
| `PASSWORD_RESET_CODE_EXPIRY_MINUTES` | Validity window for reset codes | `10` |
| `FRONTEND_ORIGIN` | Allowed CORS origin in production | *(none)* |
| `DATABASE_URL` | Full database URL (used on Render) | *(derived from individual POSTGRES_* vars)* |

For local development, copy the template below to a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-local-secret-key
POSTGRES_DB=ims_db
POSTGRES_USER=ims_user
POSTGRES_PASSWORD=ims_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
SENDGRID_API_KEY=
DEFAULT_FROM_EMAIL=noreply@example.com
ADMIN_PANEL_URL=http://localhost:8000/admin/inventory/inventoryitem/
PASSWORD_RESET_CODE_EXPIRY_MINUTES=10
```

> **Note:** Never commit `.env` to version control. The file is listed in `.gitignore`.

---

## 12. Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ running locally
- A SendGrid account with a verified sender address (optional — the app runs without it)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/william-diallo/ESE_Assignment1_Repo_William_Diallo_Middleware.git
cd ESE_Assignment1_Repo_William_Diallo_Middleware

# 2. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file and populate it (see §11 above)

# 5. Create the PostgreSQL database and user
psql -U postgres -c "CREATE DATABASE ims_db;"
psql -U postgres -c "CREATE USER ims_user WITH PASSWORD 'ims_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ims_db TO ims_user;"

# 6. Run database migrations
python manage.py migrate

# 7. (Optional) Create a superuser for the Django admin panel
python manage.py createsuperuser

# 8. Start the development server
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`.  
The Django admin panel is available at `http://localhost:8000/admin/`.

---

## 13. Running Tests

The test suite uses Django's built-in test runner. A dedicated `settings_test.py` is automatically selected when tests are run.

```bash
# Run all tests
python manage.py test

# Run tests with coverage report
python -m coverage run --rcfile=.coveragerc manage.py test
python -m coverage report

# Generate an HTML coverage report
python -m coverage html
# Open htmlcov/index.html in a browser
```

### Test Coverage Summary

| Metric | Value |
|---|---|
| Total statements | 524 |
| Total branches | 82 |
| **Overall line coverage** | **~80%** |

### Test Suite Overview

| App | Test Class | What is tested |
|---|---|---|
| `accounts` | `UserAndResetCodeModelTests` | `is_expired` property on `PasswordResetCode` (before and after expiry) |
| `accounts` | `PermissionClassTests` | `IsStaffOrReadOnly` allows safe methods, blocks writes for non-admin; `AllowAnonymousCreate` permits unauthenticated POST |
| `accounts` | `SerializerUnitTests` | `RegisterSerializer` hashes passwords correctly; `PasswordResetConfirmSerializer` rejects invalid codes |
| `accounts` | `MiddlewareUnitTests` | `RequestLoggingMiddleware` echoes `X-Request-ID` header in response |
| `accounts` | `PasswordResetViewUnitTests` | Unknown email returns generic 200; valid code resets password, marks code used, triggers confirmation email |
| `accounts` | `EmailServiceUnitTests` | Missing API key returns `False`; valid key triggers SendGrid transport |
| `accounts` | `AuthenticationIntegrationTests` | Full flow: register → login (case-insensitive email) → retrieve profile → refresh token |
| `inventory` | `InventoryModelUnitTests` | `stock_status` returns correct value at `OUT_OF_STOCK`, `LOW_STOCK`, and `AVAILABLE` thresholds |
| `inventory` | `InventoryServiceUnitTests` | Non-privileged user raises `PermissionDenied`; negative quantity raises `ValidationError`; unknown update field raises `ValidationError`; delete removes item; search finds by name |
| `inventory` | `InventorySignalsUnitTests` | Low-stock alert email is sent exactly once when status transitions into `LOW_STOCK` |
| `inventory` | `InventoryCrudIntegrationTests` | Full authenticated flow: create → list → PATCH (quantity update) → delete |

---

## 14. Deployment (Render)

This project is configured for deployment on the **Render free tier** using `render.yaml` (Infrastructure-as-Code).

### Services Defined in `render.yaml`

| Resource | Type | Name |
|---|---|---|
| Web service | Python (Gunicorn) | `ims-backend` |
| Database | PostgreSQL (free) | `ims-db` |

### Build and Start Commands

| Stage | Command |
|---|---|
| Build | `./build.sh` — installs dependencies, collects static files, runs migrations |
| Start | `gunicorn ims_backend.wsgi:application` |

### Production Environment Variables (set on Render)

| Variable | Source |
|---|---|
| `DJANGO_ENV` | `prod` (hardcoded in `render.yaml`) |
| `SECRET_KEY` | Auto-generated by Render |
| `DATABASE_URL` | Auto-injected from linked PostgreSQL service |
| `SENDGRID_API_KEY` | Set manually in Render dashboard |
| `DEFAULT_FROM_EMAIL` | Set manually in Render dashboard |
| `FRONTEND_ORIGIN` | Set manually (React frontend Render URL) |
| `ADMIN_PANEL_URL` | Set manually |

### Production Security Settings (active when `DJANGO_ENV=prod`)

- `DEBUG = False`
- `SECURE_SSL_REDIRECT = True`
- `SECURE_HSTS_SECONDS = 31536000` (1 year, with preload)
- `SESSION_COOKIE_SECURE = True` with `__Host-` prefix
- `CSRF_COOKIE_SECURE = True` with `__Host-` prefix
- Static files served via `WhiteNoise.CompressedManifestStaticFilesStorage` (with Brotli compression)
- `ALLOWED_HOSTS` automatically includes `RENDER_EXTERNAL_HOSTNAME`

### Deployed URL

The live backend API is deployed at:  
**`https://ims-backend-8qwe.onrender.com/`**

> Deployment links are included in the video demonstration submission. Free-tier PostgreSQL on Render will remain active for at least three weeks from the submission date (27 March 2026).

---

## 15. Key Technical Decisions

### Custom `User` model with email-based authentication
Django's default user model uses `username` as the login identifier. This was replaced with a custom `AbstractUser` subclass that uses `email` as `USERNAME_FIELD`. This is a common enterprise pattern that avoids the need for users to manage a separate username and simplifies user identification across systems.

### Service layer pattern
All business logic lives in service modules (`accounts/services.py`, `inventory/services.py`), not in views or serialisers. Views are kept thin — they validate input via serialisers, call a service, and return a response. This improves testability (services can be unit-tested without HTTP), maintainability (business rules are co-located), and makes it straightforward to expose the same logic via different interfaces.

### Signal-driven audit trail and notifications
Django signals (`pre_save`, `post_save`, `post_delete`) were used for audit logging and low-stock alerts rather than embedding these side-effects inside the service layer. This keeps the service layer focused on state mutation while signals handle cross-cutting concerns. The trade-off is that signal handlers can be harder to trace, but their use is limited and well-documented here.

### Dedicated `notifications` app
Email delivery is completely isolated from the `accounts` and `inventory` apps. The `notifications` app owns all email concerns: template generation, SendGrid transport, and recipient resolution. This means swapping the email provider requires changing only `transports.py`.

### Anti-enumeration on password reset
The password reset request endpoint always returns the same generic HTTP 200 response, whether or not the email address is registered. This prevents attackers from using the endpoint to discover which email addresses have accounts. Debug-mode extras (`email_matched`, `email_sent`) are only exposed in development.

### Environment-split settings
Rather than a single `settings.py` with conditionals, the settings are split into four files: `settings_common.py` (shared), `settings_dev.py`, `settings_prod.py`, and `settings_test.py`. This makes it unambiguous which settings apply in each context and prevents accidental use of development settings in production.

### Per-endpoint rate limiting
DRF's built-in throttling was extended with custom throttle classes for each sensitive endpoint (login, registration, token refresh, password reset, inventory writes, profile). This provides fine-grained protection against brute-force and enumeration attacks without relying on a third-party package or infrastructure-level solution.

---

## 16. Use of Generative AI

**GitHub Copilot** was used during the development of this project to support:

- Drafting initial docstring and inline comment templates, which were then reviewed, corrected, and integrated manually.
- Suggesting boilerplate patterns for Django signal handlers and DRF viewsets, which were then adapted to the project's service-layer architecture.
- Explaining specific `djangorestframework-simplejwt` configuration options during initial setup.
- Assisting with `render.yaml` syntax and Render deployment configuration.

All AI-generated suggestions were critically evaluated before use. The architectural decisions, security design, business logic, and test coverage strategy are the author's own work. Full understanding of every line of code in this repository was maintained throughout development, as required by the module's YELLOW AI classification.

