from datetime import datetime
from enum import Enum
from typing import Optional, List

from fastapi.openapi.models import Schema
from pydantic import Field

from app.domain.hook import HookBaseDomain, OID, Hook


class DomainSchema(HookBaseDomain):
    name: Optional[str]
    domain_schema: Optional[Schema]

    class Meta:
        collection_name: str = "domain_schema"
        key = ('name', )


class Domain(HookBaseDomain):
    domain_id: Optional[str] = Field(None, example='1234567890')
    schema_name: Optional[str] = Field(None, example='price')
    data: Optional[dict] = Field(None, example={"name": "Eggs", "price": 34.99})
    tags: Optional[List[List[str]]] = Field(None, example=[["tenant-x"]])

    class Meta:
        collection_name: str = "domain"
        key = ('schema_name', 'domain_id', )


class DomainEventStatus(str, Enum):
    CREATED = 'created'
    PROCESSING = 'processing'
    PROCESSED = 'processed'
    ERROR = 'error'
    CANCELED = 'canceled'
    FAILED = 'failed'


class DomainEvent(HookBaseDomain):
    id: Optional[OID]
    event_name: Optional[str]
    schema_name: Optional[str]
    domain_id: Optional[str]
    metadata: Optional[dict]
    status: Optional[DomainEventStatus]
    hook: Optional[Hook]
    eta: Optional[datetime]

    class Meta:
        collection_name: str = "domain_event"
        key = ('id', )
