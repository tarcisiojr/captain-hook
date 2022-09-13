from app.domain.domain import DomainSchema
from app.repository import base_repository
from app.service.exceptions import RecordNotFoundException


async def get_schema_by_name(schema_name: str) -> DomainSchema:
    schema = await base_repository.find_by_key(DomainSchema(name=schema_name), return_as=DomainSchema)

    if not schema:
        raise RecordNotFoundException(f'O schema fornecido não existe: {schema_name}')

    return schema[0]


async def exists_schema(schema_name: str):
    await get_schema_by_name(schema_name)
    return True
