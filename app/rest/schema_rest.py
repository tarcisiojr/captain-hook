from typing import List

from fastapi import APIRouter, Depends
from starlette import status

from app.domain.domain import DomainSchema
from app.rest import utils
from app.rest.schemas import DomainSchemaRequest, FindDomainSchemaRequest, KeyDomainSchemaRequest
from app.service import base_service

router = APIRouter(
    tags=['Hook'],
)

URL_BASE = '/api/v1/schemas'


@router.post(
    URL_BASE,
    response_model=DomainSchema,
    status_code=status.HTTP_201_CREATED
)
async def post_schema(domain_schema: DomainSchemaRequest):
    return await base_service.create_entity(DomainSchema(**domain_schema.dict()))


@router.get(
    URL_BASE,
    response_model=List[DomainSchema],
    status_code=status.HTTP_200_OK
)
async def get_schemas(params: FindDomainSchemaRequest = Depends()):
    domain, pagination = utils.get_find_args(params)
    return await base_service.find_entity(example=DomainSchema(**domain), **pagination)


@router.delete(
    f"{URL_BASE}/{{name}}",
    response_model=DomainSchema,
    status_code=status.HTTP_202_ACCEPTED
)
async def delete_schema(name: str):
    return await base_service.delete_entity_by_key(DomainSchema(name=name))
