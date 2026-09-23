"""ContextPolicy domain model defining rules for context selection and filtering."""

from pydantic import BaseModel, Field

from max.context.domain.enums import ContextCategory, ContextPriority, TruncationStrategy


class ContextPolicy(BaseModel):
    """Declarative policy configuration governing context inclusion, priority, and privacy."""

    name: str = Field(default="default", description="Policy identifier name")
    allowed_categories: set[ContextCategory] = Field(
        default_factory=lambda: set(ContextCategory),
        description="Set of context categories permitted by this policy",
    )
    required_categories: set[ContextCategory] = Field(
        default_factory=lambda: {ContextCategory.REQUEST, ContextCategory.SYSTEM},
        description="Set of context categories mandatory for a valid context package",
    )
    priority_order: list[ContextPriority] = Field(
        default_factory=lambda: [
            ContextPriority.CRITICAL,
            ContextPriority.HIGH,
            ContextPriority.NORMAL,
            ContextPriority.LOW,
            ContextPriority.OPTIONAL,
        ],
        description="Priority level ordering for candidate context item selection",
    )
    truncation_strategy: TruncationStrategy = Field(
        default=TruncationStrategy.TAIL,
        description="Default truncation strategy applied when budget overflow occurs",
    )
    max_items: int = Field(
        default=100,
        description="Maximum total candidate context items processed per request",
        gt=0,
    )
    max_item_tokens: int = Field(
        default=2048,
        description="Maximum token limit allowed for a single context item",
        gt=0,
    )
    deduplicate: bool = Field(
        default=True, description="Toggle content-based exact duplicate item removal"
    )
    allow_sensitive_identity: bool = Field(
        default=False,
        description="Explicit policy opt-in permitting sensitive identity attributes",
    )

    @classmethod
    def default(cls) -> "ContextPolicy":
        """Create standard balanced default context policy."""
        return cls(name="default")

    @classmethod
    def minimal(cls) -> "ContextPolicy":
        """Create strict minimal context policy including only system instructions and request."""
        return cls(
            name="minimal",
            allowed_categories={ContextCategory.SYSTEM, ContextCategory.REQUEST},
            required_categories={ContextCategory.SYSTEM, ContextCategory.REQUEST},
            max_items=10,
            allow_sensitive_identity=False,
        )

    @classmethod
    def full(cls) -> "ContextPolicy":
        """Create permissive full context policy including all categories and optional identity."""
        return cls(
            name="full",
            allowed_categories=set(ContextCategory),
            required_categories={ContextCategory.SYSTEM, ContextCategory.REQUEST},
            max_items=200,
            allow_sensitive_identity=True,
        )
