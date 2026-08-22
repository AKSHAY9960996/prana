"""Optional: adds sample batches/students/fees so the app isn't empty on first run.
   Run AFTER seed.py:  python3 seed_demo_data.py
"""
from datetime import date
from app import app
from models import db, Department, Batch, Student, Fee, Expense, Attendance, AttendanceEntry

with app.app_context():
    # Clear existing data for clean re-seed
    Expense.query.delete()
    Fee.query.delete()
    AttendanceEntry.query.delete()
    Attendance.query.delete()
    Student.query.delete()

    classic = Department.query.filter_by(name="Classic Dance").first()
    western = Department.query.filter_by(name="Western Dance").first()
    carnatic = Department.query.filter_by(name="Carnatic Music").first()

    b1 = Batch.query.filter_by(department_id=classic.id, name="Batch 1").first()
    b1.days, b1.start_time, b1.end_time, b1.monthly_fee = "Mon, Wed, Fri", "5:00 PM", "6:00 PM", 1200
    b2 = Batch.query.filter_by(department_id=classic.id, name="Batch 2").first()
    b2.days, b2.start_time, b2.end_time, b2.monthly_fee = "Tue, Thu, Sat", "6:00 PM", "7:00 PM", 1200
    b3 = Batch.query.filter_by(department_id=classic.id, name="Batch 3").first()
    b3.days, b3.start_time, b3.end_time, b3.monthly_fee = "Sat, Sun", "10:00 AM", "11:30 AM", 1500
    wb1 = Batch.query.filter_by(department_id=western.id, name="Batch 1").first()
    wb1.days, wb1.start_time, wb1.end_time, wb1.monthly_fee = "Mon, Wed, Fri", "4:00 PM", "5:00 PM", 1000
    cb1 = Batch.query.filter_by(department_id=carnatic.id, name="Batch 1").first()
    cb1.days, cb1.start_time, cb1.end_time, cb1.monthly_fee = "Tue, Thu, Sat", "5:00 PM", "6:00 PM", 1000
    db.session.commit()

    students = [
        Student(full_name="Aaradhya S", mobile="9876543210", address="12, MG Road, Bengaluru", department_id=classic.id, batch_id=b1.id),
        Student(full_name="Saanvi K", mobile="9812345670", address="45, Indiranagar, Bengaluru", department_id=classic.id, batch_id=b1.id),
        Student(full_name="Diya Iyer", mobile="9845123670", address="88, Jayanagar 4th Block, Bengaluru", department_id=classic.id, batch_id=b1.id),
        Student(full_name="Meera E", mobile="9800012345", address="5, Koramangala, Bengaluru", department_id=classic.id, batch_id=b1.id),
        Student(full_name="Nandana R", mobile="9123456789", address="102, Malleshwaram, Bengaluru", department_id=classic.id, batch_id=b2.id),
        Student(full_name="Vihaan S", mobile="9988776655", address="77, HSR Layout, Bengaluru", department_id=western.id, batch_id=wb1.id),
        Student(full_name="Meera Iyer", mobile="9000012345", address="23, Whitefield, Bengaluru", department_id=carnatic.id, batch_id=cb1.id),
    ]
    db.session.add_all(students)
    db.session.commit()

    this_month = date.today().strftime("%Y-%m")
    fees = [
        Fee(student_id=students[0].id, month=this_month, amount_due=1200, amount_paid=1200, status="paid", paid_date=date.today()),
        Fee(student_id=students[1].id, month=this_month, amount_due=1200, amount_paid=1200, status="paid", paid_date=date.today()),
        Fee(student_id=students[2].id, month=this_month, amount_due=1200, amount_paid=0, status="unpaid"),
        Fee(student_id=students[3].id, month=this_month, amount_due=1200, amount_paid=900, status="partial"),  # Fee 1200, paid 900 -> Partial
        Fee(student_id=students[4].id, month=this_month, amount_due=1200, amount_paid=600, status="partial"),  # Fee 1200, paid 600 -> Partial
        Fee(student_id=students[5].id, month=this_month, amount_due=1000, amount_paid=1000, status="paid", paid_date=date.today()),
    ]
    db.session.add_all(fees)

    sample_expenses = [
        Expense(title="Studio Rent - August", category="Rent", amount=12000, month=this_month, expense_date=date.today(), notes="Monthly space lease"),
        Expense(title="Classical Dance Instructor Salary", category="Salary", amount=8000, month=this_month, expense_date=date.today(), notes="Faculty payment"),
        Expense(title="Western Dance Instructor Salary", category="Salary", amount=6000, month=this_month, expense_date=date.today(), notes="Faculty payment"),
        Expense(title="BESCOM Electricity Bill", category="Electricity", amount=1500, month=this_month, expense_date=date.today(), notes="Studio lighting & AC"),
        Expense(title="Sound System Maintenance", category="Maintenance", amount=800, month=this_month, expense_date=date.today(), notes="Speaker cable replacement")
    ]
    db.session.add_all(sample_expenses)
    db.session.commit()
    print(f"Demo data seeded: {len(students)} students, {len(fees)} fee records, {len(sample_expenses)} expenses")
