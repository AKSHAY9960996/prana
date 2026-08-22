from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    tagline = db.Column(db.String(150), default="")
    icon = db.Column(db.String(20), default="dance")  # dance | western | music
    color = db.Column(db.String(20), default="pink")

    batches = db.relationship("Batch", backref="department", cascade="all, delete-orphan")
    students = db.relationship("Student", backref="department", cascade="all, delete-orphan")


class Batch(db.Model):
    __tablename__ = "batches"
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)  # e.g. "Batch 1"
    days = db.Column(db.String(120), default="")      # e.g. "Mon, Wed, Fri"
    start_time = db.Column(db.String(20), default="")  # e.g. "05:00 PM"
    end_time = db.Column(db.String(20), default="")    # e.g. "06:00 PM"
    monthly_fee = db.Column(db.Integer, default=0)

    students = db.relationship("Student", backref="batch", cascade="all, delete-orphan")

    @property
    def timing_label(self):
        if self.days or self.start_time:
            return f"{self.days} – {self.start_time} to {self.end_time}".strip(" –")
        return "Timing not set"


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, default="")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"), nullable=False)
    date_of_join = db.Column(db.Date, default=date.today)
    active = db.Column(db.Boolean, default=True)

    fees = db.relationship("Fee", backref="student", cascade="all, delete-orphan")
    attendance_entries = db.relationship("AttendanceEntry", backref="student", cascade="all, delete-orphan")

    @property
    def initials(self):
        parts = self.full_name.split()
        return "".join(p[0] for p in parts[:2]).upper() if parts else "ST"


class Fee(db.Model):
    __tablename__ = "fees"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # "2026-08"
    amount_due = db.Column(db.Integer, default=0)
    amount_paid = db.Column(db.Integer, default=0)
    status = db.Column(db.String(10), default="unpaid")  # paid | partial | unpaid
    paid_date = db.Column(db.Date, nullable=True)

    __table_args__ = (db.UniqueConstraint("student_id", "month", name="uix_student_month"),)

    @property
    def calculated_status(self):
        if self.amount_due > 0 and self.amount_paid >= self.amount_due:
            return "paid"
        elif self.amount_paid > 0:
            return "partial"
        return "unpaid"


class Attendance(db.Model):
    __tablename__ = "attendance_sessions"
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"), nullable=False)
    session_date = db.Column(db.Date, nullable=False, default=date.today)

    batch = db.relationship("Batch")
    entries = db.relationship("AttendanceEntry", backref="session", cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("batch_id", "session_date", name="uix_batch_date"),)


class AttendanceEntry(db.Model):
    __tablename__ = "attendance_entries"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("attendance_sessions.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    present = db.Column(db.Boolean, default=True)


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, default="Other")  # Salary, Rent, Electricity, Equipment, Maintenance, Utility, Other
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False, default=0)
    month = db.Column(db.String(7), nullable=False)  # "2026-08"
    expense_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text, default="")

