import pytest
from starlette.testclient import TestClient

from api import app
from app.service.exceptions import ValidationException

client = TestClient(app)


def _setup():
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


def _setup_hook(queue_name='price_changed'):
    payload = {
        "type": "queue",
        "schema_name": "price",
        "event_name": "price_changed",
        "queue_name": queue_name,
        "tags": ["tenant-x"]
    }

    ret = client.post('/api/v1/hooks', json=payload)
    assert ret.status_code == 201


def test_crud_create_event():
    _setup()

    payload = {
        "event_name": "price_changed",
        "metadata": {
            "new_price": 99.90
        }
    }

    ret = client.post('/api/v1/schemas/price/domains/1234567890/events', json=payload)
    assert ret.status_code == 201
    ret_json = ret.json()
    assert ret_json == []

    ret = client.get(f'/api/v1/schemas/price/events?event_name={payload.get("event_name")}')
    assert ret.status_code == 200
    ret_json_get = ret.json()
    assert len(ret_json_get) == 0

    # Definindo o hook
    _setup_hook()

    ret = client.post('/api/v1/schemas/price/domains/1234567890/events', json=payload)
    assert ret.status_code == 201
    ret_json = ret.json()
    assert len(ret_json) == 1
    assert ret_json[0].get('event_name') == payload.get('event_name')
    assert ret_json[0].get('hook') is not None
    assert ret_json[0].get('hook').get('queue_name') == 'price_changed'

    ret = client.get(f'/api/v1/schemas/price/events?event_name={payload.get("event_name")}')
    assert ret.status_code == 200
    ret_json_get = ret.json()
    assert len(ret_json_get) == 1
    assert ret_json == ret_json_get

    _setup_hook('new_queue_changed')

    ret = client.post('/api/v1/schemas/price/domains/1234567890/events', json=payload)
    assert ret.status_code == 201
    ret_json = ret.json()
    assert len(ret_json) == 2
    assert all(map(lambda x: x.get('hook').get('queue_name') in ('price_changed', 'new_queue_changed'), ret_json))


def test_invalid_payload():
    payload = {
        "abc": "price",
        "xxx": {}
    }

    ret = client.post('/api/v1/schemas/price/domains/1234567890/events', json=payload)
    assert ret.status_code == 422


def test_queue_consumption():
    _setup()
    _setup_hook()

    payload = {
        "event_name": "price_changed",
        "metadata": {
            "new_price": 99.90
        }
    }

    ret = client.post('/api/v1/schemas/price/domains/1234567890/events', json=payload)
    assert ret.status_code == 201
    ret_json = ret.json()
    assert len(ret_json) == 1
    assert ret_json[0].get('status') == 'created'

    payload = {
        "status": "processed"
    }

    ret = client.patch(f'/api/v1/schemas/price/events/{ret_json[0].get("id")}', json=payload)
    assert ret.status_code == 200
    ret_json = ret.json()
    assert ret_json.get('status') == 'processed'

    ret = client.get(f'/api/v1/schemas/price/events?event_id={ret_json.get("id")}')
    assert ret.status_code == 200
    ret_json = ret.json()
    assert len(ret_json) == 1
    assert ret_json[0].get('status') == 'processed'

    with pytest.raises(ValidationException):
        client.patch(f'/api/v1/schemas/price/events/{ret_json[0].get("id")}', json=payload)
