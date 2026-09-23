"""Configuration validators and sanity checks for MADHAV configuration."""

from madhav.config.enums import Environment
from madhav.config.errors import ConfigurationError
from madhav.config.sections import (
    ApplicationSettings,
    ContextManagementSettings,
    ConversationSettings,
    CORSSettings,
    LoggingSettings,
    MemorySettings,
    SecuritySettings,
    ServerSettings,
)


def validate_server_settings(server: ServerSettings) -> None:
    """Validate HTTP server network configuration."""
    if not (1 <= server.port <= 65535):
        raise ConfigurationError(
            f"Invalid server port: {server.port}. Port must be between 1 and 65535.",
            details={"port": server.port},
        )
    if server.workers < 1:
        raise ConfigurationError(
            f"Invalid worker count: {server.workers}. Must be at least 1.",
            details={"workers": server.workers},
        )


def validate_logging_settings(logging_cfg: LoggingSettings) -> None:
    """Validate logging level and formatting settings."""
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if str(logging_cfg.level).upper() not in valid_levels:
        raise ConfigurationError(
            f"Invalid log level: {logging_cfg.level}. Must be one of {sorted(valid_levels)}.",
            details={"level": str(logging_cfg.level)},
        )


def validate_production_settings(
    app_cfg: ApplicationSettings,
    sec_cfg: SecuritySettings,
    cors_cfg: CORSSettings,
) -> None:
    """Enforce strict security validation boundaries for production deployments."""
    if app_cfg.environment == Environment.PRODUCTION:
        if app_cfg.debug:
            raise ConfigurationError(
                "Production environment violation: debug mode cannot be enabled in production.",
                details={"environment": app_cfg.environment, "debug": app_cfg.debug},
            )
        if cors_cfg.enabled and cors_cfg.allow_credentials and "*" in cors_cfg.allowed_origins:
            raise ConfigurationError(
                "Production CORS violation: wildcard origin '*' is forbidden "
                "when allow_credentials is True.",
                details={"allowed_origins": cors_cfg.allowed_origins},
            )
        if not sec_cfg.allowed_hosts:
            raise ConfigurationError(
                "Production security violation: allowed_hosts list cannot be empty.",
                details={"allowed_hosts": sec_cfg.allowed_hosts},
            )


def validate_context_settings(context_cfg: ContextManagementSettings) -> None:
    """Validate Context Management subsystem configuration parameters."""
    if context_cfg.default_max_tokens <= 0:
        raise ConfigurationError(
            f"Invalid default_max_tokens: {context_cfg.default_max_tokens}. Must be positive.",
            details={"default_max_tokens": context_cfg.default_max_tokens},
        )
    if context_cfg.reserved_output_tokens < 0:
        val = context_cfg.reserved_output_tokens
        raise ConfigurationError(
            f"Invalid reserved_output_tokens: {val}. Cannot be negative.",
            details={"reserved_output_tokens": val},
        )
    if context_cfg.safety_margin_tokens < 0:
        val = context_cfg.safety_margin_tokens
        raise ConfigurationError(
            f"Invalid safety_margin_tokens: {val}. Cannot be negative.",
            details={"safety_margin_tokens": val},
        )

    if context_cfg.max_items <= 0:
        raise ConfigurationError(
            f"Invalid max_items: {context_cfg.max_items}. Must be positive.",
            details={"max_items": context_cfg.max_items},
        )
    combined_reserve = context_cfg.reserved_output_tokens + context_cfg.safety_margin_tokens
    if combined_reserve >= context_cfg.default_max_tokens:
        raise ConfigurationError(
            "Invalid context configuration: combined output reserve and safety margin "
            "exceed default max tokens capacity.",
            details={
                "default_max_tokens": context_cfg.default_max_tokens,
                "reserved_output_tokens": context_cfg.reserved_output_tokens,
                "safety_margin_tokens": context_cfg.safety_margin_tokens,
            },
        )


def validate_conversation_settings(conv_cfg: ConversationSettings) -> None:
    """Validate Conversation Engine subsystem configuration parameters."""
    if conv_cfg.max_message_characters <= 0:
        raise ConfigurationError(
            f"Invalid max_message_characters: {conv_cfg.max_message_characters}. Must be positive.",
            details={"max_message_characters": conv_cfg.max_message_characters},
        )
    if conv_cfg.max_title_characters <= 0:
        raise ConfigurationError(
            f"Invalid max_title_characters: {conv_cfg.max_title_characters}. Must be positive.",
            details={"max_title_characters": conv_cfg.max_title_characters},
        )
    if conv_cfg.default_page_size <= 0:
        raise ConfigurationError(
            f"Invalid default_page_size: {conv_cfg.default_page_size}. Must be positive.",
            details={"default_page_size": conv_cfg.default_page_size},
        )
    if conv_cfg.max_page_size < conv_cfg.default_page_size:
        raise ConfigurationError(
            f"Invalid max_page_size: {conv_cfg.max_page_size}. Must be >= default_page_size.",
            details={
                "max_page_size": conv_cfg.max_page_size,
                "default_page_size": conv_cfg.default_page_size,
            },
        )
    if conv_cfg.history_retrieval_limit <= 0:
        val = conv_cfg.history_retrieval_limit
        raise ConfigurationError(
            f"Invalid history_retrieval_limit: {val}. Must be positive.",
            details={"history_retrieval_limit": val},
        )


def validate_memory_settings(mem_cfg: MemorySettings) -> None:
    """Validate Memory Engine subsystem configuration parameters."""
    if mem_cfg.max_content_length <= 0:
        val = mem_cfg.max_content_length
        raise ConfigurationError(
            f"Invalid max_content_length: {val}. Must be positive.",
            details={"max_content_length": val},
        )
    if mem_cfg.max_metadata_size <= 0:
        val = mem_cfg.max_metadata_size
        raise ConfigurationError(
            f"Invalid max_metadata_size: {val}. Must be positive.",
            details={"max_metadata_size": val},
        )
    if mem_cfg.default_page_size <= 0:
        val = mem_cfg.default_page_size
        raise ConfigurationError(
            f"Invalid default_page_size: {val}. Must be positive.",
            details={"default_page_size": val},
        )
    if mem_cfg.max_page_size < mem_cfg.default_page_size:
        raise ConfigurationError(
            f"Invalid max_page_size: {mem_cfg.max_page_size}. Must be >= default_page_size.",
            details={
                "max_page_size": mem_cfg.max_page_size,
                "default_page_size": mem_cfg.default_page_size,
            },
        )
