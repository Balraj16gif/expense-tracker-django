# Expense Tracker

A Django-based expense tracker web application built during a Python Full Stack Developer internship.

## Features
- Register, login, logout
- Forgot password using a 6-digit security PIN (with lockout after 5 wrong attempts)
- Expense and income management (add, edit, delete)
- Search and filter expenses
- Dashboard with monthly summary and budget progress
- Charts (category-wise and month-wise)
- Monthly budget with warning
- Export to CSV and PDF
- Dark mode

## Technologies
HTML, CSS, Bootstrap 5, JavaScript, jQuery, Chart.js, Python, Django, SQLite, ReportLab

## How to Run
1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Create admin user: `python manage.py createsuperuser`
6. Start server: `python manage.py runserver`
7. Open http://127.0.0.1:8000