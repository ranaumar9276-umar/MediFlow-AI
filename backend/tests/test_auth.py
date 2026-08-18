def test_login_success(client):
    resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "admin@mediflow.ai", "password": "Admin@12345"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["role"] == "ADMIN"


def test_login_wrong_password(client):
    resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "admin@mediflow.ai", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "nobody@mediflow.ai", "password": "whatever123"},
    )
    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, admin_headers):
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@mediflow.ai"
    assert resp.json()["role"] == "ADMIN"


def test_register_requires_admin_role(client):
    # No token at all -> 401
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "staff1@mediflow.ai", "password": "Staff@1234", "full_name": "Staff One", "role": "STAFF"},
    )
    assert resp.status_code == 401


def test_admin_can_register_new_staff(client, admin_headers):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "staff2@mediflow.ai", "password": "Staff@1234", "full_name": "Staff Two", "role": "STAFF"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "STAFF"

    # New staff account can log in
    login_resp = client.post(
        "/api/v1/auth/login-json", json={"email": "staff2@mediflow.ai", "password": "Staff@1234"}
    )
    assert login_resp.status_code == 200

    # And a non-admin (STAFF) cannot register more users - authorization enforced server-side
    staff_token = login_resp.json()["access_token"]
    forbidden_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "staff3@mediflow.ai", "password": "Staff@1234", "full_name": "Staff Three", "role": "STAFF"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert forbidden_resp.status_code == 403
