"""Minimal, dependency-free JSON Schema validator.

Supports the keyword subset used by the Context Packs schemas: type,
properties/required/additionalProperties, items/minItems/maxItems/uniqueItems,
enum/const, minLength/maxLength/pattern, minimum/maximum, oneOf/anyOf/allOf/not,
$ref (document-local and against an external schema store keyed by $id), and
light format checks. Unknown keywords are ignored for forward compatibility.
"""

from __future__ import annotations

import re

__all__ = ["validate", "build_store", "SchemaError"]


class SchemaError(ValueError):
    pass


_URI_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:[^\s]*$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_HOSTNAME_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$")
_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _deref(ref: str, root: dict, store: dict):
    if ref == "#":
        return root
    if ref.startswith("#/"):
        parts = ref[2:].split("/")
        node = root
        for part in parts:
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or part not in node:
                raise SchemaError(f"unresolvable $ref: {ref}")
            node = node[part]
        return node
    if "#" in ref:
        uri, _, fragment = ref.partition("#")
    else:
        uri, fragment = ref, None
    node = store.get(uri)
    if node is None:
        raise SchemaError(f"external $ref not in schema store: {ref}")
    if fragment:
        parts = fragment.lstrip("/").split("/")
        for part in parts:
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or part not in node:
                raise SchemaError(f"unresolvable $ref: {ref}")
            node = node[part]
    return node


def _is_type(value, type_name: str) -> bool:
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return True


def _check_format(value: str, fmt: str) -> bool:
    if fmt == "date-time":
        return bool(_DATETIME_RE.match(value))
    if fmt == "date":
        return bool(_DATE_RE.match(value))
    if fmt == "uri":
        return bool(_URI_RE.match(value))
    if fmt == "email":
        return bool(_EMAIL_RE.match(value))
    if fmt == "hostname":
        return bool(_HOSTNAME_RE.match(value))
    return True


def _validate(value, schema, root, store, errors, path):
    if schema is True:
        return
    if schema is False:
        errors.append(f"{path}: must not validate against false schema")
        return
    if not isinstance(schema, dict):
        return

    if "not" in schema:
        sub = []
        _validate(value, schema["not"], root, store, sub, path)
        if not sub:
            errors.append(f"{path}: must not validate against 'not' schema")

    if "$ref" in schema:
        try:
            target = _deref(schema["$ref"], root, store)
        except SchemaError as exc:
            errors.append(f"{path}: {exc}")
            return
        _validate(value, target, root, store, errors, path)

    if "allOf" in schema:
        for index, sub in enumerate(schema["allOf"]):
            _validate(value, sub, root, store, errors, f"{path}/allOf[{index}]")

    if "anyOf" in schema:
        sub = []
        for index, s in enumerate(schema["anyOf"]):
            inner = []
            _validate(value, s, root, store, inner, f"{path}/anyOf[{index}]")
            if not inner:
                sub = []
                break
            sub.append(inner)
        if sub:
            errors.append(f"{path}: must match one of anyOf ({len(sub)} failed)")

    if "oneOf" in schema:
        matches = 0
        for index, s in enumerate(schema["oneOf"]):
            inner = []
            _validate(value, s, root, store, inner, f"{path}/oneOf[{index}]")
            if not inner:
                matches += 1
        if matches != 1:
            errors.append(f"{path}: must match exactly one of oneOf (matched {matches})")

    if "type" in schema:
        type_names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(value, t) for t in type_names):
            errors.append(f"{path}: expected type {type_names}, got {type(value).__name__}")

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value not in enum {schema['enum']!r}")

    if isinstance(value, dict):
        if "required" in schema:
            for name in schema["required"]:
                if name not in value:
                    errors.append(f"{path}: missing required property {name!r}")
        props = schema.get("properties", {})
        for name, prop_schema in props.items():
            if name in value:
                _validate(value[name], prop_schema, root, store, errors, f"{path}/{name}")
        additional = schema.get("additionalProperties", True)
        for name in value:
            if name in props:
                continue
            if additional is False:
                errors.append(f"{path}: unexpected property {name!r}")
            elif isinstance(additional, dict):
                _validate(value[name], additional, root, store, errors, f"{path}/{name}")

    if isinstance(value, list):
        if "items" in schema:
            for index, item in enumerate(value):
                _validate(item, schema["items"], root, store, errors, f"{path}/{index}")
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: more than {schema['maxItems']} items")
        if schema.get("uniqueItems") and len(set(_freeze(value))) != len(value):
            errors.append(f"{path}: items must be unique")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']} chars")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: longer than {schema['maxLength']} chars")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")
        if "format" in schema and not _check_format(value, schema["format"]):
            errors.append(f"{path}: invalid {schema['format']} format")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")


def _freeze(value):
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def validate(data, schema, store=None, path="$"):
    """Validate ``data`` against ``schema``. Returns a list of error strings."""
    root = schema
    errors = []
    _validate(data, schema, root, store or {}, errors, path)
    return errors


def build_store(schemas):
    """Build a { $id: schema } store from a list of schema documents."""
    store = {}
    for schema in schemas:
        if isinstance(schema, dict) and "$id" in schema:
            store[schema["$id"]] = schema
    return store
