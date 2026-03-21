# 📊 Sales Analytics Dashboard (Django + Chart.js)

An interactive analytics dashboard built using **Django (backend)** and **Chart.js (frontend)** to visualize sales data and enable dynamic user-driven insights.

---

## 🚀 Features

- 📈 KPI Cards (Total Revenue, Average Order Value, Top Product)
- 📊 Bar Chart for product-wise revenue
- 🥧 Pie Chart for product distribution
- 🔍 Dynamic product filtering with highlight-based UX
- ⚡ Real-time updates without page reload
- 🔗 REST API integration using Django

---

## 🛠️ Tech Stack

- **Backend:** Django, Django REST Framework  
- **Frontend:** HTML, CSS, JavaScript  
- **Visualization:** Chart.js  
- **Database:** SQLite  

---

## 📂 Project Structure
sales-analytics-dashboard/
│
├── datasets/ # Django app (models, views, APIs)
├── templates/ # HTML templates
├── static/ # CSS & JS files
├── manage.py
├── requirements.txt
└── README.md


---

## ▶️ How to Run Locally

### 1. Clone the repository
git clone https://github.com/tallasameethkumargoud/sales-analytics-dashboard.git

cd sales-analytics-dashboard


### 2. Create virtual environment
python -m venv venv
source venv/bin/activate # Mac/Linux


### 3. Install dependencies
pip install -r requirements.txt


### 4. Run migrations
python manage.py migrate

### 5. Start server


python manage.py runserver


Open in browser:

http://127.0.0.1:8000/


---

## 📊 API Endpoints

| Endpoint | Description |
|--------|-------------|
| `/api/analytics/` | KPI metrics |
| `/api/product-sales/` | Product-wise revenue data |

---

## 🧠 Key Highlight

This dashboard uses **contextual filtering instead of removing data**:

- Selected product → highlighted  
- Other products → faded  

👉 This helps users retain full context while focusing on specific insights.

---

## 📸 Screenshots



---

## 📌 Future Improvements

- Multi-select filters (product + date)
- Export data (CSV / PDF)
- User authentication
- Deployment (AWS / Render)

---

## 👤 Author

**Sameeth Kumar Goud Talla**  
GitHub: https://github.com/tallasameethkumargoud
