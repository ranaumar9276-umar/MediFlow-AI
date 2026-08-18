def _create_patient(client, headers, **overrides):
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-05-10",
        "gender": "FEMALE",
        "phone": "+1-555-0100",
        "email": "jane.doe@example.com",
        "blood_type": "O+",
    }
    payload.update(overrides)
    return client.post("/api/v1/patients", json=payload, headers=headers)


def test_create_patient(client, admin_headers):
    resp = _create_patient(client, admin_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["full_name"] == "Jane Doe"
    assert body["appointment_count"] == 0


def test_list_patients_requires_auth(client):
    resp = client.get("/api/v1/patients")
    assert resp.status_code == 401


def test_list_and_search_patients(client, admin_headers):
    _create_patient(client, admin_headers, first_name="Alice", last_name="Smith", email="alice@example.com")
    _create_patient(client, admin_headers, first_name="Bob", last_name="Jones", email="bob@example.com")

    resp = client.get("/api/v1/patients", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 2

    search_resp = client.get("/api/v1/patients", params={"search": "alice"}, headers=admin_headers)
    names = [p["full_name"] for p in search_resp.json()["items"]]
    assert any("Alice" in n for n in names)


def test_get_update_delete_patient(client, admin_headers):
    create_resp = _create_patient(client, admin_headers, first_name="Carl", last_name="White", email="carl@example.com")
    patient_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/patients/{patient_id}", headers=admin_headers)
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/api/v1/patients/{patient_id}", json={"phone": "+1-555-9999"}, headers=admin_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["phone"] == "+1-555-9999"

    delete_resp = client.delete(f"/api/v1/patients/{patient_id}", headers=admin_headers)
    assert delete_resp.status_code == 204

    missing_resp = client.get(f"/api/v1/patients/{patient_id}", headers=admin_headers)
    assert missing_resp.status_code == 404


def test_patient_validation_error(client, admin_headers):
    resp = client.post(
        "/api/v1/patients",
        json={"first_name": "", "last_name": "Doe", "date_of_birth": "not-a-date"},
        headers=admin_headers,
    )
    assert resp.status_code == 422
