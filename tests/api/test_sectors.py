from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    first = data[0]
    assert "sector" in first
    assert "company_count" in first
    assert "median_roe" in first
    assert "median_pe" in first
    assert "median_de" in first

def test_get_sector_companies():
    response = client.get("/api/v1/sectors/Information Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    first = data[0]
    assert "ticker" in first
    assert "company_name" in first
    assert "latest_kpis" in first

def test_get_sector_companies_not_found():
    response = client.get("/api/v1/sectors/NONEXISTENT/companies")
    assert response.status_code == 404
