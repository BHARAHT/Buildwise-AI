from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_estimate_flow() -> None:
    payload = {
        "project": {
            "built_up_area_sqft": 1800,
            "floors": 2,
            "timeline_weeks": 36,
        },
        "compression": {"target_timeline_weeks": 28},
    }

    response = client.post("/api/v1/estimate", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["cost"]["total_cost_inr"] > 0
    assert len(data["weekly_schedule"]) == 36
    assert len(data["ai_layout_suggestions"]) == 2
    assert data["compression_impact"]["compressed_timeline_weeks"] == 28


def test_compression_validation() -> None:
    payload = {
        "project": {
            "built_up_area_sqft": 1800,
            "floors": 2,
            "timeline_weeks": 36,
        },
        "compression": {"target_timeline_weeks": 36},
    }

    response = client.post("/api/v1/estimate", json=payload)

    assert response.status_code == 422
