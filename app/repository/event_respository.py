from typing import List

from bson import ObjectId

from app.domain.domain import DomainEvent, DomainEventStatus
from app.repository.mongo import database
from app.repository.mongo.database import default_database


def _get_collection():
    return default_database[DomainEvent.Meta.collection_name]


async def create_events(list_events: List[DomainEvent]):
    events = [evt.dict() for evt in list_events]
    result = await _get_collection().insert_many(events)
    cursor = _get_collection().find({"_id": {"$in": result.inserted_ids}})
    return [database.from_mongo(DomainEvent, row) async for row in cursor]


async def get_event_and_mark_processing(event_id: str) -> None | DomainEvent:
    ret = await _get_collection().find_one_and_update(
        {'_id': ObjectId(event_id), 'status': DomainEventStatus.CREATED},
        {'$set': {'status': DomainEventStatus.PROCESSING}}
    )
    if ret:
        return database.from_mongo(DomainEvent, ret)
    return None


async def find_pending_events(limit_date) -> List[DomainEvent]:
    cursor = _get_collection().find(
        {
            'status': DomainEventStatus.CREATED,
            'eta': {'$lte': limit_date}
        }
    )
    return [database.from_mongo(DomainEvent, row) async for row in cursor]


async def find_events(schema_name,
                      event_id=None,
                      event_name=None,
                      queue_name=None,
                      skip: int = 0, limit: int = 100):
    limits = {"skip": skip, "limit": limit}
    filters = {'schema_name': schema_name}

    if limit <= 0:
        limits = {}

    if event_id:
        filters['id'] = ObjectId(str(event_id))

    if event_name:
        filters['event_name'] = event_name

    if queue_name:
        filters['hook.queue_name'] = queue_name

    cursor = _get_collection().find(filters, **limits)
    return [database.from_mongo(DomainEvent, row) async for row in cursor]