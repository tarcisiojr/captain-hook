from starlette.testclient import TestClient

from api import app

client = TestClient(app)


def test_crud_create_hook():
    payload = {
        "name": "delivery",
        "domain_schema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string"
                },
                "carrier": {
                    "type": "string"
                }
            }
        }
    }
    ret = client.post('/api/v1/schemas', json=payload)
    assert ret.status_code == 201

    payload = {
        "type": "queue",
        "schema_name": "delivery",
        "event_name": "delivery_change",
        "queue_name": "all_deliveries",
        "tags": [
            "tenant-x"
        ]
    }

    ret = client.post('/api/v1/hooks', json=payload)
    assert ret.status_code == 201
    ret_json = ret.json()
    assert ret_json.get('type') == 'queue'
    assert ret_json.get('schema_name') == 'delivery'
    assert ret_json.get('event_name') == 'delivery_change'
    assert ret_json.get('queue_name') == 'all_deliveries'
    hook_id = ret_json.get('id')

    ret = client.get(f'/api/v1/hooks?type={payload.get("type")}')
    assert ret.status_code == 200
    ret_json_get = ret.json()
    assert len(ret_json_get) == 1
    assert ret_json == ret_json_get[0]

    ret = client.delete(f'/api/v1/hooks/{hook_id}')
    assert ret.status_code == 202
    ret_json_del = ret.json()
    assert ret_json == ret_json_del

    ret = client.get(f'/api/v1/hooks?type={payload.get("type")}')
    assert ret.status_code == 200
    ret_json_get = ret.json()
    assert len(ret_json_get) == 0


def test_invalid_payload():
    payload = {
        "abc": "price",
        "xxx": {}
    }

    ret = client.post('/api/v1/hooks', json=payload)
    assert ret.status_code == 422
