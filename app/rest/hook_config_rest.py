from typing import List

from fastapi import APIRouter, Depends
from starlette import status

from app.domain.hook import Hook, OID
from app.rest import utils
from app.rest.schemas import HookConfigRequest, FindHookConfigRequest
from app.service import base_service, hook_service

router = APIRouter(
    tags=['Config'],
)

URL_BASE = '/api/v1/hooks'


@router.post(
    URL_BASE,
    response_model=Hook,
    status_code=status.HTTP_201_CREATED
)
async def post_hook(hook_config: HookConfigRequest):
    return await hook_service.create_hook_config(Hook(**hook_config.dict()))


@router.get(
    URL_BASE,
    response_model=List[Hook],
    status_code=status.HTTP_200_OK
)
async def get_hooks(params: FindHookConfigRequest = Depends()):
    domain, pagination = utils.get_find_args(params)
    return await base_service.find_entity(example=Hook(**domain), **pagination)


@router.delete(
    f"{URL_BASE}/{{hook_id}}",
    response_model=Hook,
    status_code=status.HTTP_202_ACCEPTED
)
async def delete_hook(hook_id: OID):
    return await base_service.delete_entity_by_key(Hook(id=hook_id))
