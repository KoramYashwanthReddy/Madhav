"""Configuration section models for MADHAV configuration system."""

from pydantic import BaseModel, Field, SecretStr

from madhav.common.types import LogLevel
from madhav.config.enums import Environment
from madhav.version import APP_NAME, SERVICE_NAME, VERSION


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

    assistant_name: str = Field(default="Madhav", description="Default assistant identity name")
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
    chunk_size: int = Field(
        default=512, description="Target character count for document chunking"
    )
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
    embedding_dimensions: int = Field(
        default=64, description="Vector embedding dimension size"
    )
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
    max_risks: int = Field(
        default=20, description="Maximum number of identified risks per plan"
    )
    max_evidence: int = Field(
        default=50, description="Maximum evidence references attached per result"
    )
    default_mode: str = Field(
        default="PLANNING", description="Default reasoning mode ('PLANNING', 'ANALYSIS', etc.)"
    )
    development_provider: str = Field(
        default="deterministic", description="Development reasoning provider type"
    )
    ai_provider: str = Field(
        default="runtime", description="AI-backed reasoning provider type"
    )


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





