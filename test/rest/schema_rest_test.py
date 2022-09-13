from starlette.testclient import TestClient

from api import app

client = TestClient(app)


def test_crud_create_schema():
    payload = {
        "name": "price",
        "domain_schema": {
            "type": "object",
            "properties": {
                "price": {
                    "type": "number"
                },
                "name": {
                    "type": "string"
                }
            }
        }
    }

    ret = client.post('/api/v1/schemas', json=payload)
    assert ret.status_code == 201
    ret_json = ret.json()
    assert ret_json.get('name') == 'price'
    assert ret_json.get('domain_schema') is not None
    assert list(map(lambda k: k, ret_json.get('domain_schema').get('properties', []))) == ['price', 'name']

    ret = client.get(f'/api/v1/schemas?name={payload.get("name")}')
    assert ret.status_code == 200
    ret_json_get = ret.json()
    assert len(ret_json_get) == 1
    assert ret_json == ret_json_get[0]

    ret = client.delete(f'/api/v1/schemas/{payload.get("name")}')
    assert ret.status_code == 202
    ret_json_del = ret.json()
    assert ret_json == ret_json_del

    ret = client.get(f'/api/v1/schemas?name={payload.get("name")}')
    assert ret.status_code == 200
    ret_json_get = ret.json()
    assert len(ret_json_get) == 0


def test_invalid_payload():
    payload = {
        "abc": "price",
        "xxx": {
            "type": "object",
            "properties": {
                "price": {
                    "type": "number"
                },
                "name": {
                    "type": "string"
                }
            }
        }
    }

    ret = client.post('/api/v1/schemas', json=payload)
    assert ret.status_code == 422
