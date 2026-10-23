import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta, date
import random
from flask import g, current_app
import click
from werkzeug.security import generate_password_hash

# Base directory
BASE_DIR = Path(__file__).resolve().parent


def get_db(custom_path=None):
    """
    Get a database connection for the current request context.
    If custom_path is provided, connects directly (useful for tests or migrations).
    """
    if custom_path:
        conn = sqlite3.connect(custom_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    if "db" not in g:
        db_path = current_app.config.get("DATABASE_PATH")
        # Ensure parent directory exists for file-based sqlite databases
        if db_path != ":memory:":
            parent_dir = Path(db_path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path=None):
    """Initialize database tables using schema.sql."""
    schema_path = BASE_DIR / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    if db_path:
        conn = get_db(db_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
    else:
        db = get_db()
        db.executescript(schema_sql)
        db.commit()


def seed_db(db_conn=None):
    """
    Seed database with:
    1. Default administrator account
    2. Realistic fictional students (no real student data)
    3. Attendance records across multiple recent dates
    """
    close_after = False
    if db_conn is None:
        db = get_db()
    else:
        db = db_conn

    # 1. Seed Administrator
    admin_user = current_app.config.get("DEFAULT_ADMIN_USER", "admin")
    admin_pass = current_app.config.get("DEFAULT_ADMIN_PASS", "Admin@Cloud2026")
    admin_name = current_app.config.get("DEFAULT_ADMIN_NAME", "System Administrator")
    admin_email = current_app.config.get("DEFAULT_ADMIN_EMAIL", "admin@cloudattend.internal")

    existing_admin = db.execute(
        "SELECT id FROM users WHERE username = ?", (admin_user,)
    ).fetchone()

    admin_id = None
    if not existing_admin:
        hashed_pw = generate_password_hash(admin_pass)
        cursor = db.execute(
            """
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, 'admin')
            """,
            (admin_user, hashed_pw, admin_name, admin_email)
        )
        admin_id = cursor.lastrowid
    else:
        admin_id = existing_admin["id"]

    # 2. Seed Fictional Students
    fictional_students = [
        # AWS Cloud Foundations - Section A
        ("STU-1001", "Alex Chen", "AWS Cloud Foundations", "Section A", "alex.chen.demo@cloudattend.test"),
        ("STU-1002", "Jordan Taylor", "AWS Cloud Foundations", "Section A", "jordan.taylor.demo@cloudattend.test"),
        ("STU-1003", "Samira Khan", "AWS Cloud Foundations", "Section A", "samira.khan.demo@cloudattend.test"),
        ("STU-1004", "Marcus Vance", "AWS Cloud Foundations", "Section A", "marcus.vance.demo@cloudattend.test"),
        ("STU-1005", "Elena Rostova", "AWS Cloud Foundations", "Section A", "elena.rostova.demo@cloudattend.test"),

        # AWS Cloud Foundations - Section B
        ("STU-1006", "Devon Miller", "AWS Cloud Foundations", "Section B", "devon.miller.demo@cloudattend.test"),
        ("STU-1007", "Priya Patel", "AWS Cloud Foundations", "Section B", "priya.patel.demo@cloudattend.test"),
        ("STU-1008", "Liam O'Connor", "AWS Cloud Foundations", "Section B", "liam.oconnor.demo@cloudattend.test"),
        ("STU-1009", "Zara Morales", "AWS Cloud Foundations", "Section B", "zara.morales.demo@cloudattend.test"),
        ("STU-1010", "Kevin Zhang", "AWS Cloud Foundations", "Section B", "kevin.zhang.demo@cloudattend.test"),

        # DevOps & SysOps - Section A
        ("STU-2001", "Amina Bello", "DevOps & SysOps", "Section A", "amina.bello.demo@cloudattend.test"),
        ("STU-2002", "Noah Lindqvist", "DevOps & SysOps", "Section A", "noah.l.demo@cloudattend.test"),
        ("STU-2003", "Chloe Dubois", "DevOps & SysOps", "Section A", "chloe.d.demo@cloudattend.test"),
        ("STU-2004", "Rohan Gupta", "DevOps & SysOps", "Section A", "rohan.g.demo@cloudattend.test"),
        ("STU-2005", "Maya Takahashi", "DevOps & SysOps", "Section A", "maya.t.demo@cloudattend.test"),

        # Cloud Security & Architecture - Section A
        ("STU-3001", "Gabriel Santos", "Cloud Security & Architecture", "Section A", "gabriel.s.demo@cloudattend.test"),
        ("STU-3002", "Fatima Al-Hassan", "Cloud Security & Architecture", "Section A", "fatima.a.demo@cloudattend.test"),
        ("STU-3003", "Lucas Meyer", "Cloud Security & Architecture", "Section A", "lucas.m.demo@cloudattend.test"),
    ]

    student_id_map = {}
    for sid, name, cname, sec, email in fictional_students:
        row = db.execute(
            "SELECT id FROM students WHERE student_id = ?", (sid,)
        ).fetchone()
        if not row:
            cur = db.execute(
                """
                INSERT INTO students (student_id, name, class_name, section, email, status)
                VALUES (?, ?, ?, ?, ?, 'Active')
                """,
                (sid, name, cname, sec, email)
            )
            student_id_map[sid] = cur.lastrowid
        else:
            student_id_map[sid] = row["id"]

    # 3. Seed Realistic Attendance Records
    # Generate records for the past 7 weekdays including today
    today = date.today()
    past_dates = []
    
    # Collect last 7 weekdays
    current_check = today
    while len(past_dates) < 7:
        # 0=Mon, ..., 4=Fri, 5=Sat, 6=Sun
        if current_check.weekday() < 5:  # Monday to Friday
            past_dates.append(current_check.isoformat())
        current_check -= timedelta(days=1)

    # In case today is weekend, past_dates still has valid recent dates
    # Seed attendance with predetermined pseudo-random distribution
    # High present rate (~80%), occasional late (~12%), rare absent (~8%)
    # Use deterministic seed so tests and demo are consistent
    rnd = random.Random(42)
    statuses = ["Present"] * 8 + ["Late"] * 1 + ["Absent"] * 1

    for dt in past_dates:
        for sid, db_stu_id in student_id_map.items():
            status = rnd.choice(statuses)
            note = ""
            if status == "Late":
                note = "Arrived 15 minutes after session start"
            elif status == "Absent":
                note = "Excused medical / personal leave"

            db.execute(
                """
                INSERT OR IGNORE INTO attendance (student_id, attendance_date, status, notes, recorded_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (db_stu_id, dt, status, note, admin_id)
            )

    db.commit()


@click.command("init-db")
def init_db_command():
    """Clear existing data and create new database tables."""
    init_db()
    click.echo("Initialized the SQLite database schema.")


@click.command("seed-db")
def seed_db_command():
    """Seed the database with admin user and fictional student dataset."""
    seed_db()
    click.echo("Database seeded with demo admin and fictional students.")


def init_app(app):
    """Register database functions and CLI commands with the Flask application."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
