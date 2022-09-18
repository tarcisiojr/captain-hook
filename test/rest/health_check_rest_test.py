from starlette.testclient import TestClient

from api import app

client = TestClient(app)


def test_health_check():
    ret = client.get('/api/v1/health')
    assert ret.status_code == 200
    ret_json = ret.json()
    assert ret_json == 'ok'
