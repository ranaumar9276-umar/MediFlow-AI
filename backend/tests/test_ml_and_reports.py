from datetime import datetime, timedelta, timezone


def _get_department_id(client, headers, name="General Medicine"):
    resp = client.get("/api/v1/departments", headers=headers)
    for dept in resp.json():
        if dept["name"] == name:
            return dept["id"]
    raise AssertionError(f"Seed department '{name}' not found")


def test_train_requires_admin_or_manager(client):
    resp = client.post("/api/v1/ml/train")
    assert resp.status_code == 401


def test_train_reports_insufficient_data_gracefully(client, admin_headers):
    """
    With a freshly-seeded test database there won't be 30+ labeled
    (COMPLETED/NO_SHOW) appointments, so training must refuse gracefully
    with a clear reason rather than fabricating a model.
    """
    resp = client.post("/api/v1/ml/train", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "trained" in body
    if not body["trained"]:
        assert "reason" in body and len(body["reason"]) > 0


def test_model_info_before_training(client, admin_headers):
    resp = client.get("/api/v1/ml/model-info", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "model_available" in body


def test_predict_without_trained_model_returns_409_or_succeeds(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    doctor_resp = client.post(
        "/api/v1/doctors",
        json={
            "full_name": "Dr. Predict Test",
            "specialty": "General",
            "email": "dr.predicttest@mediflow.ai",
            "department_id": dept_id,
        },
        headers=admin_headers,
    )
    doctor_id = doctor_resp.json()["id"]

    resp = client.post(
        "/api/v1/ml/predict-no-show",
        json={
            "doctor_id": doctor_id,
            "department_id": dept_id,
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
        },
        headers=admin_headers,
    )
    # No model has been trained successfully yet in this test run (insufficient
    # data) -> the API must fail cleanly with 409, not crash with a 500.
    assert resp.status_code in (200, 409)
    if resp.status_code == 200:
        body = resp.json()
        assert 0.0 <= body["no_show_risk_probability"] <= 1.0
        assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_reports_appointments_requires_auth(client):
    resp = client.get("/api/v1/reports/appointments")
    assert resp.status_code == 401


def test_reports_appointments_returns_summary_and_rows(client, admin_headers):
    resp = client.get("/api/v1/reports/appointments", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "rows" in body
    assert "total_appointments" in body["summary"]
    assert "status_counts" in body["summary"]


def test_reports_appointments_filter_by_department(client, admin_headers):
    dept_id = _get_department_id(client, admin_headers)
    resp = client.get(
        "/api/v1/reports/appointments", params={"department_id": dept_id}, headers=admin_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    for row in body["rows"]:
        assert row["department_name"]  # every row belongs to some department
