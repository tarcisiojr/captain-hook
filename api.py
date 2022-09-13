import logging

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.repository.exceptions import IntegrityException
from app.service.exceptions import RecordNotFoundException, ValidationException

app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    pass


from app.rest.schema_rest import router as schema_router
from app.rest.domain_rest import router as domain_router
from app.rest.hook_config_rest import router as config_router
from app.rest.health_check_rest import router as health_router

app.include_router(health_router)
app.include_router(config_router)
app.include_router(schema_router)
app.include_router(domain_router)


def _exception_handler(_request: Request, _exc: Exception):
    if isinstance(_exc, RecordNotFoundException):
        return JSONResponse(status_code=404, content={"message": str(_exc), "detail": _exc.details})

    if isinstance(_exc, IntegrityException):
        return JSONResponse(status_code=422, content={"message": str(_exc), "detail": None})

    if isinstance(_exc, ValidationException):
        return JSONResponse(status_code=422, content={"message": str(_exc), "detail": _exc.details})

    logger.error(_exc)
    return JSONResponse(status_code=500, content={"message": str(_exc), 'detail': str(_exc)})


app.add_exception_handler(Exception, _exception_handler)
