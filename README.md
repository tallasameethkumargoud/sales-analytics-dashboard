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
