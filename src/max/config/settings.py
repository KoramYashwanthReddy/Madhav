"""Root configuration model powered by Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from max.config.sections import (
    AgentSettings,
    AIRuntimeSettings,
    APISettings,
    ApplicationControlSettings,
    ApplicationSettings,
    BrowserSettings,
    ComputerControlSettings,
    ContextManagementSettings,
    ConversationSettings,
    CORSSettings,
    FeatureFlags,
    FilesystemSettings,
    IdentitySettings,
    KnowledgeSettings,
    LoggingSettings,
    MemorySettings,
    ModelManagementSettings,
    RAGSettings,
    ReasoningSettings,
    SecurityModuleSettings,
    SecuritySettings,
    ServerSettings,
    TaskSettings,
    TerminalSettings,
    ToolRegistrySettings,
    WebIntelligenceSettings,
    CodingAgentSettings,
)
from max.config.validators import (
    validate_agent_settings,
    validate_application_control_settings,
    validate_browser_settings,
    validate_computer_control_settings,
    validate_context_settings,
    validate_conversation_settings,
    validate_filesystem_settings,
    validate_knowledge_settings,
    validate_logging_settings,
    validate_memory_settings,
    validate_production_settings,
    validate_rag_settings,
    validate_reasoning_settings,
    validate_security_module_settings,
    validate_server_settings,
    validate_task_settings,
    validate_tool_settings,
    validate_web_intelligence_settings,
    validate_coding_agent_settings,
)


class Settings(BaseSettings):
    """MAX Root Configuration Model.

    Combines application, server, API, logging, security, CORS, identity, AI runtime,
    model management, context management, conversation engine, memory engine,
    personal knowledge engine, RAG engine, reasoning & planning engine, task engine, agent engine, tool registry, permission & security module, computer control, filesystem agent, terminal agent, application control, browser agent, and feature flags.

    Supports environment variables prefixed with `MAX_` and double-underscore nested keys.
    """

    model_config = SettingsConfigDict(
        env_prefix="MAX_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    identity: IdentitySettings = Field(default_factory=IdentitySettings)
    ai_runtime: AIRuntimeSettings = Field(default_factory=AIRuntimeSettings)
    models: ModelManagementSettings = Field(default_factory=ModelManagementSettings)
    context: ContextManagementSettings = Field(default_factory=ContextManagementSettings)
    conversation: ConversationSettings = Field(default_factory=ConversationSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    knowledge: KnowledgeSettings = Field(default_factory=KnowledgeSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    reasoning: ReasoningSettings = Field(default_factory=ReasoningSettings)
    tasks: TaskSettings = Field(default_factory=TaskSettings)
    agents: AgentSettings = Field(default_factory=AgentSettings)
    tools: ToolRegistrySettings = Field(default_factory=ToolRegistrySettings)
    security_module: SecurityModuleSettings = Field(default_factory=SecurityModuleSettings)
    computer_control: ComputerControlSettings = Field(default_factory=ComputerControlSettings)
    filesystem: FilesystemSettings = Field(default_factory=FilesystemSettings)
    terminal: TerminalSettings = Field(default_factory=TerminalSettings)
    application_control: ApplicationControlSettings = Field(default_factory=ApplicationControlSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    web_intelligence: WebIntelligenceSettings = Field(default_factory=WebIntelligenceSettings)
    coding_agent: CodingAgentSettings = Field(default_factory=CodingAgentSettings)

    def model_post_init(self, __context: Any) -> None:
        """Validate settings after initialization."""
        self.validate_configuration()

    def validate_configuration(self) -> None:
        """Run validation routines across all configuration categories."""
        validate_server_settings(self.server)
        validate_logging_settings(self.logging)
        validate_production_settings(self.application, self.security, self.cors)
        validate_context_settings(self.context)
        validate_conversation_settings(self.conversation)
        validate_memory_settings(self.memory)
        validate_knowledge_settings(self.knowledge)
        validate_rag_settings(self.rag)
        validate_reasoning_settings(self.reasoning)
        validate_task_settings(self.tasks)
        validate_agent_settings(self.agents)
        validate_tool_settings(self.tools)
        validate_security_module_settings(self.security_module)
        validate_computer_control_settings(self.computer_control)
        validate_filesystem_settings(self.filesystem)
        validate_application_control_settings(self.application_control)
        validate_browser_settings(self.browser)
        validate_web_intelligence_settings(self.web_intelligence)
        validate_coding_agent_settings(self.coding_agent)




    def safe_dict(self) -> dict[str, Any]:
        """Return a dictionary representation with sensitive secrets redacted."""
        raw_dict = self.model_dump()
        return _redact_dict(raw_dict)

    def redacted(self) -> dict[str, Any]:
        """Alias for safe_dict() returning redacted configuration."""
        return self.safe_dict()


def _redact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask secret values and SecretStr instances in dictionary."""
    redacted_result: dict[str, Any] = {}
    secret_key_names = {"secret_key", "password", "token", "api_key", "credentials"}

    for key, val in d.items():
        if isinstance(val, SecretStr):
            redacted_result[key] = "***REDACTED***"
        elif isinstance(val, dict):
            redacted_result[key] = _redact_dict(val)
        elif key.lower() in secret_key_names:
            redacted_result[key] = "***REDACTED***"
        else:
            redacted_result[key] = val

    return redacted_result


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retrieve cached global application settings instance."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings instance (primarily for test isolation)."""
    get_settings.cache_clear()
