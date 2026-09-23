"""Tool input argument validator enforcing Pydantic / JSON schema constraints."""

from typing import Any

from max.tools.domain.exceptions import ToolArgumentValidationError
from max.tools.domain.tool import ToolInputSchema


class ToolArgumentValidator:
    """Validates tool invocation argument dictionaries against a ToolInputSchema."""

    @staticmethod
    def validate(tool_id: str, arguments: dict[str, Any], schema: ToolInputSchema) -> None:
        """Validate input arguments dictionary against the declared schema."""
        errors: list[str] = []

        field_map = schema.get_field_map()

        # Check required fields
        for req_field in schema.get_required_field_names():
            if req_field not in arguments:
                errors.append(f"Missing required argument '{req_field}'")

        # Check for undeclared fields if additional properties forbidden
        if not schema.allow_additional_properties:
            for arg_key in arguments:
                if arg_key not in field_map:
                    errors.append(f"Unknown argument '{arg_key}' not defined in schema")

        # Check field types and constraints
        for key, val in arguments.items():
            if key not in field_map:
                continue

            field_desc = field_map[key]

            # Type validation (basic primitives)
            expected_type = field_desc.type.lower()
            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Field '{key}' expected string, got {type(val).__name__}")
            elif expected_type in ("integer", "int") and (
                isinstance(val, bool) or not isinstance(val, int)
            ):
                errors.append(f"Field '{key}' expected integer, got {type(val).__name__}")
            elif expected_type in ("number", "float") and not isinstance(val, (int, float)):
                errors.append(f"Field '{key}' expected number, got {type(val).__name__}")
            elif expected_type in ("boolean", "bool") and not isinstance(val, bool):
                errors.append(f"Field '{key}' expected boolean, got {type(val).__name__}")
            elif expected_type == "array" and not isinstance(val, list):
                errors.append(f"Field '{key}' expected array/list, got {type(val).__name__}")
            elif expected_type in ("object", "dict") and not isinstance(val, dict):
                errors.append(f"Field '{key}' expected object/dict, got {type(val).__name__}")

            # String constraints
            if isinstance(val, str):
                if field_desc.min_length is not None and len(val) < field_desc.min_length:
                    errors.append(
                        f"Field '{key}' length {len(val)} < min_length {field_desc.min_length}"
                    )
                if field_desc.max_length is not None and len(val) > field_desc.max_length:
                    errors.append(
                        f"Field '{key}' length {len(val)} > max_length {field_desc.max_length}"
                    )

            # Numeric constraints
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                if field_desc.min_value is not None and val < field_desc.min_value:
                    errors.append(f"Field '{key}' value {val} < min_value {field_desc.min_value}")
                if field_desc.max_value is not None and val > field_desc.max_value:
                    errors.append(f"Field '{key}' value {val} > max_value {field_desc.max_value}")

            # Allowed values / enum
            if field_desc.allowed_values is not None and val not in field_desc.allowed_values:
                allowed_str = ", ".join(repr(a) for a in field_desc.allowed_values)
                errors.append(
                    f"Field '{key}' value {repr(val)} not in allowed values: [{allowed_str}]"
                )

        if errors:
            raise ToolArgumentValidationError(tool_id=tool_id, errors=errors)
