"""Enumerations for Module 15 — Permission & Security."""

from enum import StrEnum


class PermissionSubjectType(StrEnum):
    """Classification of entities that can request actions."""

    USER = "USER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"
    SERVICE = "SERVICE"
    TOOL = "TOOL"
    UNKNOWN = "UNKNOWN"


class PermissionAction(StrEnum):
    """Explicit action operations evaluated by the permission system."""

    READ = "READ"
    WRITE = "WRITE"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    OPEN = "OPEN"
    CLICK = "CLICK"
    TYPE = "TYPE"
    SEND = "SEND"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    MODIFY = "MODIFY"
    SHARE = "SHARE"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    ADMINISTER = "ADMINISTER"


class ResourceSensitivity(StrEnum):
    """Resource data classification level."""

    PUBLIC = "PUBLIC"
    NORMAL = "NORMAL"
    SENSITIVE = "SENSITIVE"
    HIGHLY_SENSITIVE = "HIGHLY_SENSITIVE"
    CRITICAL = "CRITICAL"


class PermissionScope(StrEnum):
    """Scope boundaries for permission policies and grants."""

    EXACT_RESOURCE = "EXACT_RESOURCE"
    RESOURCE_GROUP = "RESOURCE_GROUP"
    DIRECTORY = "DIRECTORY"
    PROJECT = "PROJECT"
    DOMAIN = "DOMAIN"
    APPLICATION = "APPLICATION"
    TOOL = "TOOL"
    CAPABILITY = "CAPABILITY"
    GLOBAL = "GLOBAL"


class PermissionEffect(StrEnum):
    """Policy rule evaluation outcome."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class RiskLevel(StrEnum):
    """Action risk classification level."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PermissionDecisionStatus(StrEnum):
    """Status of a permission decision."""

    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class DecisionReason(StrEnum):
    """Structured rationale for permission decisions."""

    NO_POLICY_MATCH = "NO_POLICY_MATCH"
    EXPLICIT_ALLOW = "EXPLICIT_ALLOW"
    EXPLICIT_DENY = "EXPLICIT_DENY"
    RISK_TOO_HIGH = "RISK_TOO_HIGH"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    RESOURCE_OUT_OF_SCOPE = "RESOURCE_OUT_OF_SCOPE"
    SUBJECT_NOT_ALLOWED = "SUBJECT_NOT_ALLOWED"
    TOOL_NOT_ALLOWED = "TOOL_NOT_ALLOWED"
    AGENT_NOT_ALLOWED = "AGENT_NOT_ALLOWED"
    OWNER_MISMATCH = "OWNER_MISMATCH"
    SECURITY_MODE_BLOCKED = "SECURITY_MODE_BLOCKED"
    EMERGENCY_BLOCK = "EMERGENCY_BLOCK"
    PERMISSION_EXPIRED = "PERMISSION_EXPIRED"
    INVALID_REQUEST = "INVALID_REQUEST"
    TOOL_DISABLED = "TOOL_DISABLED"
    EVALUATION_ERROR = "EVALUATION_ERROR"


class RequestStatus(StrEnum):
    """Status of a permission check request."""

    PENDING = "PENDING"
    EVALUATED = "EVALUATED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ApprovalStatus(StrEnum):
    """Status of a human approval request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ApprovalType(StrEnum):
    """Classification of approval type."""

    USER_CONFIRMATION = "USER_CONFIRMATION"
    EXPLICIT_USER_GRANT = "EXPLICIT_USER_GRANT"
    ADMIN_APPROVAL = "ADMIN_APPROVAL"


class PermissionGrantType(StrEnum):
    """Duration type for permission grants."""

    ONE_TIME = "ONE_TIME"
    SESSION = "SESSION"
    TIME_LIMITED = "TIME_LIMITED"
    PERSISTENT = "PERSISTENT"


class SecurityMode(StrEnum):
    """System-wide operational security mode."""

    NORMAL = "NORMAL"
    RESTRICTED = "RESTRICTED"
    LOCKDOWN = "LOCKDOWN"
    MAINTENANCE = "MAINTENANCE"


class SecurityEventType(StrEnum):
    """Categorization of audit log security events."""

    PERMISSION_REQUESTED = "PERMISSION_REQUESTED"
    PERMISSION_ALLOWED = "PERMISSION_ALLOWED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_APPROVED = "APPROVAL_APPROVED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    PERMISSION_EXPIRED = "PERMISSION_EXPIRED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    POLICY_CHANGED = "POLICY_CHANGED"
    SECURITY_MODE_CHANGED = "SECURITY_MODE_CHANGED"
    EMERGENCY_BLOCK_ACTIVATED = "EMERGENCY_BLOCK_ACTIVATED"
    EMERGENCY_BLOCK_DEACTIVATED = "EMERGENCY_BLOCK_DEACTIVATED"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"


class SecurityViolationType(StrEnum):
    """Classification of security boundary violations."""

    PERMISSION_BYPASS_ATTEMPT = "PERMISSION_BYPASS_ATTEMPT"
    EXPIRED_PERMISSION_USE = "EXPIRED_PERMISSION_USE"
    INVALID_APPROVAL = "INVALID_APPROVAL"
    UNAUTHORIZED_OWNER_ACCESS = "UNAUTHORIZED_OWNER_ACCESS"
    BLOCKED_ACTION_ATTEMPT = "BLOCKED_ACTION_ATTEMPT"
    MALFORMED_SECURITY_CONTEXT = "MALFORMED_SECURITY_CONTEXT"
    POLICY_CONFLICT = "POLICY_CONFLICT"
    EVALUATION_FAILURE = "EVALUATION_FAILURE"
