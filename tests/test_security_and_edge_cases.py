import pytest
from werkzeug.security import check_password_hash
import database
import io
import csv


def test_password_stored_as_secure_hash(app):
    """Test that passwords in the database are cryptographically hashed and never plaintext."""
    with app.app_context():
        db = database.get_db()
        admin = db.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
        assert admin is not None
        # Must not be plaintext
        assert admin["password_hash"] != "Admin@Cloud2026"
        # Must be valid Werkzeug hash format (scrypt or pbkdf2)
        assert admin["password_hash"].startswith(("scrypt:", "pbkdf2:"))
        # Must successfully verify
        assert check_password_hash(admin["password_hash"], "Admin@Cloud2026")


def test_csrf_protection_blocks_forged_requests(app, client):
    """Test that POST requests without a valid CSRF token are blocked with 403 when CSRF is enabled."""
    app.config["WTF_CSRF_ENABLED"] = True

    # Authenticate
    with client.session_transaction() as sess:
        sess["user"] = {"id": 1, "username": "admin", "full_name": "Admin", "role": "admin"}
        sess["csrf_token"] = "valid-secret-session-token"

    # POST request with NO CSRF token
    response = client.post(
        "/students/add",
        data={
            "student_id": "STU-FORGED",
            "name": "Attacker",
            "class_name": "Class A",
            "section": "Sec 1",
        }
    )
    assert response.status_code == 403
    assert b"CSRF" in response.data

    # POST request with WRONG CSRF token
    response_wrong = client.post(
        "/students/add",
        data={
            "csrf_token": "wrong-token-12345",
            "student_id": "STU-FORGED",
            "name": "Attacker",
            "class_name": "Class A",
            "section": "Sec 1",
        }
    )
    assert response_wrong.status_code == 403

    # POST request with CORRECT CSRF token
    response_correct = client.post(
        "/students/add",
        data={
            "csrf_token": "valid-secret-session-token",
            "student_id": "STU-LEGIT",
            "name": "Legitimate Student",
            "class_name": "Class A",
            "section": "Sec 1",
        },
        follow_redirects=True
    )
    assert response_correct.status_code == 200
    assert b"Legitimate Student" in response_correct.data


def test_export_csv_empty_dataset(auth_client):
    """Test exporting CSV when no records match filter (should return CSV with only headers)."""
    res = auth_client.get("/attendance/export-csv?type=daily&date=1990-01-01")
    assert res.status_code == 200
    content = res.data.decode("utf-8")
    reader = list(csv.reader(io.StringIO(content)))
    assert len(reader) == 1  # Header only
    assert reader[0][0] == "Student ID"
