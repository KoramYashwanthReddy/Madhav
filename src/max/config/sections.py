"""Configuration section models for MAX configuration system."""

from typing import Any
from pydantic import BaseModel, Field, SecretStr

from max.common.types import LogLevel
from max.config.enums import Environment
from max.version import APP_NAME, SERVICE_NAME, VERSION


class ApplicationSettings(BaseModel):
    """Application metadata and runtime mode configuration."""

    name: str = Field(default=APP_NAME, description="Application display name")
    service: str = Field(default=SERVICE_NAME, description="Canonical service name")
    version: str = Field(default=VERSION, description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Execution environment mode"
    )
    debug: bool = Field(default=False, description="Enable debug mode")


class ServerSettings(BaseModel):
    """HTTP server and network listener configuration."""

    host: str = Field(default="127.0.0.1", description="Server listening host IP")
    port: int = Field(default=8000, description="Server listening port")
    reload: bool = Field(default=False, description="Enable auto-reload for local development")
    workers: int = Field(default=1, description="Number of worker processes")


class APISettings(BaseModel):
    """API routing and documentation configuration."""

    prefix: str = Field(default="/api", description="Base API route prefix")
    version: str = Field(default="v1", description="Default API version string")
    docs_enabled: bool = Field(
        default=True, description="Enable interactive OpenAPI documentation (/docs, /redoc)"
    )
    openapi_enabled: bool = Field(
        default=True, description="Enable OpenAPI schema JSON endpoint (/openapi.json)"
    )


class LoggingSettings(BaseModel):
    """Structured logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Log output minimum severity level")
    json_format: bool = Field(default=True, description="Use structured JSON log formatting")
    console: bool = Field(default=True, description="Output log records to stdout")
    include_request_id: bool = Field(
        default=True, description="Include correlation request_id in log records"
    )


class SecuritySettings(BaseModel):
    """Security foundation parameters."""

    secret_key: SecretStr = Field(
        default=SecretStr("insecure-development-secret-key-change-in-production"),
        description="Core platform secret key for security operations",
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["127.0.0.1", "localhost"],
        description="Allowed HTTP Host header values",
    )
    trusted_origins: list[str] = Field(
        default_factory=list, description="Trusted proxy/network origins"
    )
    secure_cookies: bool = Field(default=False, description="Enforce secure flag on cookies")
    require_https: bool = Field(default=False, description="Enforce HTTPS redirect boundary")
    security_headers_enabled: bool = Field(
        default=True, description="Enable standard HTTP security headers"
    )


class CORSSettings(BaseModel):
    """Cross-Origin Resource Sharing (CORS) middleware configuration."""

    enabled: bool = Field(default=True, description="Enable CORS middleware")
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        description="Allowed CORS origin URLs",
    )
    allowed_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="Allowed HTTP methods for CORS requests",
    )
    allowed_headers: list[str] = Field(
        default_factory=lambda: ["*"], description="Allowed HTTP request headers for CORS"
    )
    allow_credentials: bool = Field(
        default=True, description="Allow credentials (cookies, authorization headers)"
    )


class FeatureFlags(BaseModel):
    """Typed internal feature flag toggles."""

    api_docs: bool = Field(default=True, description="Toggle interactive API docs endpoints")
    debug_endpoints: bool = Field(default=False, description="Toggle internal diagnostic endpoints")
    experimental_features: bool = Field(default=False, description="Toggle experimental features")


class IdentitySettings(BaseModel):
    """Identity subsystem default configuration settings."""

    assistant_name: str = Field(default="Max", description="Default assistant identity name")
    default_timezone: str = Field(default="UTC", description="Default fallback timezone")
    default_locale: str = Field(default="en_US", description="Default fallback locale")


class AIRuntimeSettings(BaseModel):
    """AI Runtime subsystem configuration settings."""

    provider: str = Field(default="stub", description="Active default AI runtime provider")
    timeout_seconds: float = Field(
        default=60.0, description="Default inference request timeout in seconds"
    )
    default_temperature: float = Field(default=0.7, description="Default generation temperature")
    default_max_tokens: int = Field(
        default=1024, description="Default maximum response token limit"
    )


class ModelManagementSettings(BaseModel):
    """Model Management subsystem configuration settings."""

    model_directory: str = Field(
        default="./models", description="Configured local filesystem model root directory"
    )
    default_model: str = Field(default="development-stub", description="Default model identifier")
    auto_discovery: bool = Field(
        default=False, description="Toggle local filesystem automatic model discovery on startup"
    )
    verify_checksum: bool = Field(
        default=False, description="Toggle strict checksum verification on artifact loading"
    )


class ContextManagementSettings(BaseModel):
    """Context Management subsystem configuration settings."""

    default_max_tokens: int = Field(
        default=4096, description="Default fallback model context length capacity in tokens"
    )
    reserved_output_tokens: int = Field(
        default=1024, description="Default reserved tokens reserved for model output generation"
    )
    safety_margin_tokens: int = Field(
        default=256, description="Default safety margin buffer tokens to prevent token overflow"
    )
    max_items: int = Field(
        default=100, description="Maximum total candidate context items allowed per request"
    )
    max_item_tokens: int = Field(
        default=2048, description="Maximum tokens allowed for a single context item"
    )
    debug_enabled: bool = Field(
        default=False, description="Toggle context debug inspection and detailed reporting"
    )


class ConversationSettings(BaseModel):
    """Conversation Engine subsystem configuration settings."""

    max_message_characters: int = Field(
        default=16384, description="Maximum characters allowed in a single message"
    )
    max_title_characters: int = Field(
        default=100, description="Maximum characters allowed for a conversation title"
    )
    default_page_size: int = Field(
        default=50, description="Default page size for conversation and message pagination"
    )
    max_page_size: int = Field(
        default=200, description="Maximum page size allowed for pagination requests"
    )
    auto_title_enabled: bool = Field(
        default=True, description="Toggle automatic title generation on first conversation turn"
    )
    history_retrieval_limit: int = Field(
        default=100, description="Maximum recent messages retrieved for ContextSource adapter"
    )


class MemorySettings(BaseModel):
    """Memory Engine subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle Memory Engine active state")
    max_content_length: int = Field(
        default=8192, description="Maximum characters allowed in a single memory text payload"
    )
    max_metadata_size: int = Field(default=4096, description="Maximum serialized metadata length")
    default_importance: str = Field(
        default="NORMAL",
        description="Default memory importance level ('LOW', 'NORMAL', 'HIGH', 'CRITICAL')",
    )
    default_confidence: str = Field(
        default="MEDIUM", description="Default memory confidence level ('LOW', 'MEDIUM', 'HIGH')"
    )
    duplicate_detection_enabled: bool = Field(
        default=True, description="Toggle automatic duplicate memory detection on creation"
    )
    access_tracking_enabled: bool = Field(
        default=True, description="Toggle tracking last_accessed_at timestamp on retrieval"
    )
    default_page_size: int = Field(
        default=50, description="Default page size for memory list and search pagination"
    )
    max_page_size: int = Field(
        default=200, description="Maximum page size allowed for memory pagination requests"
    )


class KnowledgeSettings(BaseModel):
    """Personal Knowledge subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle Personal Knowledge Engine active state")
    max_entity_name_length: int = Field(
        default=255, description="Maximum character length for a knowledge entity name"
    )
    max_description_length: int = Field(
        default=4096, description="Maximum character length for entity/collection description"
    )
    max_fact_value_size: int = Field(
        default=8192, description="Maximum character size for a fact value"
    )
    max_metadata_size: int = Field(default=4096, description="Maximum serialized metadata length")
    duplicate_detection_enabled: bool = Field(
        default=True, description="Toggle automatic duplicate entity/fact detection on creation"
    )
    context_projection_enabled: bool = Field(
        default=True, description="Toggle projection of active knowledge items to ContextSource"
    )
    default_page_size: int = Field(
        default=50, description="Default page size for knowledge list and search pagination"
    )
    max_page_size: int = Field(
        default=200, description="Maximum page size allowed for knowledge pagination requests"
    )


class RAGSettings(BaseModel):
    """RAG & Retrieval subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle RAG & Retrieval subsystem active state")
    chunk_size: int = Field(default=512, description="Target character count for document chunking")
    chunk_overlap: int = Field(
        default=64, description="Overlapping character count between consecutive chunks"
    )
    minimum_chunk_size: int = Field(
        default=32, description="Minimum character size boundary for generated chunks"
    )
    maximum_chunk_size: int = Field(
        default=2048, description="Maximum character size boundary for generated chunks"
    )
    default_top_k: int = Field(
        default=5, description="Default number of top vector similarity results to retrieve"
    )
    max_top_k: int = Field(
        default=50, description="Maximum top_k limit allowed for retrieval requests"
    )
    minimum_score: float = Field(
        default=0.0, description="Default minimum similarity threshold (0.0 to 1.0)"
    )
    embedding_provider: str = Field(
        default="development", description="Embedding provider type ('development')"
    )
    embedding_model: str = Field(
        default="dev-hash-embed-v1", description="Embedding model identifier"
    )
    embedding_dimensions: int = Field(default=64, description="Vector embedding dimension size")
    vector_store_provider: str = Field(
        default="memory", description="Vector store backend provider type ('memory')"
    )


class ReasoningSettings(BaseModel):
    """Reasoning & Planning subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle Reasoning subsystem active state")
    max_plan_steps: int = Field(
        default=50, description="Maximum number of steps allowed in a single plan"
    )
    max_dependencies: int = Field(
        default=100, description="Maximum number of dependencies allowed per plan"
    )
    max_assumptions: int = Field(
        default=20, description="Maximum number of assumptions per reasoning request"
    )
    max_risks: int = Field(default=20, description="Maximum number of identified risks per plan")
    max_evidence: int = Field(
        default=50, description="Maximum evidence references attached per result"
    )
    default_mode: str = Field(
        default="PLANNING", description="Default reasoning mode ('PLANNING', 'ANALYSIS', etc.)"
    )
    development_provider: str = Field(
        default="deterministic", description="Development reasoning provider type"
    )
    ai_provider: str = Field(default="runtime", description="AI-backed reasoning provider type")


class TaskSettings(BaseModel):
    """Task Engine subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle Task Engine active state")
    max_page_size: int = Field(
        default=100, description="Maximum page size allowed for task listings"
    )
    max_title_length: int = Field(
        default=255, description="Maximum character length allowed for task titles"
    )
    max_description_length: int = Field(
        default=4096, description="Maximum character length allowed for task descriptions"
    )
    max_dependency_depth: int = Field(
        default=20, description="Maximum nesting depth allowed for task dependency graph traversal"
    )
    max_parent_depth: int = Field(
        default=10, description="Maximum hierarchy depth allowed for parent/child tasks"
    )
    default_priority: str = Field(
        default="NORMAL", description="Default task priority level ('LOW', 'NORMAL', 'HIGH', etc.)"
    )
    max_retries: int = Field(
        default=3, description="Default maximum retry attempts allowed for tasks"
    )


class AgentSettings(BaseModel):
    """Agent Engine subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle Agent Engine active state")
    max_concurrent_runs: int = Field(
        default=10, description="Maximum concurrent active runs allowed"
    )
    default_max_retries: int = Field(
        default=3, description="Default maximum retry limit for agent runs"
    )
    max_delegation_depth: int = Field(
        default=5, description="Maximum allowed nesting depth for agent delegations"
    )
    max_delegations: int = Field(default=10, description="Maximum allowed delegation count per run")
    default_execution_mode: str = Field(
        default="DRY_RUN", description="Default execution mode ('DRY_RUN', 'SYNCHRONOUS', etc.)"
    )
    max_page_size: int = Field(default=100, description="Maximum page size for agent listings")


class ToolRegistrySettings(BaseModel):
    """Tool Registry subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle Tool Registry active state")
    default_timeout: float = Field(
        default=30.0, description="Default timeout in seconds for tool invocations"
    )
    max_input_size: int = Field(
        default=1048576, description="Maximum byte size allowed for tool input argument payload"
    )
    max_output_size: int = Field(
        default=5242880, description="Maximum byte size allowed for tool output payload"
    )
    allow_development_tools: bool = Field(
        default=True, description="Allow safe in-memory development tools"
    )
    max_page_size: int = Field(default=100, description="Maximum page size for tool listings")


class SecurityModuleSettings(BaseModel):
    """Permission & Security subsystem configuration settings."""

    enabled: bool = Field(
        default=True, description="Toggle Security & Permission Engine active state"
    )
    default_deny: bool = Field(
        default=True, description="Enforce strict default-deny policy posture"
    )
    default_mode: str = Field(
        default="NORMAL",
        description="Default security mode ('NORMAL', 'RESTRICTED', 'LOCKDOWN', 'MAINTENANCE')",
    )
    approval_timeout: float = Field(
        default=3600.0, description="Default timeout in seconds for pending approval requests"
    )
    max_grant_duration: float = Field(
        default=86400.0, description="Maximum duration in seconds for permission grants"
    )
    emergency_block: bool = Field(
        default=False, description="Emergency global kill-switch block state"
    )
    allow_development_approvals: bool = Field(
        default=False, description="Allow automatic development approvals for tests"
    )
    max_page_size: int = Field(default=100, description="Maximum page size for security listings")


class ComputerControlSettings(BaseModel):
    """Computer Control subsystem configuration settings."""

    enabled: bool = Field(default=False, description="Toggle physical computer control active state (defaults to false for safety)")
    dry_run: bool = Field(default=True, description="Enable dry-run simulation mode by default")
    default_timeout: float = Field(default=30.0, description="Default timeout in seconds for computer control actions")
    max_sequence_length: int = Field(default=20, description="Maximum number of actions allowed in a single sequence")
    max_click_count: int = Field(default=10, description="Maximum click count per mouse click action")
    max_typed_text_length: int = Field(default=1000, description="Maximum character length per text typing action")
    screen_capture_enabled: bool = Field(default=True, description="Enable screen capture observation")
    screen_retention_seconds: float = Field(default=60.0, description="Screen capture in-memory retention duration")
    max_page_size: int = Field(default=100, description="Maximum page size for computer control listings")


class FilesystemSettings(BaseModel):
    """Filesystem Agent subsystem configuration settings."""

    enabled: bool = Field(default=True, description="Toggle filesystem agent active state")
    dry_run: bool = Field(default=False, description="Enable dry-run simulation mode")
    allowed_roots: list[Any] = Field(default_factory=list, description="Configured allowed directory sandbox root paths")
    read_only_roots: list[Any] = Field(default_factory=list, description="Configured read-only directory root paths")
    blocked_roots: list[Any] = Field(default_factory=list, description="Explicitly blocked directory root paths")
    max_read_bytes: int = Field(default=10485760, description="Maximum allowed file read size in bytes (default: 10MB)")
    max_write_bytes: int = Field(default=10485760, description="Maximum allowed file write size in bytes (default: 10MB)")
    max_search_results: int = Field(default=1000, description="Maximum search results limit")
    max_search_depth: int = Field(default=20, description="Maximum directory traversal depth for file search")
    operation_timeout: float = Field(default=30.0, description="Default operation timeout in seconds")
    sensitive_path_protection: bool = Field(default=True, description="Enable protected sensitive path security policies")
    max_page_size: int = Field(default=100, description="Maximum page size for directory listings")


class TerminalSettings(BaseModel):
    """Terminal Agent subsystem configuration settings (Module 18)."""

    enabled: bool = Field(
        default=True, description="Toggle Terminal Agent active state"
    )
    dry_run: bool = Field(
        default=False, description="Enable dry-run simulation mode (no real subprocess execution)"
    )
    default_shell: str = Field(
        default="POWERSHELL",
        description="Default shell backend ('POWERSHELL', 'CMD', 'WSL', 'MOCK')",
    )
    default_timeout: float = Field(
        default=30.0, ge=1.0, le=300.0,
        description="Default command execution timeout in seconds",
    )
    max_output_bytes: int = Field(
        default=524288,
        description="Maximum captured stdout/stderr bytes per command (default: 512 KiB)",
    )
    allowed_working_directories: list[Any] = Field(
        default_factory=list,
        description="Allowed working directories for command execution (empty = unrestricted)",
    )
    max_page_size: int = Field(
        default=100, description="Maximum page size for terminal history listings"
    )
    wsl_distribution: str | None = Field(
        default=None, description="WSL distribution name for WSL backend (None = default distro)"
    )


class ApplicationControlSettings(BaseModel):
    """Application Control subsystem configuration settings (Module 19)."""

    enabled: bool = Field(
        default=True, description="Toggle Application Control active state"
    )
    dry_run: bool = Field(
        default=False, description="Enable dry-run simulation mode by default"
    )
    default_launch_timeout: float = Field(
        default=30.0, ge=1.0, le=300.0,
        description="Default timeout in seconds for launching applications"
    )
    max_instances_per_app: int = Field(
        default=10, ge=1, le=100,
        description="Maximum concurrent instances allowed per application"
    )
    allow_system_apps: bool = Field(
        default=True, description="Allow interaction with system/OS applications"
    )
    blocked_executables: list[str] = Field(
        default_factory=list, description="List of executable names explicitly blocked from launching"
    )
    allowed_executables: list[str] = Field(
        default_factory=list, description="List of allowed executables (empty = all except blocked)"
    )
    max_page_size: int = Field(
        default=100, description="Maximum page size for application listings"
    )


class BrowserSettings(BaseModel):
    """Browser Agent subsystem configuration settings (Module 20)."""

    enabled: bool = Field(
        default=True, description="Toggle Browser Agent active state"
    )
    default_browser: str = Field(
        default="chromium", description="Default browser engine ('chromium', 'firefox', 'webkit', 'mock')"
    )
    headless: bool = Field(
        default=True, description="Run browser in headless mode"
    )
    navigation_timeout: float = Field(
        default=30.0, ge=1.0, le=300.0, description="Default navigation timeout in seconds"
    )
    action_timeout: float = Field(
        default=15.0, ge=1.0, le=180.0, description="Default action (click, type, etc.) timeout in seconds"
    )
    download_timeout: float = Field(
        default=60.0, ge=1.0, le=600.0, description="Default file download timeout in seconds"
    )
    upload_timeout: float = Field(
        default=60.0, ge=1.0, le=600.0, description="Default file upload timeout in seconds"
    )
    session_timeout: float = Field(
        default=3600.0, ge=60.0, le=86400.0, description="Session idle expiration timeout in seconds"
    )
    max_sessions: int = Field(
        default=10, ge=1, le=50, description="Maximum concurrent active browser sessions"
    )
    max_tabs_per_session: int = Field(
        default=10, ge=1, le=50, description="Maximum open tabs per browser session"
    )
    max_redirects: int = Field(
        default=5, ge=0, le=20, description="Maximum automatic navigation redirects allowed"
    )
    max_observation_bytes: int = Field(
        default=1048576, description="Maximum character/byte length for page observations (1MB default)"
    )
    max_download_bytes: int = Field(
        default=104857600, description="Maximum allowed file download size in bytes (100MB default)"
    )
    max_upload_bytes: int = Field(
        default=52428800, description="Maximum allowed file upload size in bytes (50MB default)"
    )
    allowed_schemes: list[str] = Field(
        default_factory=lambda: ["http", "https"], description="Allowed URL schemes"
    )
    blocked_domains: list[str] = Field(
        default_factory=list, description="Explicitly blocked domain names or wildcard patterns"
    )
    allowed_domains: list[str] = Field(
        default_factory=list, description="Allowed domain names (empty = all except blocked)"
    )
    screenshot_quality: int = Field(
        default=80, ge=1, le=100, description="JPEG screenshot image quality"
    )
    redact_sensitive_inputs: bool = Field(
        default=True, description="Automatically mask passwords and secret field inputs in logs and state"
    )
    max_page_size: int = Field(
        default=100, description="Maximum page size for browser listings"
    )


class WebIntelligenceSettings(BaseModel):
    """Web Intelligence subsystem configuration settings (Module 21)."""

    enabled: bool = Field(
        default=True, description="Toggle Web Intelligence active state"
    )
    default_provider: str = Field(
        default="mock", description="Default search provider identifier ('mock')"
    )
    max_queries: int = Field(
        default=5, ge=1, le=20, description="Maximum search queries per research request"
    )
    max_results_per_query: int = Field(
        default=10, ge=1, le=50, description="Maximum search results returned per query"
    )
    max_sources: int = Field(
        default=15, ge=1, le=50, description="Maximum candidate sources evaluated per research request"
    )
    max_page_acquisitions: int = Field(
        default=10, ge=0, le=30, description="Maximum web pages fetched/acquired per research request"
    )
    max_research_duration_seconds: float = Field(
        default=120.0, ge=5.0, le=600.0, description="Maximum duration timeout for research operations"
    )
    max_content_bytes: int = Field(
        default=1048576, description="Maximum allowed text content size per page in bytes (1MB default)"
    )
    cache_duration_seconds: float = Field(
        default=3600.0, ge=0.0, le=86400.0, description="Cache retention duration in seconds"
    )
    default_freshness_policy: str = Field(
        default="NO_REQUIREMENT", description="Default freshness policy ('NO_REQUIREMENT', 'TODAY', etc.)"
    )
    default_research_depth: str = Field(
        default="STANDARD", description="Default research depth tier ('SHALLOW', 'STANDARD', 'DEEP')"
    )
    allowed_domains: list[str] = Field(
        default_factory=list, description="Global whitelist of allowed domains"
    )
    blocked_domains: list[str] = Field(
        default_factory=list, description="Global blacklist of blocked domains"
    )
    max_page_size: int = Field(
        default=100, description="Maximum page size for web intelligence listings"
    )


class CodingAgentSettings(BaseModel):
    """Coding Agent subsystem configuration settings (Module 22)."""

    enabled: bool = Field(
        default=True, description="Toggle Coding Agent active state"
    )
    max_repository_bytes: int = Field(
        default=524288000, description="Maximum allowed repository size in bytes (500MB default)"
    )
    max_files_per_analysis: int = Field(
        default=1000, ge=1, le=10000, description="Maximum files indexed per repository analysis"
    )
    max_changed_files: int = Field(
        default=50, ge=1, le=500, description="Maximum changed files allowed per changeset"
    )
    max_fix_iterations: int = Field(
        default=3, ge=1, le=10, description="Maximum debugging fix iteration attempts"
    )
    command_timeout_seconds: float = Field(
        default=120.0, ge=1.0, le=600.0, description="Maximum command execution timeout in seconds"
    )
    test_timeout_seconds: float = Field(
        default=300.0, ge=1.0, le=1200.0, description="Maximum test suite execution timeout in seconds"
    )
    build_timeout_seconds: float = Field(
        default=300.0, ge=1.0, le=1200.0, description="Maximum build execution timeout in seconds"
    )
    max_page_size: int = Field(
        default=100, description="Maximum page size for coding listings"
    )


class DeveloperAgentSettings(BaseModel):
    """Developer Agent subsystem configuration settings (Module 23)."""

    enabled: bool = Field(
        default=True, description="Toggle Developer Agent active state"
    )
    default_branch: str = Field(
        default="main", description="Default repository main branch name"
    )
    protected_branches: list[str] = Field(
        default_factory=lambda: ["main", "master", "release"],
        description="Branch names that require elevated approval for dangerous operations",
    )
    require_approval_for_push: bool = Field(
        default=False,
        description="Require PermissionGate approval before every push (vs. only force-push)",
    )
    require_approval_for_merge: bool = Field(
        default=True,
        description="Require PermissionGate approval before merging into a protected branch",
    )
    max_commit_message_length: int = Field(
        default=1000, ge=10, le=10000,
        description="Maximum character length for commit messages",
    )
    max_sessions: int = Field(
        default=20, ge=1, le=200,
        description="Maximum concurrent developer sessions",
    )
    max_workflows_per_session: int = Field(
        default=10, ge=1, le=100,
        description="Maximum workflows allowed per developer session",
    )
    git_command_timeout: float = Field(
        default=60.0, ge=1.0, le=600.0,
        description="Timeout in seconds for Git command execution",
    )
    max_log_entries: int = Field(
        default=100, ge=1, le=5000,
        description="Maximum git log entries returned per request",
    )
    max_page_size: int = Field(
        default=100, description="Maximum page size for developer listings"
    )
