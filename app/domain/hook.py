from enum import Enum
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, Field, HttpUrl


class HookBaseDomain(BaseModel):
    class Config:
        json_encoders = {ObjectId: str}


class OID(str):
    def __new__(cls, s=None):
        if not s:
            s = ObjectId()

        return super().__new__(cls, s)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return ObjectId(str(v))
        except InvalidId as exc:
            raise ValueError(exc)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class HookType(str, Enum):
    WEBHOOK = 'webhook'
    QUEUE = 'queue'


class Hook(HookBaseDomain):
    id: Optional[OID]
    type: Optional[HookType]
    schema_name: Optional[str]
    event_name: Optional[str]
    condition: Optional[str]
    delay_time: Optional[int] = Field(None, description='Tempo em minutos para disparo do hook.')
    callback: Optional[HttpUrl]

    class Meta:
        collection_name: str = "domain_schema"
        key = ('id', )

