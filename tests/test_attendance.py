import pytest
import sqlite3
import database


def test_mark_attendance_page_loads(auth_client, seed_students):
    """Test attendance taking form loads for a selected class."""
    response = auth_client.get(
        "/attendance/mark?attendance_date=2026-10-23&class_name=AWS+Cloud+Foundations"
    )
    assert response.status_code == 200
    assert b"Alice Johnson" in response.data
    assert b"Bob Smith" in response.data
    assert b"Save Attendance Records" in response.data


def test_mark_attendance_post_successful(app, auth_client, seed_students):
    """Test saving attendance entries for enrolled students."""
    response = auth_client.post(
        "/attendance/mark",
        data={
            "attendance_date": "2026-10-23",
            "class_name": "AWS Cloud Foundations",
            "section": "Section A",
            "status_1": "Present",
            "notes_1": "On time",
            "status_2": "Late",
            "notes_2": "10 min late",
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Attendance saved" in response.data

    with app.app_context():
        db = database.get_db()
        records = db.execute(
            "SELECT * FROM attendance WHERE attendance_date = '2026-10-23' ORDER BY student_id"
        ).fetchall()
        assert len(records) == 2
        assert records[0]["status"] == "Present"
        assert records[0]["notes"] == "On time"
        assert records[1]["status"] == "Late"
        assert records[1]["notes"] == "10 min late"


def test_duplicate_attendance_prevention_and_update(app, auth_client, seed_students):
    """
    Test that taking attendance again on the same date updates the record
    and does NOT create duplicate rows.
    """
    # 1. First submission: Alice is marked 'Present'
    auth_client.post(
        "/attendance/mark",
        data={
            "attendance_date": "2026-10-23",
            "class_name": "AWS Cloud Foundations",
            "section": "Section A",
            "status_1": "Present",
            "notes_1": "Initial entry",
        },
        follow_redirects=True
    )

    with app.app_context():
        db = database.get_db()
        count = db.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id = 1 AND attendance_date = '2026-10-23'"
        ).fetchone()[0]
        assert count == 1

    # 2. Second submission on the same date: Alice is changed to 'Absent'
    auth_client.post(
        "/attendance/mark",
        data={
            "attendance_date": "2026-10-23",
            "class_name": "AWS Cloud Foundations",
            "section": "Section A",
            "status_1": "Absent",
            "notes_1": "Had to leave early",
        },
        follow_redirects=True
    )

    with app.app_context():
        db = database.get_db()
        # Row count MUST still be 1 (strictly no duplicates)
        count = db.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id = 1 AND attendance_date = '2026-10-23'"
        ).fetchone()[0]
        assert count == 1

        record = db.execute(
            "SELECT * FROM attendance WHERE student_id = 1 AND attendance_date = '2026-10-23'"
        ).fetchone()
        assert record["status"] == "Absent"
        assert record["notes"] == "Had to leave early"


def test_database_unique_constraint_enforced(app, seed_students):
    """Test that SQLite schema constraint UNIQUE(student_id, attendance_date) raises IntegrityError on direct duplicate insert."""
    with app.app_context():
        db = database.get_db()
        db.execute(
            "INSERT INTO attendance (student_id, attendance_date, status) VALUES (1, '2026-10-23', 'Present')"
        )
        db.commit()

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO attendance (student_id, attendance_date, status) VALUES (1, '2026-10-23', 'Absent')"
            )


def test_invalid_date_rejected(auth_client, seed_students):
    """Test rejection of non-ISO invalid dates."""
    response = auth_client.post(
        "/attendance/mark",
        data={
            "attendance_date": "not-a-valid-date",
            "class_name": "AWS Cloud Foundations",
            "status_1": "Present",
        },
        follow_redirects=True
    )
    assert b"Please provide a valid attendance date" in response.data
