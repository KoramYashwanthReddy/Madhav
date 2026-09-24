"""Enums for Module 21 — Web Intelligence."""

from enum import StrEnum


class ResearchStatus(StrEnum):
    """Lifecycle status of a research request."""

    CREATED = "CREATED"
    PLANNING = "PLANNING"
    QUERYING = "QUERYING"
    SEARCHING = "SEARCHING"
    COLLECTING = "COLLECTING"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    COMPARING = "COMPARING"
    SYNTHESIZING = "SYNTHESIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class ResearchMode(StrEnum):
    """Mode governing research intensity and operational approach."""

    QUICK_LOOKUP = "QUICK_LOOKUP"
    STANDARD_RESEARCH = "STANDARD_RESEARCH"
    DEEP_RESEARCH = "DEEP_RESEARCH"
    SOURCE_COMPARISON = "SOURCE_COMPARISON"
    FACT_CHECK = "FACT_CHECK"
    DOCUMENTED_RESEARCH = "DOCUMENTED_RESEARCH"


class ResearchDepth(StrEnum):
    """Depth tier for search and source acquisition."""

    SHALLOW = "SHALLOW"
    STANDARD = "STANDARD"
    DEEP = "DEEP"
    EXHAUSTIVE = "EXHAUSTIVE"


class ResearchPriority(StrEnum):
    """Execution priority level."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SourceType(StrEnum):
    """Classification of web source types."""

    OFFICIAL_WEBSITE = "OFFICIAL_WEBSITE"
    GOVERNMENT = "GOVERNMENT"
    ACADEMIC_PAPER = "ACADEMIC_PAPER"
    RESEARCH_ORG = "RESEARCH_ORG"
    DOCUMENTATION = "DOCUMENTATION"
    NEWS_ARTICLE = "NEWS_ARTICLE"
    COMPANY_PUB = "COMPANY_PUB"
    BLOG = "BLOG"
    FORUM = "FORUM"
    COMMUNITY_DISCUSSION = "COMMUNITY_DISCUSSION"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    UNKNOWN = "UNKNOWN"


class SourceFreshness(StrEnum):
    """Evaluation of source publication/update age."""

    VERY_FRESH = "VERY_FRESH"
    FRESH = "FRESH"
    RECENT = "RECENT"
    AGING = "AGING"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class SourceAuthority(StrEnum):
    """Authority tier of a source for a specific claim."""

    PRIMARY_SOURCE = "PRIMARY_SOURCE"
    SECONDARY_SOURCE = "SECONDARY_SOURCE"
    TERTIARY_SOURCE = "TERTIARY_SOURCE"
    UNKNOWN = "UNKNOWN"


class FreshnessPolicy(StrEnum):
    """Required maximum freshness constraint for research."""

    REAL_TIME = "REAL_TIME"
    LAST_HOUR = "LAST_HOUR"
    TODAY = "TODAY"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
    NO_REQUIREMENT = "NO_REQUIREMENT"


class EvidenceType(StrEnum):
    """Type classification of evidence item."""

    DIRECT_FACT = "DIRECT_FACT"
    STATISTICAL_DATA = "STATISTICAL_DATA"
    STATEMENT = "STATEMENT"
    CITATION_REF = "CITATION_REF"
    QUOTE = "QUOTE"
    INFERENCE = "INFERENCE"


class EvidenceConfidence(StrEnum):
    """Qualitative confidence assessment for evidence."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNCERTAIN = "UNCERTAIN"


class ConflictType(StrEnum):
    """Classification of contradictory evidence between sources."""

    DATE_MISMATCH = "DATE_MISMATCH"
    CLAIM_CONTRADICTION = "CLAIM_CONTRADICTION"
    NUMERICAL_DISCREPANCY = "NUMERICAL_DISCREPANCY"
    DEFINITIONAL_DIFFERENCE = "DEFINITIONAL_DIFFERENCE"
    PARTIAL_DISAGREEMENT = "PARTIAL_DISAGREEMENT"


class CitationStyle(StrEnum):
    """Supported citation formatting styles."""

    APA = "APA"
    MLA = "MLA"
    CHICAGO = "CHICAGO"
    IEEE = "IEEE"
    SIMPLE = "SIMPLE"


class ContentTrustLevel(StrEnum):
    """Content trust taxonomy boundaries."""

    UNTRUSTED_WEB_CONTENT = "UNTRUSTED_WEB_CONTENT"
    SYSTEM_INSTRUCTIONS = "SYSTEM_INSTRUCTIONS"
    USER_INSTRUCTIONS = "USER_INSTRUCTIONS"
    APPROVED_TOOL_RESULTS = "APPROVED_TOOL_RESULTS"
