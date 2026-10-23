import pytest
import tempfile
import os
from werkzeug.security import generate_password_hash
from app import create_app
import database


@pytest.fixture
def app():
    """Create and configure a new application instance for each test with a clean temp DB."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    test_app = create_app("testing")
    test_app.config["DATABASE_PATH"] = db_path
    test_app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF in tests for clean programmatic POSTs
    test_app.config["TESTING"] = True

    with test_app.app_context():
        database.init_db()
        # Seed test admin
        db = database.get_db()
        db.execute(
            """
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, 'admin')
            """,
            ("admin", generate_password_hash("Admin@Cloud2026"), "Test Admin", "admin@test.local")
        )
        db.commit()

    yield test_app

    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """A test client pre-authenticated with administrator session."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": 1,
            "username": "admin",
            "full_name": "Test Admin",
            "role": "admin",
            "email": "admin@test.local",
        }
        sess["csrf_token"] = "test-token"
    return client


@pytest.fixture
def seed_students(app):
    """Fixture that seeds sample students for testing."""
    with app.app_context():
        db = database.get_db()
        cursor = db.execute(
            """
            INSERT INTO students (student_id, name, class_name, section, email, status)
            VALUES 
                ('TEST-001', 'Alice Johnson', 'AWS Cloud Foundations', 'Section A', 'alice@test.local', 'Active'),
                ('TEST-002', 'Bob Smith', 'AWS Cloud Foundations', 'Section A', 'bob@test.local', 'Active'),
                ('TEST-003', 'Charlie Brown', 'DevOps & SysOps', 'Section B', 'charlie@test.local', 'Active')
            """
        )
        db.commit()
    return [1, 2, 3]


@pytest.fixture
def seed_attendance_records(app, seed_students):
    """Seed sample attendance records for reporting and UI tests."""
    with app.app_context():
        db = database.get_db()
        # Alice (id 1): 2 Present, 1 Absent -> 66.7%
        # Bob (id 2): 2 Present, 1 Late
        db.execute(
            """
            INSERT INTO attendance (student_id, attendance_date, status, notes)
            VALUES 
                (1, '2026-10-20', 'Present', 'Good'),
                (1, '2026-10-21', 'Present', 'Good'),
                (1, '2026-10-22', 'Absent', 'Sick'),
                (2, '2026-10-20', 'Present', 'Good'),
                (2, '2026-10-21', 'Late', 'Traffic'),
                (2, '2026-10-22', 'Present', 'Good')
            """
        )
        db.commit()

