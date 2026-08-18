def test_waiting_time_analytics_endpoint(client, admin_headers):
    resp = client.get("/api/v1/analytics/waiting-time", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "has_data" in body
    assert "sample_size" in body


def test_peak_periods_endpoint(client, admin_headers):
    resp = client.get("/api/v1/analytics/peak-periods", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "hourly_distribution" in body


def test_cancellation_no_show_endpoint(client, admin_headers):
    resp = client.get("/api/v1/analytics/cancellation-no-show", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "by_department" in body
    assert "by_doctor" in body


def test_data_quality_endpoint(client, admin_headers):
    resp = client.get("/api/v1/analytics/data-quality", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "patients" in body
    assert "appointments" in body
    assert "quality_score_percent" in body["patients"]


def test_eda_charts_endpoint_returns_base64_or_none(client, admin_headers):
    resp = client.get("/api/v1/analytics/eda-charts", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    for key in ("duration_distribution", "weekday_hour_heatmap", "department_status_breakdown"):
        assert key in body
        # Either None (not enough data) or a non-empty base64 string
        assert body[key] is None or (isinstance(body[key], str) and len(body[key]) > 100)


def test_forecast_endpoint_reports_insufficient_history_gracefully(client, admin_headers):
    resp = client.get("/api/v1/analytics/forecast", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "forecastable" in body
    # With little/no seeded appointment history, forecastable should be False
    # and a clear reason must be given rather than a fabricated forecast.
    if not body["forecastable"]:
        assert "reason" in body and len(body["reason"]) > 0


def test_alerts_endpoint_requires_auth(client):
    resp = client.get("/api/v1/analytics/alerts")
    assert resp.status_code == 401


def test_alerts_endpoint_returns_list(client, admin_headers):
    resp = client.get("/api/v1/analytics/alerts", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "alerts" in body
    assert isinstance(body["alerts"], list)
    for alert in body["alerts"]:
        assert alert["severity"] in ("critical", "warning", "info")
        assert "message" in alert
