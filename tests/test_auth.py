import pytest
from flask import session


def test_login_page_renders(client):
    """Test that login page loads successfully."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Administrator Login" in response.data
    assert b"CloudAttend" in response.data


def test_login_successful(client):
    """Test successful admin login with valid credentials."""
    response = client.post(
        "/login",
        data={"username": "admin", "password": "Admin@Cloud2026"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Welcome back, Test Admin!" in response.data
    assert b"Executive Dashboard" in response.data


def test_login_invalid_password(client):
    """Test login failure with wrong password."""
    response = client.post(
        "/login",
        data={"username": "admin", "password": "WrongPassword123"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_login_nonexistent_user(client):
    """Test login failure with unknown user."""
    response = client.post(
        "/login",
        data={"username": "nonexistent", "password": "SomePassword"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_logout(auth_client):
    """Test logout clears session and redirects to login."""
    response = auth_client.post("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been securely logged out." in response.data
    assert b"Administrator Login" in response.data


@pytest.mark.parametrize("protected_url", [
    "/",
    "/dashboard",
    "/students",
    "/students/add",
    "/attendance/mark",
    "/attendance/reports",
    "/attendance/export-csv",
    "/system"
])
def test_unauthorized_access_redirects_to_login(client, protected_url):
    """Test that all sensitive management routes require authentication."""
    response = client.get(protected_url, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
