# 🚀 Data Operations Platform

A full-stack, production-grade **AI-powered Sales Analytics Platform** built with Django, PostgreSQL, Docker, and Groq LLaMA 3.3.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-6.0.3-green)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![AI](https://img.shields.io/badge/AI-Groq%20LLaMA%203.3-purple)

---

## ✨ Features

### 📊 Analytics Dashboard
- KPI Cards — Total Revenue, Avg Order Value, Top Product
- Interactive Bar Chart, Line Chart, Pie Chart (Chart.js)
- Product & revenue range filters
- CSV + PDF export

### 🤖 AI Features (Groq LLaMA 3.3)
- **Smart AI Chat** — Ask natural language questions about your data
- **AI Sales Forecast** — Linear regression trend prediction
- **AI Customer Analysis** — Pattern detection & segmentation
- **AI Recommendations Engine** — Per-product strategies (price, promote, upsell)
- **User Learning System** — Tracks clicks/dismissals, personalizes like Netflix/Amazon

### 👥 Multi-User Roles
| Role | Permissions |
|------|-------------|
| 👑 Admin | Full access, manage users, see all data |
| 📊 Analyst | Upload CSV, use AI, view analytics |
| 👁️ Viewer | Read-only dashboard |

### 🔐 Security & Infrastructure
- JWT-based session auth with password validation
- Docker + Docker Compose (3 containers)
- Gunicorn (3 workers) + Nginx reverse proxy
- HTTPS with SSL certificates
- Secrets managed via `.env` file

### 📱 Mobile Responsive
- Hamburger menu on mobile
- Stacked KPI cards, full-width charts
- Works on iPhone/Android

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0.3, Python 3.12 |
| Database | PostgreSQL 15 |
| AI | Groq LLaMA 3.3-70b |
| Data Processing | Pandas, NumPy, Scikit-learn |
| Frontend | HTML, CSS, JavaScript, Chart.js, jsPDF |
| Server | Gunicorn + Nginx |
| Containerization | Docker, Docker Compose |

---

## 🏗️ Architecture

```
Browser (HTTPS)
      ↓
   Nginx (port 443/80)     ← SSL termination + static files
      ↓
  Gunicorn (port 8000)     ← 3 worker processes
      ↓
  Django 6.0.3             ← App logic + AI APIs
      ↓
  PostgreSQL 15            ← Production database
```

---

## 📂 Project Structure

```
platform_backend/
├── datasets/
│   ├── models.py          # Dataset, Record, Customer, Product, UserProfile
│   ├── views.py           # All views + AI APIs
│   ├── decorators.py      # Role-based access control
│   └── migrations/
├── templates/
│   ├── analytics.html     # Main dashboard
│   ├── upload.html        # CSV upload
│   ├── datasets.html      # Dataset history
│   ├── admin_panel.html   # User management
│   ├── login.html
│   └── signup.html
├── platform_backend/
│   ├── settings.py
│   └── urls.py
├── nginx/
│   └── nginx.conf
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env                   # Never commit this!
```

---

## ▶️ Run Locally with Docker

### 1. Clone the repository
```bash
git clone https://github.com/tallasameethkumargoud/sales-analytics-dashboard.git
cd sales-analytics-dashboard
```

### 2. Create `.env` file
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Build and start
```bash
docker-compose up --build
```

### 4. Run migrations
```bash
docker-compose exec web python manage.py migrate
```

### 5. Create superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Open in browser
```
https://localhost
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/` | GET | KPI metrics |
| `/api/product-sales/` | GET | Product revenue data |
| `/api/sales-trend/` | GET | Daily revenue trend |
| `/api/sales-forecast/` | GET | AI forecast (7 days) |
| `/api/ai-chat/` | POST | AI data analyst chat |
| `/api/ai-sentiment/` | POST | Customer analysis |
| `/api/ai-recommendations/` | POST | Product recommendations |
| `/api/track-recommendation/` | POST | Track user interactions |
| `/api/update-user-role/` | POST | Admin: change user role |
| `/api/delete-user/` | POST | Admin: delete user |
| `/export/csv/` | GET | Export data as CSV |

---

## 📋 CSV Format

Your CSV must have these columns:
```
customer_name, product, amount
John Doe, Laptop, 1200
Jane Smith, Phone, 900
```

---

## 🔒 Environment Variables

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=data_platform
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432

GROQ_API_KEY=your-groq-api-key
```

---

## 👤 Author

**Sameeth Kumar Goud Talla**  
GitHub: [@tallasameethkumargoud](https://github.com/tallasameethkumargoud)