from jsonschema.exceptions import ValidationError, SchemaError
from jsonschema.validators import validate

from app.domain.domain import DomainSchema, Domain
from app.repository import base_repository
from app.service import schema_service
from app.service.exceptions import RecordNotFoundException, ValidationException


def _validate_domain_schema(schema: DomainSchema, domain: Domain):
    try:
        validate(instance=domain.dict().get('data'), schema=schema.domain_schema.dict(exclude_none=True))
    except ValidationError as verr:
        raise ValidationException(f"Domain has a invalid schema: {schema.name}", details=verr.message)
    except SchemaError as err:
        raise ValidationException(f"Invalid schema: {schema.name}", details=err.message)


async def create_domain(domain: Domain) -> Domain:
    schema = await schema_service.get_schema_by_name(domain.schema_name)
    _validate_domain_schema(schema, domain)
    ret = await base_repository.create(domain)
    return ret


async def get_domain_by_id(schema_name: str, domain_id: str):
    key = Domain(schema_name=schema_name, domain_id=domain_id)
    ret = await base_repository.find_by_key(key, Domain)
    if not ret:
        raise RecordNotFoundException(f'Domain not found: {schema_name}/{domain_id}',
                                      details=key.dict(include={'schema_name', 'domain_id'}))
    return ret[0]


async def _validate_domain(schema_name, domain_id):
    await get_domain_by_id(schema_name, domain_id)


async def delete_domain(domain: Domain):
    ret = await base_repository.delete_by_key(domain, return_as=Domain)
    if not ret:
        raise RecordNotFoundException(f'Domain not found: {domain.schema_name}/{domain.domain_id}',
                                      details=domain.dict(include={'schema_name', 'domain_id'}))
    return ret
