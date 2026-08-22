import os
from datetime import date, datetime
from calendar import month_name

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import func

from models import db, Department, Batch, Student, Fee, Attendance, AttendanceEntry

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# Render PostgreSQL or local SQLite support
db_url = os.environ.get("DATABASE_URL")
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    elif db_url.startswith("postgresql://") and "+pg8000" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'prana.db')}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY", "prana-space-of-art-key")

db.init_app(app)


def init_db():
    try:
        with app.app_context():
            db.create_all()
            # Seed starter departments if database is brand new
            if Department.query.count() == 0:
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
    except Exception as e:
        print("Database init info:", e)

_db_initialized = False
@app.before_request
def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True


# ---------- Lightweight Render Keep-Alive (NO Database Hit) ----------
@app.route("/ping")
def ping():
    return "pong", 200


# ---------- helpers ----------
def current_month_str():
    return date.today().strftime("%Y-%m")


def month_label(month_str):
    y, m = month_str.split("-")
    return f"{month_name[int(m)]} {y}"


@app.context_processor
def inject_globals():
    departments = Department.query.order_by(Department.id).all()
    hour = datetime.now().hour
    greeting = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
    return dict(nav_departments=departments, today=date.today(), greeting=greeting)


# ---------- dashboard ----------
@app.route("/")
def dashboard():
    total_students = Student.query.filter_by(active=True).count()
    this_month = current_month_str()

    fees_this_month = Fee.query.filter_by(month=this_month).all()
    total_collection = sum(f.amount_paid for f in fees_this_month)
    pending_fees = sum((f.amount_due - f.amount_paid) for f in fees_this_month if f.status != "paid")
    paid_count = sum(1 for f in fees_this_month if f.status == "paid")
    unpaid_count = sum(1 for f in fees_this_month if f.status != "paid")
    paid_amt = sum(f.amount_paid for f in fees_this_month if f.status == "paid")
    unpaid_amt = sum((f.amount_due - f.amount_paid) for f in fees_this_month if f.status != "paid")

    today_batches = Batch.query.count()  # simple stand-in for "today's classes"

    departments = Department.query.order_by(Department.id).all()

    # last 6 months collection trend
    trend = []
    for i in range(5, -1, -1):
        y = date.today().year
        m = date.today().month - i
        while m <= 0:
            m += 12
            y -= 1
        mstr = f"{y:04d}-{m:02d}"
        total = db.session.query(func.sum(Fee.amount_paid)).filter(Fee.month == mstr).scalar() or 0
        trend.append({"label": month_name[m][:3], "value": total})
    max_trend = max([t["value"] for t in trend] + [1])

    paid_pct = round((paid_amt / (paid_amt + unpaid_amt)) * 100) if (paid_amt + unpaid_amt) > 0 else 0

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_collection=total_collection,
        pending_fees=pending_fees,
        today_batches=today_batches,
        departments=departments,
        paid_count=paid_count,
        unpaid_count=unpaid_count,
        paid_amt=paid_amt,
        unpaid_amt=unpaid_amt,
        trend=trend,
        max_trend=max_trend,
        paid_pct=paid_pct,
        active_page="dashboard",
    )


# ---------- students ----------
@app.route("/students")
def students():
    q = request.args.get("q", "").strip()
    dept_id = request.args.get("department_id", type=int)
    query = Student.query.filter_by(active=True)
    if q:
        query = query.filter(
            (Student.full_name.ilike(f"%{q}%")) | (Student.mobile.ilike(f"%{q}%"))
        )
    if dept_id:
        query = query.filter_by(department_id=dept_id)
    all_students = query.order_by(Student.full_name).all()
    departments = Department.query.order_by(Department.id).all()

    # Calculate pending dues per student
    student_dues = {}
    for s in all_students:
        unpaid = Fee.query.filter_by(student_id=s.id).filter(Fee.status != "paid").all()
        if unpaid:
            total_pending = sum(f.amount_due - f.amount_paid for f in unpaid)
            months = [month_label(f.month) for f in unpaid]
            student_dues[s.id] = {"total": total_pending, "months": ", ".join(months)}

    return render_template(
        "students.html", students=all_students, departments=departments,
        student_dues=student_dues, q=q, dept_id=dept_id, active_page="students"
    )


@app.route("/students/new", methods=["GET", "POST"])
def student_new():
    departments = Department.query.order_by(Department.id).all()
    if request.method == "POST":
        student = Student(
            full_name=request.form["full_name"].strip(),
            mobile=request.form["mobile"].strip(),
            address=request.form.get("address", "").strip(),
            department_id=int(request.form["department_id"]),
            batch_id=int(request.form["batch_id"]),
            date_of_join=datetime.strptime(request.form["date_of_join"], "%Y-%m-%d").date()
            if request.form.get("date_of_join") else date.today(),
        )
        db.session.add(student)
        db.session.commit()
        flash("Student added successfully.", "success")
        return redirect(url_for("student_detail", student_id=student.id))
    return render_template(
        "student_form.html", student=None, departments=departments, active_page="students"
    )


@app.route("/students/<int:student_id>")
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    year = request.args.get("year", type=int) or date.today().year
    
    # Standard monthly fee from batch
    batch_fee = student.batch.monthly_fee if student.batch else 0
    
    # Load 12 months for selected year
    months_data = []
    for m in range(1, 13):
        mstr = f"{year:04d}-{m:02d}"
        fee_rec = Fee.query.filter_by(student_id=student.id, month=mstr).first()
        due = fee_rec.amount_due if fee_rec else batch_fee
        paid = fee_rec.amount_paid if fee_rec else 0
        
        if paid >= due and due > 0:
            status = "paid"
        elif paid > 0:
            status = "partial"
        else:
            status = "unpaid"
            
        months_data.append({
            "month": mstr,
            "month_num": m,
            "month_name": month_name[m],
            "due": due,
            "paid": paid,
            "pending": max(0, due - paid),
            "status": status,
            "fee_id": fee_rec.id if fee_rec else None
        })
        
    return render_template(
        "student_detail.html",
        student=student,
        year=year,
        months_data=months_data,
        active_page="students"
    )


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def student_edit(student_id):
    student = Student.query.get_or_404(student_id)
    departments = Department.query.order_by(Department.id).all()
    if request.method == "POST":
        student.full_name = request.form["full_name"].strip()
        student.mobile = request.form["mobile"].strip()
        student.address = request.form.get("address", "").strip()
        student.department_id = int(request.form["department_id"])
        student.batch_id = int(request.form["batch_id"])
        if request.form.get("date_of_join"):
            student.date_of_join = datetime.strptime(request.form["date_of_join"], "%Y-%m-%d").date()
        db.session.commit()
        flash("Student updated.", "success")
        return redirect(url_for("student_detail", student_id=student.id))
    return render_template(
        "student_form.html", student=student, departments=departments, active_page="students"
    )


@app.route("/students/<int:student_id>/delete", methods=["POST"])
def student_delete(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student removed.", "success")
    return redirect(url_for("students"))


@app.route("/api/search/students")
def api_search_students():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    students_ = Student.query.filter_by(active=True).filter(
        (Student.full_name.ilike(f"%{q}%")) | 
        (Student.mobile.ilike(f"%{q}%")) |
        (Student.address.ilike(f"%{q}%"))
    ).limit(10).all()
    return jsonify([
        {
            "id": s.id,
            "name": s.full_name,
            "mobile": s.mobile,
            "address": s.address,
            "dept": s.department.name,
            "batch": s.batch.name
        }
        for s in students_
    ])


# ---------- departments ----------
@app.route("/departments")
def departments_page():
    departments = Department.query.order_by(Department.id).all()
    return render_template("departments.html", departments=departments, active_page="departments")


# ---------- batches / settings ----------
@app.route("/batches")
def batches_page():
    return redirect(url_for("settings"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    departments = Department.query.order_by(Department.id).all()
    if request.method == "POST":
        # bulk-update batch timings & fees
        for batch in Batch.query.all():
            prefix = f"batch_{batch.id}_"
            if f"{prefix}days" in request.form:
                batch.days = request.form.get(f"{prefix}days", "").strip()
                batch.start_time = request.form.get(f"{prefix}start", "").strip()
                batch.end_time = request.form.get(f"{prefix}end", "").strip()
                fee = request.form.get(f"{prefix}fee", "0").strip()
                batch.monthly_fee = int(fee) if fee.isdigit() else 0
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", departments=departments, active_page="settings")


@app.route("/batches/new", methods=["POST"])
def batch_new():
    department_id = int(request.form["department_id"])
    batch = Batch(department_id=department_id, name=request.form["name"].strip())
    db.session.add(batch)
    db.session.commit()
    flash("Batch added.", "success")
    return redirect(url_for("settings"))


@app.route("/batches/<int:batch_id>/delete", methods=["POST"])
def batch_delete(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    db.session.delete(batch)
    db.session.commit()
    flash("Batch removed.", "success")
    return redirect(url_for("settings"))


@app.route("/api/batches/<int:department_id>")
def api_batches(department_id):
    batches = Batch.query.filter_by(department_id=department_id).all()
    return jsonify([
        {"id": b.id, "name": b.name, "timing": b.timing_label, "fee": b.monthly_fee}
        for b in batches
    ])


@app.route("/api/students/<int:batch_id>")
def api_students(batch_id):
    students_ = Student.query.filter_by(batch_id=batch_id, active=True).order_by(Student.full_name).all()
    result = []
    for s in students_:
        unpaid = Fee.query.filter_by(student_id=s.id).filter(Fee.status != "paid").all()
        total_pending = sum(f.amount_due - f.amount_paid for f in unpaid)
        unpaid_months = [{"month": f.month, "label": month_label(f.month), "due": f.amount_due - f.amount_paid, "amount_due": f.amount_due, "amount_paid": f.amount_paid} for f in unpaid]
        result.append({
            "id": s.id,
            "name": s.full_name,
            "mobile": s.mobile,
            "total_pending": total_pending,
            "unpaid_months": unpaid_months
        })
    return jsonify(result)


@app.route("/api/student/<int:student_id>/unpaid")
def api_student_unpaid(student_id):
    unpaid = Fee.query.filter_by(student_id=student_id).filter(Fee.status != "paid").order_by(Fee.month.asc()).all()
    return jsonify([
        {
            "id": f.id,
            "month": f.month,
            "month_label": month_label(f.month),
            "amount_due": f.amount_due,
            "amount_paid": f.amount_paid,
            "pending": f.amount_due - f.amount_paid
        }
        for f in unpaid
    ])


# ---------- fees ----------
@app.route("/fees")
def fees_page():
    departments = Department.query.order_by(Department.id).all()
    this_month = current_month_str()

    records = (
        db.session.query(Fee, Student, Batch)
        .join(Student, Fee.student_id == Student.id)
        .join(Batch, Student.batch_id == Batch.id)
        .order_by(Fee.month.desc(), Student.full_name)
        .limit(100)
        .all()
    )
    
    # Dues query across all months
    dues = (
        db.session.query(Fee, Student, Batch)
        .join(Student, Fee.student_id == Student.id)
        .join(Batch, Student.batch_id == Batch.id)
        .filter(Fee.status != "paid")
        .order_by(Fee.month.asc(), Student.full_name)
        .all()
    )

    return render_template(
        "fees.html",
        departments=departments,
        records=records,
        dues=dues,
        this_month=this_month,
        month_label=month_label(this_month),
        active_page="fees",
    )


@app.route("/fees/add", methods=["POST"])
def fee_add():
    student_id = int(request.form["student_id"])
    month = request.form.get("month") or current_month_str()
    amount_due = int(request.form.get("amount_due") or 0)
    amount_paid = int(request.form.get("amount_paid") or 0)
    
    if amount_due > 0 and amount_paid >= amount_due:
        status = "paid"
    elif amount_paid > 0:
        status = "partial"
    else:
        status = request.form.get("status", "unpaid")

    fee = Fee.query.filter_by(student_id=student_id, month=month).first()
    if not fee:
        fee = Fee(student_id=student_id, month=month)
        db.session.add(fee)
    fee.amount_due = amount_due
    fee.amount_paid = amount_paid
    fee.status = status
    fee.paid_date = date.today() if status == "paid" else None
    db.session.commit()
    flash("Fee record saved successfully.", "success")
    
    next_url = request.form.get("next_url")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("fees_page"))


# ---------- attendance ----------
@app.route("/attendance", methods=["GET"])
def attendance_page():
    departments = Department.query.order_by(Department.id).all()
    batch_id = request.args.get("batch_id", type=int)
    day_str = request.args.get("date") or date.today().isoformat()
    session_date = datetime.strptime(day_str, "%Y-%m-%d").date()

    all_batches = Batch.query.all()
    if not batch_id and all_batches:
        batch_id = all_batches[0].id

    students_in_batch = []
    existing = {}
    if batch_id:
        students_in_batch = Student.query.filter_by(batch_id=batch_id, active=True).order_by(Student.full_name).all()
        session = Attendance.query.filter_by(batch_id=batch_id, session_date=session_date).first()
        if session:
            existing = {e.student_id: e.present for e in session.entries}

    return render_template(
        "attendance.html",
        departments=departments,
        batches=all_batches,
        batch_id=batch_id,
        session_date=session_date,
        students=students_in_batch,
        existing=existing,
        active_page="attendance",
    )


@app.route("/attendance/save", methods=["POST"])
def attendance_save():
    batch_id = int(request.form["batch_id"])
    day_str = request.form["date"]
    session_date = datetime.strptime(day_str, "%Y-%m-%d").date()

    session = Attendance.query.filter_by(batch_id=batch_id, session_date=session_date).first()
    if not session:
        session = Attendance(batch_id=batch_id, session_date=session_date)
        db.session.add(session)
        db.session.flush()

    students_in_batch = Student.query.filter_by(batch_id=batch_id, active=True).all()
    existing = {e.student_id: e for e in session.entries}
    for s in students_in_batch:
        present = request.form.get(f"present_{s.id}") == "on"
        if s.id in existing:
            existing[s.id].present = present
        else:
            db.session.add(AttendanceEntry(session_id=session.id, student_id=s.id, present=present))
    db.session.commit()
    flash("Attendance saved.", "success")
    return redirect(url_for("attendance_page", batch_id=batch_id, date=day_str))


# ---------- P&L statements ----------
@app.route("/pl-statements")
def pl_statements():
    departments = Department.query.order_by(Department.id).all()
    month = request.args.get("month") or current_month_str()
    batch_id = request.args.get("batch_id", type=int)

    query = (
        db.session.query(Fee, Student, Batch)
        .join(Student, Fee.student_id == Student.id)
        .join(Batch, Student.batch_id == Batch.id)
        .filter(Fee.month == month)
    )
    if batch_id:
        query = query.filter(Batch.id == batch_id)
    rows = query.order_by(Student.full_name).all()

    total_collection = sum(r[0].amount_paid for r in rows)
    total_fees = sum(r[0].amount_due for r in rows)
    total_paid = sum(r[0].amount_paid for r in rows if r[0].status == "paid")
    total_unpaid = sum((r[0].amount_due - r[0].amount_paid) for r in rows if r[0].status != "paid")

    all_batches = Batch.query.all()

    return render_template(
        "pl_statements.html",
        departments=departments,
        rows=rows,
        month=month,
        month_label=month_label(month),
        batches=all_batches,
        batch_id=batch_id,
        total_collection=total_collection,
        total_fees=total_fees,
        total_paid=total_paid,
        total_unpaid=total_unpaid,
        active_page="pl_statements",
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
