from datetime import datetime, timedelta, timezone


def test_dashboard_summary_requires_auth(client):
    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 401


def test_dashboard_summary_reflects_real_data(client, admin_headers):
    before = client.get("/api/v1/dashboard/summary", headers=admin_headers).json()
    baseline_patients = before["total_patients"]

    # Create a new patient and confirm the dashboard total increments -
    # proving the number is computed live, not hardcoded.
    client.post(
        "/api/v1/patients",
        json={
            "first_name": "Dash",
            "last_name": "Board",
            "date_of_birth": "1995-02-02",
            "email": "dash.board@example.com",
        },
        headers=admin_headers,
    )

    after = client.get("/api/v1/dashboard/summary", headers=admin_headers).json()
    assert after["total_patients"] == baseline_patients + 1
    assert "department_workload" in after
    assert "appointment_trend_last_14_days" in after
    assert len(after["appointment_trend_last_14_days"]) == 14


def test_analytics_appointment_statistics(client, admin_headers):
    resp = client.get("/api/v1/analytics/appointment-statistics", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "row_count" in body
    assert "statistics" in body
    assert "weekday_distribution" in body
