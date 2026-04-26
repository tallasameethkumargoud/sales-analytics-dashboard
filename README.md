# 🚀 Data Operations Platform — AI-Powered Sales Analytics

A production-grade, AI-powered **Sales Analytics SaaS Platform** built with Django, PostgreSQL, Docker, and Groq LLaMA 3.3 — complete with CI/CD pipeline, 66 automated tests, role-based access, Sentry monitoring, and Railway cloud deployment.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0.3-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![AI](https://img.shields.io/badge/AI-Groq%20LLaMA%203.3%2070B-8B5CF6)
![Tests](https://img.shields.io/badge/Tests-66%20passing-22C55E?logo=pytest&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway&logoColor=white)
![Sentry](https://img.shields.io/badge/Monitoring-Sentry-362D59?logo=sentry&logoColor=white)

> **Live Demo:** [sales-analytics-dashboard-production.up.railway.app](https://sales-analytics-dashboard-production.up.railway.app)

---

## 📌 What This Project Does

Users upload CSV sales data and instantly get:

- **Interactive dashboard** with KPI cards, bar/line/pie charts, and filters
- **AI-powered insights** — ask questions in natural language, get data-driven answers
- **Sales forecasting** — 7-day revenue predictions with trend analysis
- **Customer segmentation** — AI identifies VIPs, spending tiers, and patterns
- **Smart recommendations** — per-product strategies that learn from your behavior
- **Multi-user roles** — Admin, Analyst, and Viewer with granular permissions
- **One-click exports** — CSV and PDF reports

---

## ✨ Features

### 📊 Analytics Dashboard
- **KPI Cards** — Total Revenue, Average Order Value, Top Product
- **Interactive Charts** — Bar (revenue by product), Line (daily trend), Pie (distribution) via Chart.js
- **Smart Filters** — Product and price range sliders with real-time chart updates
- **Sales Forecast** — NumPy linear regression projects next 7 days with AI-generated trend explanation
- **Export** — Download reports as CSV or PDF (jsPDF)

### 🤖 AI Features (Groq LLaMA 3.3-70B)

| Feature | What It Does |
|---------|-------------|
| **Smart AI Chat** | Ask natural language questions — AI answers with exact numbers from your real data |
| **Sales Forecast** | Linear regression trend prediction + AI explanation in plain English |
| **Customer Analysis** | Name origin patterns, spending tiers, VIP identification, diversity scoring |
| **Recommendations Engine** | Per-product strategies: increase price, promote, upsell, bundle, discount, discontinue |
| **User Learning System** | Tracks clicks/applies/dismissals → personalizes future recommendations (Netflix-style) |

### 👥 Multi-User Roles

| Role | Permissions |
|------|-------------|
| 👑 **Admin** | Everything + manage users via Admin Panel + delete accounts + change roles |
| 📊 **Analyst** | Upload CSV, use AI features, view analytics, export data |
| 👁️ **Viewer** | Read-only dashboard access |

Role enforcement via custom `@role_required` and `@api_role_required` decorators at both view and API levels. Templates use `{% if is_admin %}` for conditional UI rendering.

### 🔐 Security
- Session-based auth with password validation (8+ chars, uppercase, number, special character)
- HTTPS with SSL certificates (Nginx SSL termination)
- CSRF protection on all forms
- Environment variables for all secrets (`.env` file, never hardcoded)
- `SECURE_PROXY_SSL_HEADER` configured for Railway proxy

### 📱 Mobile Responsive
- Hamburger menu (≡) with slide-down navigation on mobile
- Stacked KPI cards and full-width charts below 768px
- Touch-friendly UI across all 8 templates
- Works on iPhone and Android

### 🧪 Testing — 66 Automated Tests
- **test_models.py** (138 lines) — Model creation, relationships, string representations
- **test_auth.py** (126 lines) — Login, signup, password validation, session management
- **test_api.py** (211 lines) — All API endpoints end-to-end, auth checks, data filtering, user isolation
- **test_views.py** (117 lines) — Page rendering, redirects, role-based access control

Uses `pytest-django`, `factory_boy` for clean test data, and SQLite in-memory DB for fast local tests.

### 🔄 CI/CD Pipeline (GitHub Actions)
Every `git push` to `main` triggers:

- **Test Job** — Spins up Ubuntu + PostgreSQL 15, installs dependencies, runs all 66 tests with `coverage`
- **Lint Job** — Runs `flake8` for code style checks

Both pass → Railway auto-deploys the new version. Bad code is blocked automatically.

### 🔍 Sentry Error Monitoring
- Real-time error tracking with `sentry-sdk` + `DjangoIntegration`
- Full stack traces, user info, browser, OS, and request context
- Email alerts on unhandled exceptions
- Conditional init — only activates when `SENTRY_DSN` is set

### ⚡ Redis Caching
- Caches expensive DB queries for 10x faster response times
- Leverages `django-redis` for easy integration with Django
- Stores cached data in Redis with a 5-minute expiry
- Implements cache invalidation on new data uploads
- Significantly reduces database load, especially with multiple concurrent users
- Improves overall application performance and scalability

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 6.0.3, Python 3.12, Django REST Framework |
| **Database** | PostgreSQL 15 (Railway in production, Docker locally) |
| **Caching** | Redis 7 (Docker container) |
| **AI** | Groq LLaMA 3.3-70B via Groq API |
| **Data Processing** | Pandas, NumPy, Scikit-learn |
| **Frontend** | HTML, CSS, JavaScript, Chart.js, jsPDF |
| **Server** | Gunicorn (3 workers) + Nginx (reverse proxy + SSL) |
| **Containerization** | Docker, Docker Compose (4 containers) |
| **Deployment** | Railway (auto-deploy from GitHub) |
| **CI/CD** | GitHub Actions (test + lint pipeline) |
| **Monitoring** | Sentry (real-time error tracking) |
| **Testing** | pytest, factory_boy, coverage, flake8 |

---

## 🏗️ Architecture

```
                    Internet
                       │
              GitHub Repository
             ┌─────────┴─────────┐
       GitHub Actions         Railway Cloud
       (CI/CD Pipeline)       (Production)
             │                     │
       Run 66 tests          Nginx (port 443/80)
       Run flake8            SSL termination
       ✅ Pass               static files
             │                     │
       Auto-deploy ──→       Gunicorn (port 8000)
                             3 worker processes
                                   │
                             Django 6.0.3
                             ├── Auth (signup/login/roles)
                             ├── Upload (CSV → Pandas → DB)
                             ├── Analytics (ORM aggregates)
                             ├── AI APIs (Groq LLaMA 3.3)
                             │    ├── Smart Chat
                             │    ├── Sales Forecast
                             │    ├── Customer Analysis
                             │    └── Recommendations
                             └── Sentry (error monitoring)
                                   │
                             PostgreSQL 15
                             ├── Dataset, Record
                             ├── Customer, Product
                             ├── UserProfile (roles)
                             └── RecommendationInteraction
```

---

## 📂 Project Structure

```
sales-analytics-dashboard/
├── datasets/
│   ├── models.py              # 5 models: Dataset, Record, Customer, Product,
│   │                          #   UserProfile, RecommendationInteraction
│   ├── views.py               # All views + 4 AI API endpoints (694 lines)
│   ├── decorators.py          # @role_required, @api_role_required
│   ├── admin.py               # Django admin config
│   ├── tests/
│   │   ├── factories.py       # factory_boy test data factories
│   │   ├── test_models.py     # 138 lines — model unit tests
│   │   ├── test_auth.py       # 126 lines — auth integration tests
│   │   ├── test_api.py        # 211 lines — API endpoint tests
│   │   └── test_views.py      # 117 lines — view + role tests
│   └── migrations/
├── templates/
│   ├── analytics.html         # Main dashboard (677 lines, Chart.js, AI panels)
│   ├── upload.html            # CSV upload with preview (488 lines)
│   ├── admin_panel.html       # User management (218 lines)
│   ├── datasets.html          # Dataset history (329 lines)
│   ├── login.html             # Login page
│   ├── signup.html            # Registration with validation
│   ├── records.html           # Data records view
│   └── success.html           # Upload confirmation
├── platform_backend/
│   ├── settings.py            # PostgreSQL, Sentry, Groq, session config
│   ├── test_settings.py       # SQLite in-memory for fast tests
│   ├── urls.py                # 20 URL patterns
│   └── wsgi.py
├── nginx/
│   └── nginx.conf             # HTTPS, reverse proxy, static file serving
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI/CD: test + lint jobs
├── Dockerfile                 # Python 3.12-slim, Gunicorn CMD
├── docker-compose.yml         # 3 services: web, db, nginx
├── railway.json               # Railway deployment config
├── requirements.txt           # 17 dependencies
├── pytest.ini                 # Test configuration
├── setup.cfg                  # flake8 config
└── .env                       # Secrets (never committed)
```


## ▶️ Run Locally with Docker

### 1. Clone
```bash
git clone https://github.com/tallasameethkumargoud/sales-analytics-dashboard.git
cd sales-analytics-dashboard
```

### 2. Create `.env` file
```bash
cat > .env << EOF
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=data_platform
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0

GROQ_API_KEY=your-groq-api-key
SENTRY_DSN=               # optional — leave blank to disable
EOF
```

### 3. Build and start all containers
```bash
docker-compose up --build
```

### 4. Run migrations
```bash
docker-compose exec web python manage.py migrate
```

### 5. Create a superuser (Admin role)
```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Open in browser
https://localhost        # HTTPS (self-signed cert — accept the warning)
http://localhost:80      # Redirects to HTTPS

---

## 🧪 Run Tests Locally

```bash
# No Docker or PostgreSQL needed — tests use SQLite in-memory
pip install -r requirements.txt
pytest                              # Run all 66 tests
pytest --tb=short                   # Shorter output
coverage run -m pytest && coverage report   # With coverage
```

---

## 📡 API Endpoints

| Endpoint | Method | Auth | Role | Description |
|----------|--------|------|------|-------------|
| `/upload/` | POST | ✅ | Any | Upload CSV dataset |
| `/preview/` | POST | ✅ | Any | Preview CSV before upload |
| `/api/analytics/` | GET | ✅ | Any | KPI metrics (revenue, AOV, top product) |
| `/api/product-sales/` | GET | ✅ | Any | Product revenue data (supports `?min=&max=` filters) |
| `/api/sales-trend/` | GET | ✅ | Any | Daily revenue trend |
| `/api/sales-forecast/` | GET | ✅ | Any | 7-day AI forecast + trend explanation |
| `/api/ai-chat/` | POST | ✅ | Any | Natural language data Q&A |
| `/api/ai-sentiment/` | POST | ✅ | Any | Customer analysis + segmentation |
| `/api/ai-recommendations/` | POST | ✅ | Any | Personalized product strategies |
| `/api/track-recommendation/` | POST | ✅ | Any | Track user interaction (click/apply/dismiss) |
| `/api/update-user-role/` | POST | ✅ | Admin | Change a user's role |
| `/api/delete-user/` | POST | ✅ | Admin | Delete a user account |
| `/export/csv/` | GET | ✅ | Any | Download sales data as CSV |

---

## 📋 CSV Format

Your CSV file must include these columns:

```csv
customer_name,product,amount
John Doe,Laptop,1200
Jane Smith,Phone,900
Alice Johnson,Tablet,650
Bob Williams,Laptop,1350
```

- **Max file size:** 5MB
- **Format:** CSV only
- Preview is shown before upload for validation

---

## 🔒 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key |
| `DEBUG` | ✅ | `True` for dev, `False` for production |
| `ALLOWED_HOSTS` | ✅ | Comma-separated hostnames |
| `DB_NAME` | ✅ | PostgreSQL database name |
| `DB_USER` | ✅ | PostgreSQL username |
| `DB_PASSWORD` | ✅ | PostgreSQL password |
| `DB_HOST` | ✅ | `db` for Docker, `localhost` for local |
| `DB_PORT` | ✅ | PostgreSQL port (default: `5432`) |
| `DATABASE_URL` | ⚡ | Railway auto-sets this (overrides individual DB vars) |
| `REDIS_URL` | ✅ | Redis connection URL (default: `redis://redis:6379/0`) |
| `GROQ_API_KEY` | ✅ | Groq API key for AI features |
| `SENTRY_DSN` | ❌ | Sentry DSN for error monitoring (optional) |

---

## ☁️ Deploy to Railway

1. Push your code to GitHub
2. Connect the repo to [Railway](https://railway.app)
3. Railway auto-detects the `Dockerfile` and builds
4. Add a **PostgreSQL** plugin in Railway
5. Add a **Redis** plugin in Railway
6. Set environment variables in Railway's **Variables** tab:

- `SECRET_KEY`, `GROQ_API_KEY`, `DEBUG=False`
  - `ALLOWED_HOSTS=your-app.up.railway.app`
  - `DATABASE_URL` is auto-set by Railway's PostgreSQL plugin
  - `REDIS_URL` is auto-set by Railway's Redis plugin

7. Deploy — your app is live at `https://your-app.up.railway.app`

---

## 🔄 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml — runs on every push to main

Job 1: 🧪 Run Tests
  → Ubuntu + PostgreSQL 15 service
  → pip install dependencies
  → python manage.py migrate
  → coverage run -m pytest (66 tests)

Job 2: 🔍 Code Quality
  → flake8 linting
  → Code style enforcement

Both pass → Railway auto-deploys ✅
Either fails → Deploy blocked ❌
```

---

## 🗃️ Database Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `Dataset` | Uploaded CSV file | name, file, uploaded_by, uploaded_at |
| `Customer` | Unique customer | name |
| `Product` | Unique product | name |
| `Record` | Individual sale | dataset, customer, product, amount |
| `UserProfile` | Role assignment | user (OneToOne), role (admin/analyst/viewer) |
| `RecommendationInteraction` | AI learning | user, product, action_type, interaction, impact |

---

## 👤 Author

**Sameeth Kumar Goud Talla**
GitHub: [@tallasameethkumargoud](https://github.com/tallasameethkumargoud)
