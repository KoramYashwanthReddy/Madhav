"""Enums for Module 22 — Coding Agent."""

from enum import StrEnum


class CodingStatus(StrEnum):
    """Lifecycle state transitions for a Coding Session or Task."""

    CREATED = "CREATED"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    MODIFYING = "MODIFYING"
    VALIDATING = "VALIDATING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class CodingMode(StrEnum):
    """Structured operational modes for Coding Agent execution."""

    CODE_EXPLANATION = "CODE_EXPLANATION"
    CODE_ANALYSIS = "CODE_ANALYSIS"
    BUG_FIX = "BUG_FIX"
    FEATURE_IMPLEMENTATION = "FEATURE_IMPLEMENTATION"
    REFACTOR = "REFACTOR"
    TEST_GENERATION = "TEST_GENERATION"
    TEST_REPAIR = "TEST_REPAIR"
    PERFORMANCE_ANALYSIS = "PERFORMANCE_ANALYSIS"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    CODE_REVIEW = "CODE_REVIEW"
    DOCUMENTATION = "DOCUMENTATION"
    DEPENDENCY_ANALYSIS = "DEPENDENCY_ANALYSIS"
    BUILD_DEBUGGING = "BUILD_DEBUGGING"


class ProjectType(StrEnum):
    """Ecosystem project type classification."""

    PYTHON = "PYTHON"
    JAVA = "JAVA"
    JAVASCRIPT = "JAVASCRIPT"
    TYPESCRIPT = "TYPESCRIPT"
    RUST = "RUST"
    GO = "GO"
    C_CPP = "C_CPP"
    CSHARP = "CSHARP"
    KOTLIN = "KOTLIN"
    PHP = "PHP"
    UNKNOWN = "UNKNOWN"


class IssueSeverity(StrEnum):
    """Severity classification for code issues and security findings."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueCategory(StrEnum):
    """Category classification of code defects."""

    SYNTAX = "SYNTAX"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    CODE_STYLE = "CODE_STYLE"
    BUG_RISK = "BUG_RISK"
    UNTESTED_CODE = "UNTESTED_CODE"
    CONFIGURATION = "CONFIGURATION"
    DEPRECATION = "DEPRECATION"


class ChangeType(StrEnum):
    """Type of file system patch change operation."""

    CREATE_FILE = "CREATE_FILE"
    MODIFY_FILE = "MODIFY_FILE"
    DELETE_FILE = "DELETE_FILE"
    RENAME_FILE = "RENAME_FILE"


class SymbolType(StrEnum):
    """Classification of code symbols."""

    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    VARIABLE = "VARIABLE"
    CONSTANT = "CONSTANT"
    INTERFACE = "INTERFACE"
    ENUM = "ENUM"
    MODULE = "MODULE"
    PACKAGE = "PACKAGE"
    ENDPOINT = "ENDPOINT"
    COMPONENT = "COMPONENT"
    TEST = "TEST"


class FailureCategory(StrEnum):
    """Category of build/test/command execution failures."""

    CODE_ERROR = "CODE_ERROR"
    TEST_FAILURE = "TEST_FAILURE"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    BUILD_ERROR = "BUILD_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"
