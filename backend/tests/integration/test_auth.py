"""Auth vertical slice: login → session → /auth/me → CSRF → lockout → reset."""
from tests.conftest import PASSWORD, auth_headers, login


def test_login_success_returns_roles_and_permissions(client, ids):
    csrf = login(client, "admin")
    assert csrf
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["username"] == "admin"
    assert "SUPER_ADMIN" in body["roles"]
    assert "MANAGE_USERS" in body["permissions"]
    assert body["active_year"]["name"] == "2026/2027"
    assert body["active_term"]["name"] == "Term 1"


def test_login_failure_is_uniform(client):
    r = client.post("/api/v1/auth/login",
                    json={"username": "admin", "password": "wrong-password"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"
    # unknown username returns the same error shape (no account enumeration)
    r2 = client.post("/api/v1/auth/login",
                     json={"username": "ghost", "password": "wrong-password"})
    assert r2.status_code == 401
    assert r2.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_unauthenticated_access_denied(client):
    r = client.get("/api/v1/students")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "AUTH_REQUIRED"


def test_csrf_required_on_mutations(client, ids):
    login(client, "admin")
    # no CSRF header → 403 even with a valid session
    r = client.post("/api/v1/students", json={
        "surname": "NoCSRF", "other_names": "Test", "gender": "F",
        "date_of_birth": "2018-01-01"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "CSRF_INVALID"


def test_lockout_after_failures(client, ids):
    csrf = login(client, "admin")
    # dedicated user so lockout doesn't pollute shared fixtures
    r = client.post("/api/v1/users", headers=auth_headers(csrf), json={
        "username": "locktest", "password": PASSWORD,
        "role_codes": ["TEACHER"]})
    assert r.status_code == 201, r.text

    from fastapi.testclient import TestClient
    from app.main import app
    c2 = TestClient(app)
    for _ in range(5):
        bad = c2.post("/api/v1/auth/login",
                      json={"username": "locktest", "password": "nope-nope"})
        assert bad.status_code == 401
    locked = c2.post("/api/v1/auth/login",
                     json={"username": "locktest", "password": PASSWORD})
    assert locked.status_code == 401
    assert locked.json()["error"]["code"] == "ACCOUNT_LOCKED"

    # admin unlocks → login works again
    uid = r.json()["id"]
    ur = client.post(f"/api/v1/users/{uid}/unlock", headers=auth_headers(csrf))
    assert ur.status_code == 200
    ok = c2.post("/api/v1/auth/login",
                 json={"username": "locktest", "password": PASSWORD})
    assert ok.status_code == 200


def _make_user(client, csrf, username):
    r = client.post("/api/v1/users", headers=auth_headers(csrf),
                    json={"username": username, "password": PASSWORD,
                          "role_codes": ["TEACHER"]})
    assert r.status_code == 201, r.text
    return r.json()


def test_password_reset_flow(client):
    csrf = login(client, "admin")
    _make_user(client, csrf, "resetme")
    r = client.post("/api/v1/auth/password/reset-request", json={"username": "resetme"})
    assert r.status_code == 200 and r.json()["sent"] is True
    token = r.json()["dev_token"]  # dev mode only; prod delivers via SMS/email
    assert token

    new_pass = "Reset-Password-77"
    c = client.post("/api/v1/auth/password/reset-confirm",
                    json={"token": token, "new_password": new_pass})
    assert c.status_code == 200, c.text

    from fastapi.testclient import TestClient
    from app.main import app
    c2 = TestClient(app)
    old = c2.post("/api/v1/auth/login", json={"username": "resetme", "password": PASSWORD})
    assert old.status_code == 401  # old password dead, sessions revoked
    new = c2.post("/api/v1/auth/login", json={"username": "resetme", "password": new_pass})
    assert new.status_code == 200


def test_token_reuse_rejected(client):
    csrf = login(client, "admin")
    _make_user(client, csrf, "resetme2")
    r = client.post("/api/v1/auth/password/reset-request", json={"username": "resetme2"})
    token = r.json()["dev_token"]
    ok = client.post("/api/v1/auth/password/reset-confirm",
                     json={"token": token, "new_password": "Another-Pass-55"})
    assert ok.status_code == 200
    again = client.post("/api/v1/auth/password/reset-confirm",
                        json={"token": token, "new_password": "Yet-Another-66"})
    assert again.status_code == 401
    assert again.json()["error"]["code"] == "TOKEN_INVALID"


def test_logout_revokes_session(client):
    csrf = login(client, "teacherA")
    r = client.post("/api/v1/auth/logout", headers=auth_headers(csrf))
    assert r.status_code == 200
    r2 = client.get("/api/v1/auth/me")
    assert r2.status_code == 401
