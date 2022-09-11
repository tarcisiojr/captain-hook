from typing import List

from bson import ObjectId

from app.domain.domain import DomainEvent, DomainEventStatus
from app.repository import base_repository
from app.repository.mongo.database import default_database


def _get_collection():
    return default_database[DomainEvent.Meta.collection_name]


async def create_events(list_events: List[DomainEvent]):
    events = [evt.dict() for evt in list_events]
    result = await _get_collection().insert_many(events)
    cursor = _get_collection().find({"_id": {"$in": result.inserted_ids}})
    return [base_repository.from_mongo(DomainEvent, row) async for row in cursor]


async def get_event_and_mark_processing(event_id: str) -> None | DomainEvent:
    ret = await _get_collection().find_one_and_update(
        {'_id': ObjectId(event_id), 'status': DomainEventStatus.CREATED},
        {'$set': {'status': DomainEventStatus.PROCESSING}}
    )
    if ret:
        return base_repository.from_mongo(DomainEvent, ret)
    return None
