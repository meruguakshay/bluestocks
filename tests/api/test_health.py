from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "version" in data
    assert "db_row_counts" in data
    
    # Verify row counts contain expected tables
    counts = data["db_row_counts"]
    assert "companies" in counts
    assert "profitandloss" in counts
    assert "balancesheet" in counts
    assert "cashflow" in counts
    assert "financial_ratios" in counts
    assert "peer_percentiles" in counts
