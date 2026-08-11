from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_screener_no_filters():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Ranked ordering check
    for i in range(len(data) - 1):
        score_i = data[i]["composite_score"]
        score_next = data[i+1]["composite_score"]
        if score_i is not None and score_next is not None:
            assert score_i >= score_next

def test_screener_with_filters():
    response = client.get("/api/v1/screener?min_roe=15&max_de=1.5&sector=Information Technology")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["roe"] >= 15.0
        assert item["de"] <= 1.5
        assert item["sector"].lower() == "information technology"
