"""JSON Schema validation helpers for benchmark files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "benchmark" / "schema"


class SchemaValidationError(ValueError):
    """Raised when a JSON value fails schema validation."""


def load_schema(name: str) -> dict[str, Any]:
    with (SCHEMA_DIR / name).open() as fh:
        return json.load(fh)


def validate_instance(instance: Any, schema_name: str) -> None:
    """Validate *instance* against a benchmark schema.

    Uses the external ``jsonschema`` package when installed; otherwise falls
    back to the draft-07 subset used by this repository's schemas.
    """
    schema = load_schema(schema_name)
    try:
        from jsonschema import Draft7Validator, RefResolver
        from jsonschema.exceptions import ValidationError
    except ModuleNotFoundError:
        _FallbackValidator(schema, schema_name).validate(instance)
        return

    store = {
        "ast.schema.json": load_schema("ast.schema.json"),
        "https://canb.example/schema/ast.schema.json": load_schema(
            "ast.schema.json"
        ),
    }
    resolver = RefResolver(
        base_uri=f"{SCHEMA_DIR.as_uri()}/",
        referrer=schema,
        store=store,
    )
    Draft7Validator.check_schema(schema)
    try:
        Draft7Validator(schema, resolver=resolver).validate(instance)
    except ValidationError as exc:
        raise SchemaValidationError(str(exc)) from exc


class _FallbackValidator:
    def __init__(self, schema: dict[str, Any], schema_name: str) -> None:
        self.schema = schema
        self.schema_name = schema_name
        self._schemas = {schema_name: schema}

    def validate(self, instance: Any) -> None:
        self._validate_schema(self.schema, instance, self.schema, "$")

    def _validate_schema(
        self,
        schema: dict[str, Any],
        instance: Any,
        root: dict[str, Any],
        path: str,
    ) -> None:
        if "$ref" in schema:
            ref_schema, ref_root = self._resolve_ref(schema["$ref"], root)
            self._validate_schema(ref_schema, instance, ref_root, path)
            return

        for sub in schema.get("allOf", []):
            self._validate_schema(sub, instance, root, path)

        if "if" in schema:
            try:
                self._validate_schema(schema["if"], instance, root, path)
            except SchemaValidationError:
                pass
            else:
                if "then" in schema:
                    self._validate_schema(schema["then"], instance, root, path)

        if "oneOf" in schema:
            matches = 0
            last_error: SchemaValidationError | None = None
            for sub in schema["oneOf"]:
                try:
                    self._validate_schema(sub, instance, root, path)
                except SchemaValidationError as exc:
                    last_error = exc
                else:
                    matches += 1
            if matches != 1:
                detail = f": {last_error}" if last_error else ""
                raise SchemaValidationError(
                    f"{path}: expected exactly one matching schema, got {matches}{detail}"
                )

        if "not" in schema:
            try:
                self._validate_schema(schema["not"], instance, root, path)
            except SchemaValidationError:
                pass
            else:
                raise SchemaValidationError(f"{path}: matched forbidden schema")

        if "const" in schema and instance != schema["const"]:
            raise SchemaValidationError(
                f"{path}: expected {schema['const']!r}, got {instance!r}"
            )

        if "enum" in schema and instance not in schema["enum"]:
            raise SchemaValidationError(
                f"{path}: {instance!r} not in {schema['enum']!r}"
            )

        if "type" in schema:
            expected = schema["type"]
            if isinstance(expected, str):
                expected = [expected]
            if not any(self._is_type(instance, typ) for typ in expected):
                raise SchemaValidationError(
                    f"{path}: expected type {expected!r}, got {type(instance).__name__}"
                )

        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < schema["minLength"]:
                raise SchemaValidationError(f"{path}: string too short")
            if "pattern" in schema and not re.fullmatch(
                schema["pattern"], instance
            ):
                raise SchemaValidationError(
                    f"{path}: {instance!r} does not match {schema['pattern']!r}"
                )

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                raise SchemaValidationError(
                    f"{path}: {instance!r} below minimum {schema['minimum']!r}"
                )
            if (
                "exclusiveMinimum" in schema
                and instance <= schema["exclusiveMinimum"]
            ):
                raise SchemaValidationError(
                    f"{path}: {instance!r} not above {schema['exclusiveMinimum']!r}"
                )

        if isinstance(instance, list):
            self._validate_array(schema, instance, root, path)

        if isinstance(instance, dict):
            self._validate_object(schema, instance, root, path)

    def _validate_array(
        self,
        schema: dict[str, Any],
        instance: list[Any],
        root: dict[str, Any],
        path: str,
    ) -> None:
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise SchemaValidationError(f"{path}: too few items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            raise SchemaValidationError(f"{path}: too many items")
        items = schema.get("items")
        if isinstance(items, list):
            for idx, sub in enumerate(items[: len(instance)]):
                self._validate_schema(sub, instance[idx], root, f"{path}/{idx}")
        elif isinstance(items, dict):
            for idx, item in enumerate(instance):
                self._validate_schema(items, item, root, f"{path}/{idx}")

    def _validate_object(
        self,
        schema: dict[str, Any],
        instance: dict[str, Any],
        root: dict[str, Any],
        path: str,
    ) -> None:
        for key in schema.get("required", []):
            if key not in instance:
                raise SchemaValidationError(f"{path}: missing required {key!r}")
        properties = schema.get("properties", {})
        for key, sub in properties.items():
            if key in instance:
                self._validate_schema(sub, instance[key], root, f"{path}/{key}")
        if schema.get("additionalProperties") is False:
            extra = set(instance) - set(properties)
            if extra:
                raise SchemaValidationError(
                    f"{path}: unexpected properties {sorted(extra)!r}"
                )

    def _resolve_ref(
        self,
        ref: str,
        root: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if ref.startswith("#/"):
            return self._resolve_pointer(root, ref[2:].split("/")), root
        if ref == "ast.schema.json":
            schema = self._schemas.get(ref)
            if schema is None:
                schema = load_schema(ref)
                self._schemas[ref] = schema
            return schema, schema
        raise SchemaValidationError(f"unsupported schema ref {ref!r}")

    @staticmethod
    def _resolve_pointer(schema: dict[str, Any], parts: list[str]) -> dict[str, Any]:
        current: Any = schema
        for part in parts:
            current = current[part]
        if not isinstance(current, dict):
            raise SchemaValidationError("schema pointer did not resolve to object")
        return current

    @staticmethod
    def _is_type(instance: Any, typ: str) -> bool:
        if typ == "null":
            return instance is None
        if typ == "object":
            return isinstance(instance, dict)
        if typ == "array":
            return isinstance(instance, list)
        if typ == "string":
            return isinstance(instance, str)
        if typ == "integer":
            return isinstance(instance, int) and not isinstance(instance, bool)
        if typ == "number":
            return (
                isinstance(instance, (int, float))
                and not isinstance(instance, bool)
            )
        if typ == "boolean":
            return isinstance(instance, bool)
        return False
