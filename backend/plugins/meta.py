from jsonschema import Draft202012Validator

MAX_FIELDS = 16  # questions per plugin
MAX_OPTIONS = 16  # answers per choice question
MAX_ANSWER_LENGTH = 50  # characters in a choice answer
MAX_DESCRIPTION = 200  # characters in a question
MAX_RULES = 16  # rules per plugin
MAX_PATTERN = 512  # characters in a rule pattern
MAX_NAME_LENGTH = 64  # characters in a question key or rule name

NAME = {
    "type": "string",
    "pattern": r"^[a-z][a-z0-9_]*\Z",
    "maxLength": MAX_NAME_LENGTH,
}

ANSWERS = {
    "type": "array",
    "items": {
        "type": "string",
        "pattern": r"^\S([\s\S]*\S)?\Z",
        "maxLength": MAX_ANSWER_LENGTH,
    },
    "minItems": 2,
    "maxItems": MAX_OPTIONS,
    "uniqueItems": True,
}

INT = {"type": "integer"}
NUM = {"type": "number"}
FORMATS = ["date", "date-time", "time", "email", "uri", "hostname", "ipv4", "ipv6", "uuid"]

def _when(kind, then):
    return {"if": {"properties": {"type": {"const": kind}}, "required": ["type"]}, "then": then}

FIELD = {
    "type": "object",
    "properties": {
        "type": {
            "enum": ["boolean", "string", "array", "number", "integer"],
        },
        "description": {
            "type": "string",
            "maxLength": MAX_DESCRIPTION,
        },
        "nullable": {"type": "boolean"},
    },
    "required": ["type"],
    "allOf": [
        _when("boolean", {"properties": {"enum": {"enum": [[True, False], [False, True]]}}}),
        _when("string", {"properties": {"enum": ANSWERS, "format": {"enum": FORMATS}}, "not": {"required": ["enum", "format"]}}),
        _when("array", {"properties": {"items": {"type": "object", "properties": {"type": {"const": "string"}, "enum": ANSWERS}, "required": ["enum"], "additionalProperties": False}}, "required": ["items"]}),
        _when("number", {"properties": {"minimum": NUM, "maximum": NUM}, "dependentRequired": {"minimum": ["maximum"], "maximum": ["minimum"]}}),
        _when("integer", {"properties": {"minimum": INT, "maximum": INT}, "required": ["minimum"]}),
    ],
    "unevaluatedProperties": False,
}

SCHEMA = Draft202012Validator({
    "type": "object",
    "properties": {
        "type": {"const": "object"},
        "properties": {
            "type": "object",
            "minProperties": 1,
            "maxProperties": MAX_FIELDS,
            "propertyNames": {**NAME, "not": {"const": "rules"}},
            "additionalProperties": FIELD,
        },
    },
    "required": ["properties"],
    "additionalProperties": False,
})
RULES = Draft202012Validator({
    "type": "object",
    "maxProperties": MAX_RULES,
    "propertyNames": NAME,
    "additionalProperties": {
        "type": "string",
        "minLength": 1,
        "maxLength": MAX_PATTERN,
    },
})

for meta in (SCHEMA, RULES): Draft202012Validator.check_schema(meta.schema)
