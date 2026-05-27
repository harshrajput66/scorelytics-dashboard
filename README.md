# 📊 Scorelytics — Student Performance Analytics Dashboard

A clean, minimal **Streamlit** dashboard for tracking student academic performance across **Class 11 & 12** in four streams: Medical, Non-Medical, Commerce, and Arts.

---

## 🚀 Features

- **Overview Dashboard** — School-wide KPIs, score distribution, subject averages, and correlation charts
- **Student Profiles** — Filter students by risk level, grade, and attendance; view individual score breakdowns and generate PDF report cards
- **Database Explorer** — Inspect raw SQLite tables and run custom SQL queries in the browser

---

## 🏫 School Setup

| Stream | Subjects |
|---|---|
| Medical | Physics, Chemistry, Biology, English, Physical Education |
| Non-Medical | Physics, Chemistry, Mathematics, English, Computer Science |
| Commerce | Accountancy, Business Studies, Economics, English, Mathematics |
| Arts | History, Political Science, Geography, English, Hindi |

- 500 mock students with Indian names
- Classes: **Class 11** and **Class 12**
- Risk classification: High / Medium / Low based on score + attendance

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/scorelytics-dashboard.git
cd scorelytics-dashboard
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

The database and mock data are **auto-generated on first run** — no setup needed!

---

## 📁 Project Structure

```
scorelytics-dashboard/
├── app.py                  # Main Streamlit application
├── analytics.py            # Grade logic, risk classification, PDF generation
├── database.py             # SQLite database setup and queries
├── generate_mock_data.py   # 500-student mock data generator
├── requirements.txt        # Python dependencies
└── .gitignore
```

---

## 📦 Dependencies

```
streamlit
pandas
numpy
scikit-learn
reportlab
matplotlib
seaborn
```

---

## 📄 License

MIT License — free to use and modify.
