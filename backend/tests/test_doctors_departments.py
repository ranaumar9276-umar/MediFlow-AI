def test_create_department_requires_manager_or_admin(client):
    resp = client.post("/api/v1/departments", json={"name": "Neurology"})
    assert resp.status_code == 401  # no auth token at all


def test_admin_can_manage_department_and_doctor(client, admin_headers):
    dept_resp = client.post(
        "/api/v1/departments",
        json={"name": "Neurology", "description": "Brain and nervous system", "location": "Building B"},
        headers=admin_headers,
    )
    assert dept_resp.status_code == 201
    dept_id = dept_resp.json()["id"]

    doctor_resp = client.post(
        "/api/v1/doctors",
        json={
            "full_name": "Dr. Amara Okafor",
            "specialty": "Neurology",
            "email": "dr.okafor@mediflow.ai",
            "department_id": dept_id,
            "daily_capacity": 8,
        },
        headers=admin_headers,
    )
    assert doctor_resp.status_code == 201
    assert doctor_resp.json()["department_name"] == "Neurology"

    # department now reports 1 doctor
    dept_get = client.get(f"/api/v1/departments/{dept_id}", headers=admin_headers)
    assert dept_get.json()["doctor_count"] == 1


def test_duplicate_department_name_rejected(client, admin_headers):
    client.post("/api/v1/departments", json={"name": "Radiology"}, headers=admin_headers)
    dup = client.post("/api/v1/departments", json={"name": "Radiology"}, headers=admin_headers)
    assert dup.status_code == 409


def test_cannot_delete_department_with_doctors(client, admin_headers):
    dept_resp = client.post("/api/v1/departments", json={"name": "Oncology"}, headers=admin_headers)
    dept_id = dept_resp.json()["id"]
    client.post(
        "/api/v1/doctors",
        json={
            "full_name": "Dr. Onco Test",
            "specialty": "Oncology",
            "email": "dr.onco@mediflow.ai",
            "department_id": dept_id,
        },
        headers=admin_headers,
    )
    delete_resp = client.delete(f"/api/v1/departments/{dept_id}", headers=admin_headers)
    assert delete_resp.status_code == 409
