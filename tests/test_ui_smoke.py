def test_smoke_all_pages_rendered_with_seeded_data(auth_client, seed_attendance_records):
    """Smoke test ensuring every single template renders with 200 OK without errors."""
    endpoints = [
        "/",
        "/dashboard",
        "/students",
        "/students/add",
        "/students/1/edit",
        "/students/1",
        "/attendance/mark",
        "/attendance/mark?attendance_date=2026-10-20&class_name=AWS+Cloud+Foundations",
        "/attendance/reports",
        "/attendance/reports?type=monthly&month=2026-10",
        "/attendance/export-csv?type=daily&date=2026-10-20",
        "/system",
    ]
    for ep in endpoints:
        resp = auth_client.get(ep)
        assert resp.status_code == 200, f"Endpoint {ep} failed with status {resp.status_code}"
