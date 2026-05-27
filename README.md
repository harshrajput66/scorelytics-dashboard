# Scorelytics — Student Performance Analytics Dashboard

A Streamlit dashboard I built to track student academic performance across Class 11 & 12 — covering four streams (Medical, Non-Medical, Commerce, and Arts) with risk classification, individual profiles, and PDF report card generation.

## Getting Started

```bash
git clone https://github.com/harshrajput66/scorelytics-dashboard.git
cd scorelytics-dashboard
pip install -r requirements.txt
streamlit run app.py
```

The database and mock data are auto-generated on first run — no extra setup needed.

## What's Inside

- **Overview** — school-wide stats, score distributions, and subject averages
- **Student Profiles** — filter by risk level, grade, or attendance and download PDF report cards
- **Database Explorer** — browse raw tables or run your own SQL queries

## Tech Stack

Python · Streamlit · SQLite · Pandas · ReportLab · Scikit-learn
