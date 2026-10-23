import pytest
import database
import io
import csv


def test_reports_daily_view(auth_client, seed_attendance_records):
    """Test daily report filter."""
    res = auth_client.get("/attendance/reports?type=daily&date=2026-10-20")
    assert res.status_code == 200
    assert b"Showing daily report for <strong>2026-10-20</strong>" in res.data
    assert b"Alice Johnson" in res.data
    assert b"Bob Smith" in res.data
    # On 2026-10-20 both Alice and Bob are present -> 100.0%
    assert b"100.0%" in res.data


def test_reports_monthly_view(auth_client, seed_attendance_records):
    """Test monthly report filter."""
    res = auth_client.get("/attendance/reports?type=monthly&month=2026-10")
    assert res.status_code == 200
    assert b"Showing monthly report for <strong>2026-10</strong>" in res.data
    # Total records = 6, Present = 4, 4/6 = 66.7%
    assert b"66.7%" in res.data


def test_reports_status_filtering(auth_client, seed_attendance_records):
    """Test filtering by status 'Absent'."""
    res = auth_client.get("/attendance/reports?type=all&status=Absent")
    assert res.status_code == 200
    assert b"Alice Johnson" in res.data
    assert b"Sick" in res.data
    # Filtered Records should be 1
    assert b"Filtered Records" in res.data


def test_zero_records_calculation_handling(auth_client):
    """
    Test zero-division handling: when there are 0 records matching the filter,
    attendance percentage should safely calculate to 0.0% and not crash.
    """
    res = auth_client.get("/attendance/reports?type=daily&date=1999-01-01")
    assert res.status_code == 200
    assert b"0.0%" in res.data
    assert b"No Records Found" in res.data


def test_export_csv_headers_and_content(auth_client, seed_attendance_records):
    """Test CSV export functionality."""
    res = auth_client.get("/attendance/export-csv?type=daily&date=2026-10-20")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "attachment; filename=cloudattend_report_2026-10-20.csv" in res.headers.get("Content-Disposition", "")

    # Parse and verify CSV contents
    content = res.data.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    # Check header
    header = rows[0]
    expected_header = [
        "Student ID", "Student Name", "Class", "Section",
        "Attendance Date", "Status", "Notes", "Recorded Timestamp"
    ]
    assert header == expected_header

    # Check data rows
    assert len(rows) == 3  # Header + 2 student rows for 2026-10-20
    data_row_1 = rows[1]
    assert data_row_1[0] == "TEST-001"
    assert data_row_1[1] == "Alice Johnson"
    assert data_row_1[4] == "2026-10-20"
    assert data_row_1[5] == "Present"
