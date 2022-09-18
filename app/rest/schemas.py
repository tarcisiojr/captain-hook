from typing import Optional, Dict, List

from fastapi.openapi.models import Schema
from pydantic import BaseModel, Field, HttpUrl

from app.domain.domain import DomainEventStatus
from app.domain.hook import HookBaseDomain, HookType


class Pagination(BaseModel):
    page: int = Field(1, example=1, le=1)
    per_page: int = Field(100, example=100, le=200, ge=1)


class DomainSchemaRequest(HookBaseDomain):
    name: str = Field(..., example='price')
    domain_schema: Schema = Field(..., example={
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "price": {"type": "number"},
            "name": {"type": "string"},
        },
    })


class FindDomainSchemaRequest(Pagination, HookBaseDomain):
    name: Optional[str] = Field(None, example='price')


class KeyDomainSchemaRequest(HookBaseDomain):
    name: str = Field(..., example='price')


class DomainRequest(HookBaseDomain):
    domain_id: str = Field(..., example='1234567890')
    data: dict = Field(..., example={"name": "Eggs", "price": 34.99})
    tags: Optional[List[List[str]]] = Field(..., example=[["tenant-x"]])


class FindDomainRequest(Pagination, HookBaseDomain):
    domain_id: Optional[str] = Field(None, example='1234567890')


class FindEventsRequest(Pagination, HookBaseDomain):
    event_name: Optional[str] = Field(None, example='price_changed')
    queue_name: Optional[str] = Field(None, example='default')


class UpdateEventRequest(HookBaseDomain):
    status: DomainEventStatus = Field(None, example=DomainEventStatus.PROCESSED)


class DomainEventRequest(HookBaseDomain):
    event_name: str = Field(..., example='price_changed')
    metadata: Optional[dict] = Field(..., example={"new_price": 30050})


class WebhookRequest(HookBaseDomain):
    callback_url: HttpUrl = Field(..., example='https://example.com/')
    delay_time: int = Field(0, description='Wait time to trigger http request')
    http_headers: Optional[Dict[str, str]] = Field(..., description='Custom headers for http request')
    timeout: Optional[int] = Field(3, description='Timeout for http request')
    max_retries: Optional[int] = Field(3, description='Max retries in case of http request exception')


class HookConfigRequest(HookBaseDomain):
    type: HookType
    schema_name: str = Field(..., example='price')
    event_name: str = Field(..., example='price_changed')
    condition: Optional[str] = Field(None, example='event.metadata.new_price > 20000')
    webhook: Optional[WebhookRequest]
    queue_name: Optional[str] = Field('default', description='Queue name for manual consumption.')
    tags: Optional[List[str]] = Field(..., example=["tenant-x"])


class FindHookConfigRequest(Pagination, HookBaseDomain):
    type: Optional[HookType]
    schema_name: Optional[str]
    event_name: Optional[str]
