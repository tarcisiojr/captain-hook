from typing import List

from app.domain.hook import Hook
from app.repository.mongo import database
from app.repository.mongo.database import default_database


def _get_collection():
    return default_database[Hook.Meta.collection_name]


async def find_eligible_hooks(schema_name: str, event_name: str, tags: List[str]) -> List[Hook]:
    tags_filter = {}

    if tags:
        tags_filter = {"tags": {"$all": tags}}

    cursor = _get_collection().find(
        {
            "schema_name": schema_name,
            "event_name": event_name,
            **tags_filter
        },
    )
    return [database.from_mongo(Hook, row) async for row in cursor]