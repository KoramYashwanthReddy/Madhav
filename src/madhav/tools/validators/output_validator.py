"""Tool output result validator enforcing output schema conformity."""

from typing import Any

from madhav.tools.domain.exceptions import ToolOutputValidationError
from madhav.tools.domain.tool import ToolOutputSchema


class ToolOutputValidator:
    """Validates tool invocation output payload dictionaries against a ToolOutputSchema."""

    @staticmethod
    def validate(tool_id: str, output: dict[str, Any], schema: ToolOutputSchema) -> None:
        """Validate result dictionary against declared output schema fields."""
        errors: list[str] = []

        if not isinstance(output, dict):
            raise ToolOutputValidationError(
                tool_id=tool_id, errors=[f"Output must be a dictionary payload, got {type(output).__name__}"]
            )

        field_map = {f.name: f for f in schema.fields}

        # Check required fields
        for field_desc in schema.fields:
            if field_desc.required and field_desc.name not in output:
                errors.append(f"Missing required output field '{field_desc.name}'")

        # Type checks
        for key, val in output.items():
            if key not in field_map:
                continue
            field_desc = field_map[key]
            expected_type = field_desc.type.lower()

            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Output field '{key}' expected string, got {type(val).__name__}")
            elif expected_type in ("integer", "int") and (isinstance(val, bool) or not isinstance(val, int)):
                errors.append(f"Output field '{key}' expected integer, got {type(val).__name__}")
            elif expected_type in ("number", "float") and not isinstance(val, (int, float)):
                errors.append(f"Output field '{key}' expected number, got {type(val).__name__}")
            elif expected_type in ("boolean", "bool") and not isinstance(val, bool):
                errors.append(f"Output field '{key}' expected boolean, got {type(val).__name__}")

        if errors:
            raise ToolOutputValidationError(tool_id=tool_id, errors=errors)
