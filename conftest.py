import pytest_asyncio

from app.repository.mongo.database import mongo_client, default_database


@pytest_asyncio.fixture(autouse=True)
async def before_all():
    await mongo_client.drop_database(default_database)
