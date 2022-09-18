import logging

from fastapi import APIRouter
from starlette import status

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=['Health'],
)

URL_BASE = '/api/v1/health'


@router.get(
    URL_BASE,
    response_model=str,
    status_code=status.HTTP_200_OK
)
async def get_health():
    return "ok"


# @router.post(
#     URL_BASE,
#     response_model=dict,
#     status_code=status.HTTP_200_OK
# )
# async def post_health(payload: dict):
#     logger.info(f'Healthcheck POST: {str(payload)}')
#     return payload
