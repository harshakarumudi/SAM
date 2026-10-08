from jose import jwt

from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    raw_pass = "SecurePass123!"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_payload():
    data = {"sub": "agri_admin", "role": "ADMIN"}
    token = create_access_token(data)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "agri_admin"
    assert decoded["role"] == "ADMIN"
    assert "exp" in decoded


def test_login_api_success(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@Secure2026!"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"


def test_login_api_invalid_credentials(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "BadPassword123!"}
    )
    assert resp.status_code == 401
    assert "Incorrect username or password" in resp.json()["detail"]
