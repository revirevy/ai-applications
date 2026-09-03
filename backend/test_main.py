from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_overview_contract():
    response = client.get('/overview')
    body = response.json()
    assert response.status_code == 200
    assert {'import', 'quality', 'kpis', 'monthly'} <= body.keys()
    assert body['import']['referential'] == 'ATIH MCO 2026'

def test_import_rejects_http():
    response = client.post('/imports', json={'url': 'http://example.com/file.xlsx'})
    assert response.status_code == 400
