# Prana Space of Art

A dance & music academy management app for Classic Dance (3 batches), Western Dance, and Carnatic Music departments.

## Features
- Dashboard with collection stats, fee status, and department overview
- Student management (add / edit / delete)
- Fees: tap Fees → select department → select batch → select student → record monthly fee paid/unpaid
- Attendance: mark present/absent by batch and date
- PL Statements: monthly collection totals, paid/unpaid breakdown
- Settings: set batch timings (days, start/end time) and monthly fee per batch

## Setup

```bash
pip install -r requirements.txt --break-system-packages   # or use a virtualenv

# 1. Create the database with the 3 departments + batches (Classic Dance x3, Western Dance x1, Carnatic Music x1)
python3 seed.py

# 2. (Optional) Add sample students & fee records to try the app with data
python3 seed_demo_data.py

# 3. Run the app
python3 app.py
```

Then open http://localhost:5000

## Notes
- Database: SQLite file `prana.db`, created in the project folder. No server setup needed.
- Batch timings and monthly fee amounts are NOT hardcoded — set them from the **Settings** page after first run.
- To add more batches to any department, use the "+ Add batch" option on the Settings page.
- To start fresh, delete `prana.db` and re-run `python3 seed.py`.

## Project structure
```
app.py                 Flask routes
models.py               SQLAlchemy models (Department, Batch, Student, Fee, Attendance)
seed.py                  Creates departments + batches (run first, once)
seed_demo_data.py        Optional sample students/fees
templates/               Jinja HTML templates
static/css/style.css     Theme (matches Prana Space of Art design)
static/js/main.js        Sidebar toggle for mobile
```
