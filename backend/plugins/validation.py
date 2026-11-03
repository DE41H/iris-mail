from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from laya.structured import SchemaError, plan_from_json_schema


@deconstructible
class SchemaValidator:
    def __call__(self, value):
        try:
            plan_from_json_schema(value)
        except SchemaError as err:
            raise ValidationError(str(err), code="invalid_schema") from err

    def __eq__(self, other):
        return isinstance(other, SchemaValidator)
