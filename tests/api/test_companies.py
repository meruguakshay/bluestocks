from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Check fields in first item
    first = data[0]
    assert "id" in first
    assert "company_name" in first
    assert "broad_sector" in first
    assert "sub_sector" in first
    assert "roe_pct" in first
    assert "roce_pct" in first

def test_get_companies_filter_sector():
    response = client.get("/api/v1/companies?sector=IT")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["broad_sector"].lower() == "it"

def test_get_company_profile():
    # TCS is standard
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert "broad_sector" in data
    assert "latest_ratios" in data
    assert "pros_cons" in data

def test_get_company_profile_not_found():
    response = client.get("/api/v1/companies/NONEXISTENT")
    assert response.status_code == 404

def test_get_company_pl():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "sales" in data[0]

def test_get_company_bs():
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "total_assets" in data[0]

def test_get_company_cashflow():
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "operating_activity" in data[0]

def test_get_company_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "return_on_equity_pct" in data[0]
