from datetime import datetime, timedelta, timezone


def _get_department_id(client, headers, name="General Medicine"):
    resp = client.get("/api/v1/departments", headers=headers)
    for dept in resp.json():
        if dept["name"] == name:
            return dept["id"]
    raise AssertionError(f"Seed department '{name}' not found")


def _create_doctor(client, headers, department_id, email="dr.house@mediflow.ai"):
    resp = client.post(
        "/api/v1/doctors",
        json={
            "full_name": "Dr. Gregory House",
            "specialty": "Diagnostics",
            "email": email,
            "department_id": department_id,
            "daily_capacity": 10,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_patient(client, headers, email="patient.appt@example.com"):
    resp = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Appt",
            "last_name": "Tester",
            "date_of_birth": "1985-01-01",
            "email": email,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_appointment_full_lifecycle(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    doctor_id = _create_doctor(client, admin_headers, dept_id, email="dr.lifecycle@mediflow.ai")
    patient_id = _create_patient(client, admin_headers, email="lifecycle.patient@example.com")

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    create_resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": dept_id,
            "scheduled_at": scheduled_at,
            "duration_minutes": 30,
            "reason": "Annual checkup",
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    appointment_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "SCHEDULED"

    complete_resp = client.post(f"/api/v1/appointments/{appointment_id}/complete", headers=admin_headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"


def test_appointment_double_booking_is_rejected(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    doctor_id = _create_doctor(client, admin_headers, dept_id, email="dr.conflict@mediflow.ai")
    patient_a = _create_patient(client, admin_headers, email="patient.a@example.com")
    patient_b = _create_patient(client, admin_headers, email="patient.b@example.com")

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    first = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_a,
            "doctor_id": doctor_id,
            "department_id": dept_id,
            "scheduled_at": scheduled_at,
            "duration_minutes": 30,
        },
        headers=admin_headers,
    )
    assert first.status_code == 201

    # Overlapping slot for the SAME doctor must be rejected
    second = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_b,
            "doctor_id": doctor_id,
            "department_id": dept_id,
            "scheduled_at": scheduled_at,
            "duration_minutes": 30,
        },
        headers=admin_headers,
    )
    assert second.status_code == 409


def test_cancel_appointment(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    doctor_id = _create_doctor(client, admin_headers, dept_id, email="dr.cancel@mediflow.ai")
    patient_id = _create_patient(client, admin_headers, email="cancel.patient@example.com")

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

    cancel_resp = client.post(f"/api/v1/appointments/{appointment_id}/cancel", headers=admin_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Cancelling again should fail - only SCHEDULED appointments can be cancelled
    second_cancel = client.post(f"/api/v1/appointments/{appointment_id}/cancel", headers=admin_headers)
    assert second_cancel.status_code == 400


def test_appointment_invalid_doctor_department_mismatch(client, admin_headers):
    dept_a = _get_department_id(client, admin_headers, "General Medicine")
    dept_b = _get_department_id(client, admin_headers, "Cardiology")
    doctor_id = _create_doctor(client, admin_headers, dept_a, email="dr.mismatch@mediflow.ai")
    patient_id = _create_patient(client, admin_headers, email="mismatch.patient@example.com")

    resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": dept_b,  # wrong department for this doctor
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=4)).isoformat(),
        },
        headers=admin_headers,
    )
    assert resp.status_code == 400
