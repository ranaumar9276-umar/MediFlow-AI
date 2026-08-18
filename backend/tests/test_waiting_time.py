from datetime import datetime, timedelta, timezone


def _get_department_id(client, headers, name="General Medicine"):
    resp = client.get("/api/v1/departments", headers=headers)
    for dept in resp.json():
        if dept["name"] == name:
            return dept["id"]
    raise AssertionError(f"Seed department '{name}' not found")


def _create_doctor(client, headers, department_id, email):
    resp = client.post(
        "/api/v1/doctors",
        json={
            "full_name": "Dr. Wait Time",
            "specialty": "General",
            "email": email,
            "department_id": department_id,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_patient(client, headers, email):
    resp = client.post(
        "/api/v1/patients",
        json={"first_name": "Wait", "last_name": "Tester", "date_of_birth": "1990-01-01", "email": email},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_check_in_and_start_records_wait_time(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    doctor_id = _create_doctor(client, admin_headers, dept_id, "dr.waittime@mediflow.ai")
    patient_id = _create_patient(client, admin_headers, "waittime.patient@example.com")

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": dept_id,
            "scheduled_at": scheduled_at,
        },
        headers=admin_headers,
    )
    appointment_id = create_resp.json()["id"]
    assert create_resp.json()["checked_in_at"] is None
    assert create_resp.json()["wait_time_minutes"] is None

    checkin_resp = client.post(f"/api/v1/appointments/{appointment_id}/check-in", headers=admin_headers)
    assert checkin_resp.status_code == 200
    assert checkin_resp.json()["checked_in_at"] is not None

    # Cannot start before check-in already happened - but here it did, so start should succeed
    start_resp = client.post(f"/api/v1/appointments/{appointment_id}/start", headers=admin_headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["started_at"] is not None
    assert start_resp.json()["wait_time_minutes"] is not None
    assert start_resp.json()["wait_time_minutes"] >= 0


def test_cannot_start_before_check_in(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    doctor_id = _create_doctor(client, admin_headers, dept_id, "dr.nocheckin@mediflow.ai")
    patient_id = _create_patient(client, admin_headers, "nocheckin.patient@example.com")

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create_resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": dept_id,
            "scheduled_at": scheduled_at,
        },
        headers=admin_headers,
    )
    appointment_id = create_resp.json()["id"]

    start_resp = client.post(f"/api/v1/appointments/{appointment_id}/start", headers=admin_headers)
    assert start_resp.status_code == 400


def test_cannot_check_in_twice(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    doctor_id = _create_doctor(client, admin_headers, dept_id, "dr.doublecheckin@mediflow.ai")
    patient_id = _create_patient(client, admin_headers, "doublecheckin.patient@example.com")

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    create_resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": dept_id,
            "scheduled_at": scheduled_at,
        },
        headers=admin_headers,
    )
    appointment_id = create_resp.json()["id"]

    first = client.post(f"/api/v1/appointments/{appointment_id}/check-in", headers=admin_headers)
    assert first.status_code == 200
    second = client.post(f"/api/v1/appointments/{appointment_id}/check-in", headers=admin_headers)
    assert second.status_code == 400
