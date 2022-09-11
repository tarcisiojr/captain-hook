from typing import List

from fastapi import APIRouter, status, Depends, Path

from app.domain.domain import Domain, DomainEvent
from app.rest import utils
from app.rest.schemas import DomainRequest, DomainEventRequest, FindDomainRequest
from app.service import domain_service, base_service

router = APIRouter(
    tags=['Hook'],
)

URL_BASE = '/api/v1/schemas/{name}/domains'


@router.post(
    f"{URL_BASE}",
    response_model=Domain,
    status_code=status.HTTP_201_CREATED
)
async def post_domain(domain: DomainRequest, name: str = Path(example='price')):
    return await domain_service.create_domain(Domain(**domain.dict(), schema_name=name))


@router.get(
    URL_BASE,
    response_model=List[Domain],
    status_code=status.HTTP_200_OK
)
async def get_domains(name: str, params: FindDomainRequest = Depends()):
    domain, pagination = utils.get_find_args(params)
    return await base_service.find_entity(example=Domain(**domain, schema_name=name), **pagination)


@router.delete(
    f"{URL_BASE}/{{domain_id}}",
    response_model=Domain,
    status_code=status.HTTP_202_ACCEPTED
)
async def delete_domain(name: str, domain_id: str):
    return await domain_service.delete_domain(Domain(schema_name=name, domain_id=domain_id))


@router.post(
    f"{URL_BASE}/{{domain_id}}/events",
    response_model=List[DomainEvent]
)
async def post_domain_event(event: DomainEventRequest,
                            name: str = Path(example='price'),
                            domain_id: str = Path(example='1234567890')):
    return await domain_service.insert_event(DomainEvent(
        **event.dict(),
        schema_name=name,
        domain_id=domain_id))
