import re

import regex
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from laya.structured import SchemaError, plan_from_json_schema

KEY = re.compile(r"[a-z][a-z0-9_]*")
MAX_OPTIONS = 64
MAX_RULES = 16
MAX_PATTERN = 512
EMPTY_SCHEMA = {"type": "object", "properties": {}}


def _problem(prop):
    match prop:
        case dict() if not isinstance(prop.get("description", ""), str):
            return "description must be a string"
        case {"enum": [bool(), bool()] as values} if set(values) == {True, False}:  # bool() rejects 1 and 0
            return None
        case {"enum": list(values)}:
            answers = {v.strip() for v in values if isinstance(v, str)}
            if not set(map(type, values)) <= {str}: return "enum values must be strings"
            if not 2 <= len(values) <= MAX_OPTIONS: return f"needs 2 to {MAX_OPTIONS} answers"
            if "" in answers: return "answers must not be blank"
            if len(answers) != len(values): return "answers must be unique"
            return None
        case {"type": "boolean"}:
            return None
        case {"type": "integer", "minimum": int(lo), "maximum": int(hi)} if bool not in {type(lo), type(hi)}:
            return None
        case dict():
            return "must be an enum, a boolean or an integer with minimum and maximum"
        case _:
            return "must be an object"


@deconstructible
class SchemaValidator:
    def __call__(self, value):
        if value == EMPTY_SCHEMA: return
        try:
            plan_from_json_schema(value)
        except SchemaError as err:
            raise ValidationError(str(err), code="invalid_schema") from err
        for key, prop in value["properties"].items():
            if not KEY.fullmatch(key):
                raise ValidationError(f"properties.{key}: key must match ^[a-z][a-z0-9_]*$", code="invalid_schema")
            if key == "rules":
                raise ValidationError("properties.rules: key is reserved for rule matches", code="invalid_schema")
            if problem := _problem(prop):
                raise ValidationError(f"properties.{key}: {problem}", code="invalid_schema")

    def __eq__(self, other):
        return isinstance(other, SchemaValidator)


@deconstructible
class RuleValidator:
    def __call__(self, value):
        if not isinstance(value, dict): raise ValidationError("must be an object of name: pattern", code="invalid_rules")
        if len(value) > MAX_RULES: raise ValidationError(f"at most {MAX_RULES} rules", code="invalid_rules")
        for name, pattern in value.items():
            if not KEY.fullmatch(name):
                raise ValidationError(f"{name}: name must match ^[a-z][a-z0-9_]*$", code="invalid_rules")
            if not isinstance(pattern, str) or not 0 < len(pattern) <= MAX_PATTERN:
                raise ValidationError(f"{name}: pattern must be 1 to {MAX_PATTERN} characters", code="invalid_rules")
            try:
                regex.compile(pattern)
            except regex.error as err:
                raise ValidationError(f"{name}: {err}", code="invalid_rules") from err

    def __eq__(self, other):
        return isinstance(other, RuleValidator)
