"""ContextValidator service performing structural, policy, and budget validation checks."""

from max.context.domain.package import ContextPackage
from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.exceptions import ContextBudgetExceededError, InvalidContextError


class ContextValidator:
    """Validates ContextRequest input structure and assembled ContextPackage integrity."""

    def validate_request(self, request: ContextRequest) -> None:
        """Validate ContextRequest payload before context gathering."""
        if not request.user_request or not request.user_request.strip():
            raise InvalidContextError(
                "ContextRequest user_request cannot be empty or whitespace-only.",
                details={"request_id": request.request_id},
            )

    def validate_package(self, package: ContextPackage, policy: ContextPolicy) -> None:
        """Validate assembled ContextPackage integrity, budget limits, and policy requirements."""
        if not package.messages:
            raise InvalidContextError(
                "Assembled ContextPackage must contain at least one AIMessage.",
                details={"request_id": package.request_id},
            )

        # Check total estimated tokens against budget
        max_budget = package.budget.available_input_tokens
        if package.token_estimate > max_budget:
            raise ContextBudgetExceededError(
                f"Assembled context package token estimate ({package.token_estimate}) "
                f"exceeds max available budget ({max_budget}).",
                details={
                    "request_id": package.request_id,
                    "token_estimate": package.token_estimate,
                    "available_budget": max_budget,
                },
            )

        # Check required categories per policy
        included_categories = {item.category for item in package.items}
        missing_required = policy.required_categories - included_categories
        if missing_required:
            missing_names = [cat.value for cat in missing_required]
            raise InvalidContextError(
                f"ContextPackage is missing mandatory required category items: {missing_names}.",
                details={
                    "request_id": package.request_id,
                    "missing_categories": missing_names,
                    "included_categories": [cat.value for cat in included_categories],
                },
            )

        # Ensure message content non-empty
        for idx, msg in enumerate(package.messages):
            if not msg.content or not msg.content.strip():
                raise InvalidContextError(
                    f"Message at index {idx} has empty or invalid content.",
                    details={"request_id": package.request_id, "message_index": idx},
                )
