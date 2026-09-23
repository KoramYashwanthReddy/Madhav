"""Domain enumerations for Personal Knowledge Engine."""

from enum import StrEnum


class KnowledgeEntityType(StrEnum):
    """Supported categories for real-world and conceptual knowledge entities."""

    PERSON = "person"
    PROJECT = "project"
    ORGANIZATION = "organization"
    COMPANY = "company"
    SKILL = "skill"
    TECHNOLOGY = "technology"
    GOAL = "goal"
    INTEREST = "interest"
    EDUCATION = "education"
    JOB = "job"
    LOCATION = "location"
    DOCUMENT = "document"
    CONCEPT = "concept"
    EVENT = "event"
    OTHER = "other"


class KnowledgeStatus(StrEnum):
    """Lifecycle state of a knowledge entity, fact, relation, or collection."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    DELETED = "deleted"


class KnowledgeConfidence(StrEnum):
    """System confidence rating in stored knowledge item."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class KnowledgeSourceType(StrEnum):
    """Provenances for knowledge items."""

    USER_EXPLICIT = "user_explicit"
    USER_PROFILE = "user_profile"
    CONVERSATION = "conversation"
    MEMORY = "memory"
    IMPORTED = "imported"
    MANUAL = "manual"
    SYSTEM = "system"
    FUTURE_AI_INFERENCE = "future_ai_inference"


class KnowledgeRelationType(StrEnum):
    """Controlled relationship types between knowledge entities."""

    OWNS = "owns"
    USES = "uses"
    WORKS_ON = "works_on"
    WORKS_AT = "works_at"
    LEARNED = "learned"
    LEARNING = "learning"
    INTERESTED_IN = "interested_in"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"
    CREATED = "created"
    MANAGES = "manages"
    KNOWS = "knows"
    LOCATED_AT = "located_at"
    HAS_SKILL = "has_skill"
    HAS_GOAL = "has_goal"
    HAS_EXPERIENCE = "has_experience"


class FactValueType(StrEnum):
    """Supported scalar and structured data types for knowledge facts."""

    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    REFERENCE = "reference"
    JSON = "json"


class KnowledgeScope(StrEnum):
    """Ownership and visibility scope of knowledge elements."""

    USER = "user"
    SYSTEM = "system"
