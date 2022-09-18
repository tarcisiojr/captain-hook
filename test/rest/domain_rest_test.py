from starlette.testclient import TestClient

from api import app

client = TestClient(app)


def test_crud_create_domain():
    payload = {
        "name": "price",
        "domain_schema": {
            "type": "object",
            "additionalProperties": False,
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

    payload = {
        "domain_id": "1234567890",
        "data": {
            "name": "Eggs",
            "price": 34.99
        },
        "tags": [["tenant-x"]]
    }

    ret = client.post('/api/v1/schemas/price/domains', json=payload)
    assert ret.status_code == 201
    ret_json = ret.json()
    assert ret_json == {**payload, 'schema_name': 'price'}

    ret = client.get(f'/api/v1/schemas/price/domains?domain_id={payload.get("domain_id")}')
    assert ret.status_code == 200
    ret_json_get = ret.json()
    assert len(ret_json_get) == 1
    assert ret_json == ret_json_get[0]

    ret = client.delete(f'/api/v1/schemas/price/domains/{payload.get("domain_id")}')
    assert ret.status_code == 202
    ret_json_del = ret.json()
    assert ret_json == ret_json_del

    ret = client.get(f'/api/v1/schemas/price/domains?domain_id{payload.get("domain_id")}')
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

    ret = client.post('/api/v1/schemas/price/domains', json=payload)
    assert ret.status_code == 422
