import pytest
import database


def test_list_students(auth_client, seed_students):
    """Test viewing the student directory."""
    response = auth_client.get("/students")
    assert response.status_code == 200
    assert b"Alice Johnson" in response.data
    assert b"Bob Smith" in response.data
    assert b"TEST-001" in response.data


def test_add_student_successful(app, auth_client):
    """Test adding a new student with valid data."""
    response = auth_client.post(
        "/students/add",
        data={
            "student_id": "NEW-101",
            "name": "Diana Prince",
            "class_name": "Cloud Security & Architecture",
            "section": "Section A",
            "email": "diana@test.local",
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Diana Prince" in response.data
    assert b"added successfully" in response.data

    with app.app_context():
        db = database.get_db()
        row = db.execute("SELECT * FROM students WHERE student_id = 'NEW-101'").fetchone()
        assert row is not None
        assert row["name"] == "Diana Prince"
        assert row["class_name"] == "Cloud Security & Architecture"


def test_add_student_duplicate_id_prevented(auth_client, seed_students):
    """Test that duplicate student IDs are rejected."""
    response = auth_client.post(
        "/students/add",
        data={
            "student_id": "TEST-001",  # Already exists from fixture
            "name": "Duplicate Person",
            "class_name": "AWS Cloud Foundations",
            "section": "Section A",
            "email": "dup@test.local",
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"is already in use" in response.data


def test_add_student_validation_errors(auth_client):
    """Test validation errors for empty fields and bad inputs."""
    # Empty ID
    response = auth_client.post(
        "/students/add",
        data={
            "student_id": "",
            "name": "No ID Student",
            "class_name": "Class A",
            "section": "A",
        },
        follow_redirects=True
    )
    assert b"Student ID is required" in response.data

    # Invalid email
    response = auth_client.post(
        "/students/add",
        data={
            "student_id": "STU-999",
            "name": "Bad Email Student",
            "class_name": "Class A",
            "section": "A",
            "email": "invalid-email-format",
        },
        follow_redirects=True
    )
    assert b"Invalid email address format" in response.data


def test_edit_student(app, auth_client, seed_students):
    """Test updating existing student details."""
    response = auth_client.post(
        "/students/1/edit",
        data={
            "student_id": "TEST-001-MOD",
            "name": "Alice Johnson Updated",
            "class_name": "AWS Advanced Cloud",
            "section": "Section X",
            "email": "alice.updated@test.local",
            "status": "Active",
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"updated successfully" in response.data

    with app.app_context():
        db = database.get_db()
        row = db.execute("SELECT * FROM students WHERE id = 1").fetchone()
        assert row["student_id"] == "TEST-001-MOD"
        assert row["name"] == "Alice Johnson Updated"
        assert row["class_name"] == "AWS Advanced Cloud"


def test_delete_student(app, auth_client, seed_students):
    """Test deleting student record."""
    response = auth_client.post("/students/1/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"have been deleted" in response.data

    with app.app_context():
        db = database.get_db()
        row = db.execute("SELECT * FROM students WHERE id = 1").fetchone()
        assert row is None


def test_search_and_filter_students(auth_client, seed_students):
    """Test searching by student query and filtering by class."""
    # Search by name
    res = auth_client.get("/students?q=Bob")
    assert b"Bob Smith" in res.data
    assert b"Alice Johnson" not in res.data

    # Filter by class
    res2 = auth_client.get("/students?class_name=DevOps+%26+SysOps")
    assert b"Charlie Brown" in res2.data
    assert b"Alice Johnson" not in res2.data


def test_view_student_dossier(auth_client, seed_students):
    """Test viewing student dossier."""
    res = auth_client.get("/students/1")
    assert res.status_code == 200
    assert b"Alice Johnson" in res.data
    assert b"Dossier" in res.data
