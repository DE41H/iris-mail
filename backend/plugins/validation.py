import re2
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from jsonschema.exceptions import best_match

from plugins.meta import RULES, SCHEMA

EMPTY_SCHEMA = {"type": "object", "properties": {}}
RE2 = re2.Options()
RE2.log_errors = False
MAX_LEVELS = 10  # steps on a scale question (max - min + 1)
MAX_MATCHES = 20  # matches kept per rule per email
MAX_MATCH_LENGTH = 200  # characters kept per match

def _check(validator, value, code):
    errors = list(validator.iter_errors(value))
    if err := best_match([e for e in errors if e.validator != "unevaluatedProperties"] or errors):
        message = err.message if len(err.message) <= 200 else f"must meet {err.validator}: {err.validator_value}"
        raise ValidationError(f"{err.json_path[2:] or 'top level'}: {message}", code=code)


@deconstructible
class SchemaValidator:
    def __call__(self, value):
        if value == EMPTY_SCHEMA: return
        _check(SCHEMA, value, "invalid_schema")
        for key, prop in value["properties"].items():
            if "maximum" not in prop: continue
            if prop["maximum"] < prop["minimum"]:
                raise ValidationError(f"properties.{key}: maximum must be at least minimum", code="invalid_schema")
            if prop["type"] == "integer" and prop["maximum"] - prop["minimum"] + 1 > MAX_LEVELS:
                raise ValidationError(f"properties.{key}: at most {MAX_LEVELS} levels", code="invalid_schema")

    def __eq__(self, other):
        return isinstance(other, SchemaValidator)


@deconstructible
class RuleValidator:
    def __call__(self, value):
        _check(RULES, value, "invalid_rules")
        for name, pattern in value.items():
            try: re2.compile(pattern, RE2)
            except re2.error as err:
                raise ValidationError(f"{name}: {err.args[0].decode()}", code="invalid_rules") from err

    def __eq__(self, other):
        return isinstance(other, RuleValidator)
