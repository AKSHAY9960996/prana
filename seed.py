"""Run once to set up the database with starter data:
   python3 seed.py
"""
from datetime import date, timedelta
from app import app
from models import db, Department, Batch, Student, Fee, Attendance, AttendanceEntry

with app.app_context():
    db.drop_all()
    db.create_all()

    classic = Department(name="Classic Dance", tagline="Bharatanatyam & Classical", icon="dance", color="pink")
    western = Department(name="Western Dance", tagline="Contemporary, Hip-hop, etc.", icon="western", color="purple")
    carnatic = Department(name="Carnatic Music", tagline="Vocal & Instrumental", icon="music", color="orange")
    db.session.add_all([classic, western, carnatic])
    db.session.flush()

    b1 = Batch(department_id=classic.id, name="Batch 1")
    b2 = Batch(department_id=classic.id, name="Batch 2")
    b3 = Batch(department_id=classic.id, name="Batch 3")
    wb1 = Batch(department_id=western.id, name="Batch 1")
    cb1 = Batch(department_id=carnatic.id, name="Batch 1")
    db.session.add_all([b1, b2, b3, wb1, cb1])
    db.session.commit()

    print("Seeded departments and batches:")
    for d in Department.query.all():
        print(f"  {d.name}: {[b.name for b in d.batches]}")

    print("\nDatabase ready at prana.db")
    print("Set batch timings and monthly fees from the Settings page.")
