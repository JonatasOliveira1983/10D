import pytest
from backend.app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_bankroll_status_fields(client):
    # Assuming the bankroll manager is initialized and returns a status
    response = client.get('/api/bankroll/status')
    assert response.status_code == 200
    data = response.get_json()
    # Check that the new fields are present
    assert 'total_pnl' in data, "total_pnl not in response"
    assert 'roi_percentage' in data, "roi_percentage not in response"
    assert 'neural_status' in data, "neural_status not in response"
    # Basic type checks
    assert isinstance(data['total_pnl'], (int, float)), "total_pnl should be numeric"
    assert isinstance(data['roi_percentage'], (int, float)), "roi_percentage should be numeric"
    assert isinstance(data['neural_status'], str), "neural_status should be a string"
