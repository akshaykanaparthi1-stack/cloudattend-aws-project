import os
import csv
import io
import re
import secrets
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, abort, Response, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import config_by_name
import database


def create_app(config_name=None):
    """Application factory for CloudAttend."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_obj)

    # Initialize database hooks and CLI commands
    database.init_app(app)

    # Auto-initialize database and demo seed if database file doesn't exist yet
    with app.app_context():
        db_path = app.config.get("DATABASE_PATH")
        if db_path != ":memory:" and not os.path.exists(db_path):
            database.init_db()
            database.seed_db()

    # -------------------------------------------------------------
    # Security Helpers & Middleware
    # -------------------------------------------------------------
    @app.before_request
    def ensure_csrf_token():
        """Ensure session has a CSRF token."""
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)

    @app.before_request
    def verify_csrf():
        """Verify CSRF token for state-changing HTTP methods."""
        # Exempt GET, HEAD, OPTIONS
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return
        # Exempt during unit testing if configured
        if app.config.get("TESTING") and not app.config.get("WTF_CSRF_ENABLED", False):
            return

        token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        if not token or token != session.get("csrf_token"):
            app.logger.warning("CSRF token verification failed for endpoint: %s", request.endpoint)
            abort(403, description="CSRF security validation failed. Please refresh and try again.")

    @app.after_request
    def set_security_headers(response):
        """Add standard security headers to all responses."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.context_processor
    def inject_helpers():
        """Inject useful helper variables and functions into templates."""
        user = session.get("user")
        if user and isinstance(user, dict) and "id" in user:
            try:
                db = database.get_db()
                db_user = db.execute(
                    "SELECT id, username, full_name, role, email FROM users WHERE id = ?",
                    (user["id"],)
                ).fetchone()
                if db_user:
                    user = {
                        "id": db_user["id"],
                        "username": db_user["username"],
                        "full_name": db_user["full_name"],
                        "role": db_user["role"],
                        "email": db_user["email"],
                    }
                    session["user"] = user
            except Exception:
                pass

        return {
            "csrf_token": lambda: session.get("csrf_token", ""),
            "current_user": user,
            "today_date": date.today().isoformat(),
            "app_name": "CloudAttend",
        }

    # -------------------------------------------------------------
    # Authentication Decorator
    # -------------------------------------------------------------
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login", next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    # -------------------------------------------------------------
    # Input Validation Helpers
    # -------------------------------------------------------------
    def validate_student_data(student_id, name, class_name, section, email=""):
        errors = []
        student_id = (student_id or "").strip()
        name = (name or "").strip()
        class_name = (class_name or "").strip()
        section = (section or "").strip()
        email = (email or "").strip()

        if not student_id:
            errors.append("Student ID is required.")
        elif not re.match(r"^[A-Za-z0-9\-_]{2,30}$", student_id):
            errors.append("Student ID must be 2-30 alphanumeric characters (hyphens and underscores allowed).")

        if not name or len(name) < 2 or len(name) > 100:
            errors.append("Student name must be between 2 and 100 characters.")

        if not class_name:
            errors.append("Class name is required.")

        if not section:
            errors.append("Section is required.")

        if email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            errors.append("Invalid email address format.")

        return errors, {
            "student_id": student_id,
            "name": name,
            "class_name": class_name,
            "section": section,
            "email": email,
        }

    def validate_iso_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    # -------------------------------------------------------------
    # Authentication Routes
    # -------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "user" in session:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                flash("Username and password are required.", "danger")
                return render_template("login.html")

            db = database.get_db()
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session.permanent = True
                session["user"] = {
                    "id": user["id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                    "email": user["email"],
                }
                session["csrf_token"] = secrets.token_hex(32)
                flash(f"Welcome back, {user['full_name']}!", "success")
                next_url = request.args.get("next")
                # Basic protection against open redirect
                if next_url and next_url.startswith("/"):
                    return redirect(next_url)
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password.", "danger")

        return render_template("login.html")

    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        session.clear()
        flash("You have been securely logged out.", "info")
        return redirect(url_for("login"))

    # -------------------------------------------------------------
    # Dashboard Route
    # -------------------------------------------------------------
    @app.route("/")
    @app.route("/dashboard")
    @login_required
    def dashboard():
        db = database.get_db()
        today_str = date.today().isoformat()

        # 1. Total Students
        total_students = db.execute(
            "SELECT COUNT(*) AS count FROM students WHERE status = 'Active'"
        ).fetchone()["count"]

        # 2. Total Classes
        classes_count = db.execute(
            "SELECT COUNT(DISTINCT class_name) AS count FROM students WHERE status = 'Active'"
        ).fetchone()["count"]

        # 3. Today's Attendance breakdown
        today_stats = db.execute(
            """
            SELECT 
                COUNT(*) as total_marked,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_count
            FROM attendance
            WHERE attendance_date = ?
            """,
            (today_str,)
        ).fetchone()

        today_present = today_stats["present_count"] or 0
        today_absent = today_stats["absent_count"] or 0
        today_late = today_stats["late_count"] or 0
        today_marked = today_stats["total_marked"] or 0

        # Calculate today percentage
        today_percentage = (
            round((today_present / today_marked) * 100, 1) if today_marked > 0 else 0.0
        )

        # 4. Overall Attendance Rate (all historical records)
        overall_stats = db.execute(
            """
            SELECT 
                COUNT(*) as total_all,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_all
            FROM attendance
            """
        ).fetchone()
        total_all = overall_stats["total_all"] or 0
        present_all = overall_stats["present_all"] or 0
        overall_percentage = (
            round((present_all / total_all) * 100, 1) if total_all > 0 else 0.0
        )

        # 5. Attendance Trend for the last 7 distinct recorded dates
        trend_rows = db.execute(
            """
            SELECT 
                attendance_date,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late
            FROM attendance
            GROUP BY attendance_date
            ORDER BY attendance_date DESC
            LIMIT 7
            """
        ).fetchall()
        # Reverse to chronological order (oldest to newest)
        trend_data = list(reversed([dict(row) for row in trend_rows]))

        # 6. Class-wise breakdown for Today (or Overall if no records today)
        class_stats_rows = db.execute(
            """
            SELECT 
                s.class_name,
                COUNT(DISTINCT s.id) as total_students,
                SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_today,
                SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_today,
                SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_today
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.attendance_date = ?
            WHERE s.status = 'Active'
            GROUP BY s.class_name
            ORDER BY s.class_name ASC
            """,
            (today_str,)
        ).fetchall()

        class_summary = []
        for r in class_stats_rows:
            marked = r["present_today"] + r["absent_today"] + r["late_today"]
            pct = round((r["present_today"] / marked) * 100, 1) if marked > 0 else 0.0
            class_summary.append({
                "class_name": r["class_name"],
                "total_students": r["total_students"],
                "present": r["present_today"],
                "absent": r["absent_today"],
                "late": r["late_today"],
                "marked": marked,
                "percentage": pct,
            })

        # 7. Recent Activity (latest 5 attendance records)
        recent_activity = db.execute(
            """
            SELECT a.id, a.attendance_date, a.status, a.notes, a.created_at,
                   s.student_id, s.name as student_name, s.class_name, s.section
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            ORDER BY a.created_at DESC, a.id DESC
            LIMIT 5
            """
        ).fetchall()

        return render_template(
            "dashboard.html",
            total_students=total_students,
            classes_count=classes_count,
            today_present=today_present,
            today_absent=today_absent,
            today_late=today_late,
            today_marked=today_marked,
            today_percentage=today_percentage,
            overall_percentage=overall_percentage,
            trend_data=trend_data,
            class_summary=class_summary,
            recent_activity=recent_activity,
            today_str=today_str,
        )

    # -------------------------------------------------------------
    # Student Management Routes
    # -------------------------------------------------------------
    @app.route("/students")
    @login_required
    def list_students():
        db = database.get_db()
        search_query = request.args.get("q", "").strip()
        selected_class = request.args.get("class_name", "").strip()
        selected_section = request.args.get("section", "").strip()

        # Build dynamic query with parameterization
        sql = "SELECT * FROM students WHERE 1=1"
        params = []

        if search_query:
            sql += " AND (student_id LIKE ? OR name LIKE ? OR email LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])

        if selected_class:
            sql += " AND class_name = ?"
            params.append(selected_class)

        if selected_section:
            sql += " AND section = ?"
            params.append(selected_section)

        sql += " ORDER BY class_name, section, name ASC"
        students = db.execute(sql, params).fetchall()

        # Distinct classes and sections for filters
        classes = [r["class_name"] for r in db.execute(
            "SELECT DISTINCT class_name FROM students ORDER BY class_name"
        ).fetchall()]
        sections = [r["section"] for r in db.execute(
            "SELECT DISTINCT section FROM students ORDER BY section"
        ).fetchall()]

        return render_template(
            "students/index.html",
            students=students,
            classes=classes,
            sections=sections,
            search_query=search_query,
            selected_class=selected_class,
            selected_section=selected_section,
            total_count=len(students)
        )

    @app.route("/students/add", methods=["GET", "POST"])
    @login_required
    def add_student():
        db = database.get_db()
        if request.method == "POST":
            student_id = request.form.get("student_id")
            name = request.form.get("name")
            class_name = request.form.get("class_name")
            section = request.form.get("section")
            email = request.form.get("email")

            errors, sanitized = validate_student_data(student_id, name, class_name, section, email)

            # Check for duplicate student_id
            if not errors:
                existing = db.execute(
                    "SELECT id FROM students WHERE student_id = ?",
                    (sanitized["student_id"],)
                ).fetchone()
                if existing:
                    errors.append(f"Student ID '{sanitized['student_id']}' is already in use.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "students/add.html",
                    form_data=request.form,
                    classes=_get_existing_classes(db)
                )

            # Insert student
            db.execute(
                """
                INSERT INTO students (student_id, name, class_name, section, email, status)
                VALUES (?, ?, ?, ?, ?, 'Active')
                """,
                (
                    sanitized["student_id"],
                    sanitized["name"],
                    sanitized["class_name"],
                    sanitized["section"],
                    sanitized["email"] or None
                )
            )
            db.commit()
            flash(f"Student '{sanitized['name']}' ({sanitized['student_id']}) added successfully!", "success")
            return redirect(url_for("list_students"))

        return render_template(
            "students/add.html",
            form_data={},
            classes=_get_existing_classes(db)
        )

    @app.route("/students/<int:id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_student(id):
        db = database.get_db()
        student = db.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()
        if not student:
            abort(404, description="Student not found.")

        if request.method == "POST":
            student_id = request.form.get("student_id")
            name = request.form.get("name")
            class_name = request.form.get("class_name")
            section = request.form.get("section")
            email = request.form.get("email")
            status = request.form.get("status", "Active")

            errors, sanitized = validate_student_data(student_id, name, class_name, section, email)
            if status not in ("Active", "Inactive"):
                errors.append("Invalid status selected.")

            # Check duplicate student_id on other students
            if not errors:
                existing = db.execute(
                    "SELECT id FROM students WHERE student_id = ? AND id != ?",
                    (sanitized["student_id"], id)
                ).fetchone()
                if existing:
                    errors.append(f"Student ID '{sanitized['student_id']}' is already in use by another student.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "students/edit.html",
                    student=student,
                    classes=_get_existing_classes(db)
                )

            db.execute(
                """
                UPDATE students
                SET student_id = ?, name = ?, class_name = ?, section = ?, email = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    sanitized["student_id"],
                    sanitized["name"],
                    sanitized["class_name"],
                    sanitized["section"],
                    sanitized["email"] or None,
                    status,
                    id
                )
            )
            db.commit()
            flash(f"Student '{sanitized['name']}' updated successfully!", "success")
            return redirect(url_for("list_students"))

        return render_template(
            "students/edit.html",
            student=student,
            classes=_get_existing_classes(db)
        )

    @app.route("/students/<int:id>/delete", methods=["POST"])
    @login_required
    def delete_student(id):
        db = database.get_db()
        student = db.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()
        if not student:
            abort(404, description="Student not found.")

        db.execute("DELETE FROM students WHERE id = ?", (id,))
        db.commit()
        flash(f"Student '{student['name']}' and their attendance history have been deleted.", "info")
        return redirect(url_for("list_students"))

    @app.route("/students/<int:id>")
    @login_required
    def view_student(id):
        db = database.get_db()
        student = db.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()
        if not student:
            abort(404, description="Student not found.")

        # Attendance stats for this student
        stats = db.execute(
            """
            SELECT 
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_count
            FROM attendance
            WHERE student_id = ?
            """,
            (id,)
        ).fetchone()

        total_days = stats["total_days"] or 0
        present = stats["present_count"] or 0
        absent = stats["absent_count"] or 0
        late = stats["late_count"] or 0
        pct = round((present / total_days) * 100, 1) if total_days > 0 else 0.0

        history = db.execute(
            """
            SELECT attendance_date, status, notes, created_at
            FROM attendance
            WHERE student_id = ?
            ORDER BY attendance_date DESC
            """,
            (id,)
        ).fetchall()

        return render_template(
            "students/view.html",
            student=student,
            total_days=total_days,
            present=present,
            absent=absent,
            late=late,
            percentage=pct,
            history=history
        )

    # -------------------------------------------------------------
    # Attendance Marking Routes
    # -------------------------------------------------------------
    @app.route("/attendance/mark", methods=["GET", "POST"])
    @login_required
    def mark_attendance():
        db = database.get_db()
        today_iso = date.today().isoformat()

        if request.method == "POST":
            selected_date = request.form.get("attendance_date", "").strip()
            selected_class = request.form.get("class_name", "").strip()
            selected_section = request.form.get("section", "").strip()

            parsed_date = validate_iso_date(selected_date)
            if not parsed_date:
                flash("Please provide a valid attendance date (YYYY-MM-DD).", "danger")
                return redirect(url_for("mark_attendance", class_name=selected_class, section=selected_section))

            if not selected_class:
                flash("Please select a class before saving attendance.", "danger")
                return redirect(url_for("mark_attendance"))

            # Fetch active students for this class & section
            q = "SELECT id, name, student_id FROM students WHERE class_name = ? AND status = 'Active'"
            params = [selected_class]
            if selected_section:
                q += " AND section = ?"
                params.append(selected_section)
            students = db.execute(q, params).fetchall()

            if not students:
                flash("No active students found in the selected class/section.", "warning")
                return redirect(url_for("mark_attendance", attendance_date=selected_date, class_name=selected_class))

            admin_id = session.get("user", {}).get("id")
            saved_count = 0
            updated_count = 0

            # Process attendance records within a transaction
            try:
                for s in students:
                    status_val = request.form.get(f"status_{s['id']}")
                    notes_val = (request.form.get(f"notes_{s['id']}") or "").strip()

                    # Only process if status is chosen
                    if status_val in ("Present", "Absent", "Late"):
                        # Check if record already exists for duplicate prevention
                        existing = db.execute(
                            "SELECT id FROM attendance WHERE student_id = ? AND attendance_date = ?",
                            (s["id"], selected_date)
                        ).fetchone()

                        if existing:
                            # Update existing row safely
                            db.execute(
                                """
                                UPDATE attendance
                                SET status = ?, notes = ?, recorded_by = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                                """,
                                (status_val, notes_val, admin_id, existing["id"])
                            )
                            updated_count += 1
                        else:
                            # Insert new row
                            db.execute(
                                """
                                INSERT INTO attendance (student_id, attendance_date, status, notes, recorded_by)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (s["id"], selected_date, status_val, notes_val, admin_id)
                            )
                            saved_count += 1

                db.commit()
                flash(
                    f"Attendance saved for {selected_class} on {selected_date}: {saved_count} new entries, {updated_count} updated entries.",
                    "success"
                )
            except Exception as e:
                db.rollback()
                app.logger.error("Error saving attendance: %s", str(e))
                flash(f"Error saving attendance: {str(e)}", "danger")

            return redirect(url_for(
                "mark_attendance",
                attendance_date=selected_date,
                class_name=selected_class,
                section=selected_section
            ))

        # GET request handling
        selected_date = request.args.get("attendance_date", today_iso)
        selected_class = request.args.get("class_name", "")
        selected_section = request.args.get("section", "")

        classes = _get_existing_classes(db)
        sections = [r["section"] for r in db.execute(
            "SELECT DISTINCT section FROM students ORDER BY section"
        ).fetchall()]

        students_list = []
        existing_records_map = {}

        if selected_class:
            q = "SELECT id, student_id, name, class_name, section FROM students WHERE class_name = ? AND status = 'Active'"
            params = [selected_class]
            if selected_section:
                q += " AND section = ?"
                params.append(selected_section)
            q += " ORDER BY name ASC"
            students_list = db.execute(q, params).fetchall()

            # Fetch existing records for this date
            if students_list:
                s_ids = [s["id"] for s in students_list]
                placeholders = ",".join("?" for _ in s_ids)
                records = db.execute(
                    f"""
                    SELECT student_id, status, notes
                    FROM attendance
                    WHERE attendance_date = ? AND student_id IN ({placeholders})
                    """,
                    [selected_date] + s_ids
                ).fetchall()
                for r in records:
                    existing_records_map[r["student_id"]] = {
                        "status": r["status"],
                        "notes": r["notes"] or "",
                    }

        return render_template(
            "attendance/mark.html",
            classes=classes,
            sections=sections,
            selected_date=selected_date,
            selected_class=selected_class,
            selected_section=selected_section,
            students=students_list,
            existing_records=existing_records_map,
            today_iso=today_iso,
        )

    # -------------------------------------------------------------
    # Reports & Analytics Routes
    # -------------------------------------------------------------
    @app.route("/attendance/reports")
    @login_required
    def reports():
        db = database.get_db()

        # Query Filters
        filter_type = request.args.get("type", "daily") # daily, monthly, all
        selected_date = request.args.get("date", date.today().isoformat())
        selected_month = request.args.get("month", date.today().strftime("%Y-%m"))
        selected_class = request.args.get("class_name", "")
        selected_section = request.args.get("section", "")
        selected_status = request.args.get("status", "")
        search_student = request.args.get("student_query", "").strip()

        # Build dynamic SQL
        sql = """
            SELECT 
                a.id, a.attendance_date, a.status, a.notes, a.created_at,
                s.id as student_db_id, s.student_id, s.name as student_name, s.class_name, s.section
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE 1=1
        """
        params = []

        if filter_type == "daily" and selected_date:
            sql += " AND a.attendance_date = ?"
            params.append(selected_date)
        elif filter_type == "monthly" and selected_month:
            sql += " AND a.attendance_date LIKE ?"
            params.append(f"{selected_month}%")

        if selected_class:
            sql += " AND s.class_name = ?"
            params.append(selected_class)

        if selected_section:
            sql += " AND s.section = ?"
            params.append(selected_section)

        if selected_status:
            sql += " AND a.status = ?"
            params.append(selected_status)

        if search_student:
            sql += " AND (s.name LIKE ? OR s.student_id LIKE ?)"
            term = f"%{search_student}%"
            params.extend([term, term])

        sql += " ORDER BY a.attendance_date DESC, s.class_name, s.name ASC"
        records = db.execute(sql, params).fetchall()

        # Accurate calculations (handling zero records safely)
        total_records = len(records)
        present_count = sum(1 for r in records if r["status"] == "Present")
        absent_count = sum(1 for r in records if r["status"] == "Absent")
        late_count = sum(1 for r in records if r["status"] == "Late")

        if total_records > 0:
            attendance_percentage = round((present_count / total_records) * 100, 1)
        else:
            attendance_percentage = 0.0

        # Class options and Section options for filter dropdowns
        classes = _get_existing_classes(db)
        sections = [r["section"] for r in db.execute(
            "SELECT DISTINCT section FROM students ORDER BY section"
        ).fetchall()]

        return render_template(
            "attendance/history.html",
            records=records,
            total_records=total_records,
            present_count=present_count,
            absent_count=absent_count,
            late_count=late_count,
            attendance_percentage=attendance_percentage,
            classes=classes,
            sections=sections,
            filter_type=filter_type,
            selected_date=selected_date,
            selected_month=selected_month,
            selected_class=selected_class,
            selected_section=selected_section,
            selected_status=selected_status,
            search_student=search_student,
        )

    @app.route("/attendance/export-csv")
    @login_required
    def export_csv():
        db = database.get_db()

        # Same filters as reports
        filter_type = request.args.get("type", "daily")
        selected_date = request.args.get("date", date.today().isoformat())
        selected_month = request.args.get("month", date.today().strftime("%Y-%m"))
        selected_class = request.args.get("class_name", "")
        selected_section = request.args.get("section", "")
        selected_status = request.args.get("status", "")
        search_student = request.args.get("student_query", "").strip()

        sql = """
            SELECT 
                s.student_id,
                s.name as student_name,
                s.class_name,
                s.section,
                a.attendance_date,
                a.status,
                COALESCE(a.notes, '') as notes,
                a.created_at
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE 1=1
        """
        params = []

        if filter_type == "daily" and selected_date:
            sql += " AND a.attendance_date = ?"
            params.append(selected_date)
        elif filter_type == "monthly" and selected_month:
            sql += " AND a.attendance_date LIKE ?"
            params.append(f"{selected_month}%")

        if selected_class:
            sql += " AND s.class_name = ?"
            params.append(selected_class)

        if selected_section:
            sql += " AND s.section = ?"
            params.append(selected_section)

        if selected_status:
            sql += " AND a.status = ?"
            params.append(selected_status)

        if search_student:
            sql += " AND (s.name LIKE ? OR s.student_id LIKE ?)"
            term = f"%{search_student}%"
            params.extend([term, term])

        sql += " ORDER BY a.attendance_date DESC, s.class_name, s.name ASC"
        records = db.execute(sql, params).fetchall()

        # Build CSV file in-memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Student ID", "Student Name", "Class", "Section",
            "Attendance Date", "Status", "Notes", "Recorded Timestamp"
        ])

        for r in records:
            writer.writerow([
                r["student_id"],
                r["student_name"],
                r["class_name"],
                r["section"],
                r["attendance_date"],
                r["status"],
                r["notes"],
                r["created_at"],
            ])

        output.seek(0)
        filename_stamp = selected_date if filter_type == "daily" else (selected_month if filter_type == "monthly" else "all")
        filename = f"cloudattend_report_{filename_stamp}.csv"

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # -------------------------------------------------------------
    # System & About Route
    # -------------------------------------------------------------
    @app.route("/system")
    @login_required
    def system_info():
        db = database.get_db()
        db_path = app.config.get("DATABASE_PATH")
        
        sqlite_version = db.execute("SELECT sqlite_version()").fetchone()[0]
        total_students = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_attendance = db.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

        return render_template(
            "system.html",
            sqlite_version=sqlite_version,
            db_path=db_path,
            total_students=total_students,
            total_attendance=total_attendance,
            total_users=total_users,
        )

    # -------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("error.html", code=403, title="Access Forbidden", message=str(error.description)), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("error.html", code=404, title="Page Not Found", message="The page or resource you requested could not be found."), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("error.html", code=500, title="Internal Server Error", message="A server error occurred. Please try again later."), 500

    def _get_existing_classes(db):
        rows = db.execute("SELECT DISTINCT class_name FROM students ORDER BY class_name").fetchall()
        return [r["class_name"] for r in rows]

    return app


# Application instance for development / WSGI
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
