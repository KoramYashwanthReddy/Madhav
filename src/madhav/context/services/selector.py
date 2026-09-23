"""ContextSelector service implementing candidate item selection and budgeting."""

import logging
from typing import Any

from madhav.context.domain.budget import ContextBudget
from madhav.context.domain.enums import ContextCategory, TruncationStrategy
from madhav.context.domain.item import ContextItem
from madhav.context.domain.policy import ContextPolicy
from madhav.context.domain.report import ContextSelectionReport
from madhav.context.exceptions import RequiredContextOverflowError
from madhav.context.services.estimator import TokenEstimator
from madhav.context.services.truncator import ContextTruncator

logger = logging.getLogger("madhav.context.selector")


class ContextSelector:
    """Selects, prioritizes, truncates, and budgets candidate ContextItems."""

    def __init__(
        self, estimator: TokenEstimator, truncator: ContextTruncator | None = None
    ) -> None:
        self._estimator = estimator
        self._truncator = truncator or ContextTruncator(estimator)

    def select(
        self,
        candidates: list[ContextItem],
        budget: ContextBudget,
        policy: ContextPolicy,
    ) -> tuple[
        list[ContextItem],
        list[ContextItem],
        list[dict[str, Any]],
        ContextSelectionReport,
    ]:
        """Perform deterministic selection of context items matching budget constraints."""

        included_items: list[ContextItem] = []
        truncated_items: list[ContextItem] = []
        dropped_items: list[dict[str, Any]] = []

        available_tokens = budget.available_input_tokens
        remaining_budget = available_tokens

        # 1. Estimate initial token counts and remove expired items
        valid_candidates: list[ContextItem] = []
        for item in candidates:
            if item.is_expired:
                dropped_items.append(
                    {
                        "context_id": item.context_id,
                        "category": item.category.value,
                        "priority": item.priority.name,
                        "estimated_tokens": item.token_estimate,
                        "dropped_reason": "expired",
                    }
                )
                continue

            item_copy = item.model_copy(deep=True)
            if item_copy.token_estimate <= 0:
                item_copy.token_estimate = self._estimator.estimate(item_copy.content)

            valid_candidates.append(item_copy)

        # 2. Filter allowed categories
        filtered_candidates: list[ContextItem] = []
        for item in valid_candidates:
            if item.category not in policy.allowed_categories:
                dropped_items.append(
                    {
                        "context_id": item.context_id,
                        "category": item.category.value,
                        "priority": item.priority.name,
                        "estimated_tokens": item.token_estimate,
                        "dropped_reason": "category_disallowed",
                    }
                )
            else:
                filtered_candidates.append(item)

        # 3. Deduplicate exact content if enabled
        deduped_candidates: list[ContextItem] = []
        seen_hashes: set[str] = set()
        for item in filtered_candidates:
            if policy.deduplicate:
                chash = item.content_hash
                if chash in seen_hashes:
                    dropped_items.append(
                        {
                            "context_id": item.context_id,
                            "category": item.category.value,
                            "priority": item.priority.name,
                            "estimated_tokens": item.token_estimate,
                            "dropped_reason": "duplicate",
                        }
                    )
                    continue
                seen_hashes.add(chash)
            deduped_candidates.append(item)

        # 4. Enforce max candidate items count limit
        limited_candidates = deduped_candidates[: policy.max_items]
        if len(deduped_candidates) > policy.max_items:
            for item in deduped_candidates[policy.max_items :]:
                dropped_items.append(
                    {
                        "context_id": item.context_id,
                        "category": item.category.value,
                        "priority": item.priority.name,
                        "estimated_tokens": item.token_estimate,
                        "dropped_reason": "max_items_limit_exceeded",
                    }
                )

        # 5. Deterministic sorting: Required first, priority descending, category, context_id
        def sort_key(item: ContextItem) -> tuple[int, int, int, str]:
            # Required: 0 for True (first), 1 for False
            req_rank = 0 if item.required else 1
            # Priority: inverted int value for descending order (CRITICAL=5 -> -5)
            prio_rank = -int(item.priority)
            # Category index in policy.priority_order if matching
            cat_rank = 0
            if item.category in policy.allowed_categories:
                cat_rank = list(ContextCategory).index(item.category)
            return (req_rank, prio_rank, cat_rank, item.context_id)

        sorted_candidates = sorted(limited_candidates, key=sort_key)

        # 6. Budget accumulation and truncation
        total_tokens_used = 0

        for item in sorted_candidates:
            # Enforce max item tokens limit per policy
            if item.token_estimate > policy.max_item_tokens:
                if policy.truncation_strategy != TruncationStrategy.NONE:
                    item = self._truncator.truncate(
                        item, policy.max_item_tokens, strategy=policy.truncation_strategy
                    )
                    truncated_items.append(item)

            if item.token_estimate <= remaining_budget:
                included_items.append(item)
                remaining_budget -= item.token_estimate
                total_tokens_used += item.token_estimate
            else:
                # Item exceeds remaining budget
                if policy.truncation_strategy != TruncationStrategy.NONE and remaining_budget > 20:
                    truncated_candidate = self._truncator.truncate(
                        item, remaining_budget, strategy=policy.truncation_strategy
                    )
                    if (
                        truncated_candidate.token_estimate <= remaining_budget
                        and truncated_candidate.token_estimate > 0
                    ):
                        included_items.append(truncated_candidate)
                        if truncated_candidate not in truncated_items:
                            truncated_items.append(truncated_candidate)
                        remaining_budget -= truncated_candidate.token_estimate
                        total_tokens_used += truncated_candidate.token_estimate
                        continue

                # Could not fit item into budget
                if item.required:
                    msg = (
                        f"Mandatory required context item '{item.context_id}' from source "
                        f"'{item.source}' ({item.token_estimate} tokens) cannot fit within "
                        f"budget ({remaining_budget} tokens available out of {available_tokens})."
                    )
                    raise RequiredContextOverflowError(
                        msg,
                        details={
                            "context_id": item.context_id,
                            "source": item.source,
                            "category": item.category.value,
                            "item_tokens": item.token_estimate,
                            "remaining_budget": remaining_budget,
                            "total_budget": available_tokens,
                        },
                    )

                dropped_items.append(
                    {
                        "context_id": item.context_id,
                        "category": item.category.value,
                        "priority": item.priority.name,
                        "estimated_tokens": item.token_estimate,
                        "dropped_reason": "budget_exceeded",
                    }
                )

        report = ContextSelectionReport(
            included_items=len(included_items),
            truncated_items=len(truncated_items),
            dropped_items=len(dropped_items),
            total_estimated_tokens=total_tokens_used,
            available_budget=available_tokens,
            policy_used=policy.name,
            summary={
                "category_counts": {
                    cat.value: sum(1 for i in included_items if i.category == cat)
                    for cat in ContextCategory
                }
            },
        )

        return included_items, truncated_items, dropped_items, report
