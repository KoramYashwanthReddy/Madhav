"""ContextTruncator service performing safe, strategy-based text truncation."""

import math

from madhav.context.domain.enums import TruncationStrategy
from madhav.context.domain.item import ContextItem
from madhav.context.services.estimator import TokenEstimator


class ContextTruncator:
    """Performs deterministic text truncation on ContextItem objects to fit target token budgets."""

    def __init__(self, estimator: TokenEstimator) -> None:
        self._estimator = estimator

    def truncate(
        self,
        item: ContextItem,
        target_max_tokens: int,
        strategy: TruncationStrategy = TruncationStrategy.TAIL,
    ) -> ContextItem:
        """Truncate context item text to fit target token budget safely."""
        current_estimate = self._estimator.estimate(item.content)
        if current_estimate <= target_max_tokens or strategy == TruncationStrategy.NONE:
            return item

        content = item.content

        if strategy == TruncationStrategy.TAIL:

            truncated_content = self._truncate_tail(content, target_max_tokens)
        elif strategy == TruncationStrategy.HEAD:
            truncated_content = self._truncate_head(content, target_max_tokens)
        elif strategy == TruncationStrategy.HEAD_AND_TAIL:
            truncated_content = self._truncate_head_and_tail(content, target_max_tokens)
        else:
            truncated_content = content

        new_estimate = self._estimator.estimate(truncated_content)

        # Clone item with truncated content and updated metadata
        updated_item = item.model_copy(deep=True)
        updated_item.content = truncated_content
        updated_item.token_estimate = new_estimate
        updated_item.metadata.update(
            {
                "truncated": True,
                "original_token_estimate": current_estimate,
                "truncated_token_estimate": new_estimate,
                "truncation_strategy": strategy.value,
            }
        )

        return updated_item

    def _truncate_tail(self, text: str, max_tokens: int) -> str:
        """Truncate trailing text preserving the beginning."""
        chars = len(text)
        current_tokens = self._estimator.estimate(text)
        if current_tokens <= max_tokens:
            return text

        ratio = max_tokens / float(current_tokens)
        keep_chars = max(10, math.floor(chars * ratio * 0.9))
        truncated = text[:keep_chars].rstrip() + "\n... [TRUNCATED TAIL]"

        # Iteratively refine if still exceeding
        while self._estimator.estimate(truncated) > max_tokens and keep_chars > 20:
            keep_chars = int(keep_chars * 0.85)
            truncated = text[:keep_chars].rstrip() + "\n... [TRUNCATED TAIL]"

        return truncated

    def _truncate_head(self, text: str, max_tokens: int) -> str:
        """Truncate leading text preserving the ending."""
        chars = len(text)
        current_tokens = self._estimator.estimate(text)
        if current_tokens <= max_tokens:
            return text

        ratio = max_tokens / float(current_tokens)
        keep_chars = max(10, math.floor(chars * ratio * 0.9))
        truncated = "[TRUNCATED HEAD] ...\n" + text[-keep_chars:].lstrip()

        while self._estimator.estimate(truncated) > max_tokens and keep_chars > 20:
            keep_chars = int(keep_chars * 0.85)
            truncated = "[TRUNCATED HEAD] ...\n" + text[-keep_chars:].lstrip()

        return truncated

    def _truncate_head_and_tail(self, text: str, max_tokens: int) -> str:
        """Truncate middle text preserving the beginning and ending."""
        chars = len(text)
        current_tokens = self._estimator.estimate(text)
        if current_tokens <= max_tokens:
            return text

        ratio = max_tokens / float(current_tokens)
        keep_total = max(20, math.floor(chars * ratio * 0.85))
        half = keep_total // 2

        head_part = text[:half].rstrip()
        tail_part = text[-half:].lstrip()
        truncated = f"{head_part}\n... [TRUNCATED MIDDLE] ...\n{tail_part}"

        while self._estimator.estimate(truncated) > max_tokens and half > 15:
            half = int(half * 0.85)
            head_part = text[:half].rstrip()
            tail_part = text[-half:].lstrip()
            truncated = f"{head_part}\n... [TRUNCATED MIDDLE] ...\n{tail_part}"

        return truncated
