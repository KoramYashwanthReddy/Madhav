"""Configuration validators and sanity checks for MAX configuration."""

from max.config.enums import Environment
from max.config.errors import ConfigurationError
from max.config.sections import (
    AgentSettings,
    ApplicationControlSettings,
    ApplicationSettings,
    ComputerControlSettings,
    ContextManagementSettings,
    ConversationSettings,
    CORSSettings,
    FilesystemSettings,
    KnowledgeSettings,
    LoggingSettings,
    MemorySettings,
    RAGSettings,
    ReasoningSettings,
    SecurityModuleSettings,
    SecuritySettings,
    ServerSettings,
    TaskSettings,
    ToolRegistrySettings,
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


def validate_knowledge_settings(k_cfg: KnowledgeSettings) -> None:
    """Validate Personal Knowledge Engine subsystem configuration parameters."""
    if k_cfg.max_entity_name_length <= 0:
        val = k_cfg.max_entity_name_length
        raise ConfigurationError(
            f"Invalid max_entity_name_length: {val}. Must be positive.",
            details={"max_entity_name_length": val},
        )
    if k_cfg.max_description_length <= 0:
        val = k_cfg.max_description_length
        raise ConfigurationError(
            f"Invalid max_description_length: {val}. Must be positive.",
            details={"max_description_length": val},
        )
    if k_cfg.max_fact_value_size <= 0:
        val = k_cfg.max_fact_value_size
        raise ConfigurationError(
            f"Invalid max_fact_value_size: {val}. Must be positive.",
            details={"max_fact_value_size": val},
        )
    if k_cfg.max_metadata_size <= 0:
        val = k_cfg.max_metadata_size
        raise ConfigurationError(
            f"Invalid max_metadata_size: {val}. Must be positive.",
            details={"max_metadata_size": val},
        )
    if k_cfg.default_page_size <= 0:
        val = k_cfg.default_page_size
        raise ConfigurationError(
            f"Invalid default_page_size: {val}. Must be positive.",
            details={"default_page_size": val},
        )
    if k_cfg.max_page_size < k_cfg.default_page_size:
        raise ConfigurationError(
            f"Invalid max_page_size: {k_cfg.max_page_size}. Must be >= default_page_size.",
            details={
                "max_page_size": k_cfg.max_page_size,
                "default_page_size": k_cfg.default_page_size,
            },
        )


def validate_rag_settings(rag_cfg: RAGSettings) -> None:
    """Validate RAG & Retrieval subsystem configuration parameters."""
    if rag_cfg.minimum_chunk_size <= 0:
        raise ConfigurationError(
            f"Invalid minimum_chunk_size: {rag_cfg.minimum_chunk_size}. Must be positive.",
            details={"minimum_chunk_size": rag_cfg.minimum_chunk_size},
        )
    if rag_cfg.chunk_size < rag_cfg.minimum_chunk_size:
        raise ConfigurationError(
            f"Invalid chunk_size: {rag_cfg.chunk_size}. Must be >= minimum_chunk_size.",
            details={
                "chunk_size": rag_cfg.chunk_size,
                "minimum_chunk_size": rag_cfg.minimum_chunk_size,
            },
        )
    if rag_cfg.maximum_chunk_size < rag_cfg.chunk_size:
        raise ConfigurationError(
            f"Invalid maximum_chunk_size: {rag_cfg.maximum_chunk_size}. Must be >= chunk_size.",
            details={
                "maximum_chunk_size": rag_cfg.maximum_chunk_size,
                "chunk_size": rag_cfg.chunk_size,
            },
        )
    if rag_cfg.chunk_overlap < 0 or rag_cfg.chunk_overlap >= rag_cfg.chunk_size:
        raise ConfigurationError(
            f"Invalid chunk_overlap: {rag_cfg.chunk_overlap}. Must be >= 0 and < chunk_size.",
            details={"chunk_overlap": rag_cfg.chunk_overlap, "chunk_size": rag_cfg.chunk_size},
        )
    if rag_cfg.default_top_k <= 0:
        raise ConfigurationError(
            f"Invalid default_top_k: {rag_cfg.default_top_k}. Must be positive.",
            details={"default_top_k": rag_cfg.default_top_k},
        )
    if rag_cfg.max_top_k < rag_cfg.default_top_k:
        raise ConfigurationError(
            f"Invalid max_top_k: {rag_cfg.max_top_k}. Must be >= default_top_k.",
            details={"max_top_k": rag_cfg.max_top_k, "default_top_k": rag_cfg.default_top_k},
        )
    if rag_cfg.embedding_dimensions <= 0:
        raise ConfigurationError(
            f"Invalid embedding_dimensions: {rag_cfg.embedding_dimensions}. Must be positive.",
            details={"embedding_dimensions": rag_cfg.embedding_dimensions},
        )


def validate_reasoning_settings(reasoning_cfg: ReasoningSettings) -> None:
    """Validate Reasoning & Planning subsystem configuration parameters."""
    if reasoning_cfg.max_plan_steps <= 0:
        raise ConfigurationError(
            f"Invalid max_plan_steps: {reasoning_cfg.max_plan_steps}. Must be positive.",
            details={"max_plan_steps": reasoning_cfg.max_plan_steps},
        )
    if reasoning_cfg.max_dependencies <= 0:
        raise ConfigurationError(
            f"Invalid max_dependencies: {reasoning_cfg.max_dependencies}. Must be positive.",
            details={"max_dependencies": reasoning_cfg.max_dependencies},
        )
    if reasoning_cfg.max_assumptions <= 0:
        raise ConfigurationError(
            f"Invalid max_assumptions: {reasoning_cfg.max_assumptions}. Must be positive.",
            details={"max_assumptions": reasoning_cfg.max_assumptions},
        )
    if reasoning_cfg.max_risks <= 0:
        raise ConfigurationError(
            f"Invalid max_risks: {reasoning_cfg.max_risks}. Must be positive.",
            details={"max_risks": reasoning_cfg.max_risks},
        )
    if reasoning_cfg.max_evidence <= 0:
        raise ConfigurationError(
            f"Invalid max_evidence: {reasoning_cfg.max_evidence}. Must be positive.",
            details={"max_evidence": reasoning_cfg.max_evidence},
        )


def validate_task_settings(task_cfg: TaskSettings) -> None:
    """Validate Task Engine subsystem configuration parameters."""
    if task_cfg.max_page_size <= 0:
        raise ConfigurationError(
            f"Invalid max_page_size: {task_cfg.max_page_size}. Must be positive.",
            details={"max_page_size": task_cfg.max_page_size},
        )
    if task_cfg.max_title_length <= 0:
        raise ConfigurationError(
            f"Invalid max_title_length: {task_cfg.max_title_length}. Must be positive.",
            details={"max_title_length": task_cfg.max_title_length},
        )
    if task_cfg.max_description_length <= 0:
        raise ConfigurationError(
            f"Invalid max_description_length: {task_cfg.max_description_length}. Must be positive.",
            details={"max_description_length": task_cfg.max_description_length},
        )
    if task_cfg.max_dependency_depth <= 0:
        raise ConfigurationError(
            f"Invalid max_dependency_depth: {task_cfg.max_dependency_depth}. Must be positive.",
            details={"max_dependency_depth": task_cfg.max_dependency_depth},
        )
    if task_cfg.max_parent_depth <= 0:
        raise ConfigurationError(
            f"Invalid max_parent_depth: {task_cfg.max_parent_depth}. Must be positive.",
            details={"max_parent_depth": task_cfg.max_parent_depth},
        )


def validate_agent_settings(agent_cfg: AgentSettings) -> None:
    """Validate Agent Engine subsystem configuration parameters."""
    if agent_cfg.max_concurrent_runs <= 0:
        raise ConfigurationError(
            f"Invalid max_concurrent_runs: {agent_cfg.max_concurrent_runs}. Must be positive.",
            details={"max_concurrent_runs": agent_cfg.max_concurrent_runs},
        )
    if agent_cfg.max_delegation_depth <= 0:
        raise ConfigurationError(
            f"Invalid max_delegation_depth: {agent_cfg.max_delegation_depth}. Must be positive.",
            details={"max_delegation_depth": agent_cfg.max_delegation_depth},
        )
    if agent_cfg.max_delegations <= 0:
        raise ConfigurationError(
            f"Invalid max_delegations: {agent_cfg.max_delegations}. Must be positive.",
            details={"max_delegations": agent_cfg.max_delegations},
        )


def validate_tool_settings(tool_cfg: ToolRegistrySettings) -> None:
    """Validate Tool Registry subsystem configuration parameters."""
    if tool_cfg.default_timeout <= 0:
        raise ConfigurationError(
            f"Invalid default_timeout: {tool_cfg.default_timeout}. Must be positive.",
            details={"default_timeout": tool_cfg.default_timeout},
        )
    if tool_cfg.max_input_size <= 0:
        raise ConfigurationError(
            f"Invalid max_input_size: {tool_cfg.max_input_size}. Must be positive.",
            details={"max_input_size": tool_cfg.max_input_size},
        )
    if tool_cfg.max_output_size <= 0:
        raise ConfigurationError(
            f"Invalid max_output_size: {tool_cfg.max_output_size}. Must be positive.",
            details={"max_output_size": tool_cfg.max_output_size},
        )


def validate_security_module_settings(sec_module_cfg: SecurityModuleSettings) -> None:
    """Validate Permission & Security subsystem configuration parameters."""
    if sec_module_cfg.approval_timeout <= 0:
        raise ConfigurationError(
            f"Invalid approval_timeout: {sec_module_cfg.approval_timeout}. Must be positive.",
            details={"approval_timeout": sec_module_cfg.approval_timeout},
        )
    if sec_module_cfg.max_grant_duration <= 0:
        raise ConfigurationError(
            f"Invalid max_grant_duration: {sec_module_cfg.max_grant_duration}. Must be positive.",
            details={"max_grant_duration": sec_module_cfg.max_grant_duration},
        )


def validate_computer_control_settings(computer_cfg: ComputerControlSettings) -> None:
    """Validate Computer Control subsystem configuration parameters."""
    if computer_cfg.default_timeout <= 0:
        raise ConfigurationError(
            f"Invalid default_timeout: {computer_cfg.default_timeout}. Must be positive.",
            details={"default_timeout": computer_cfg.default_timeout},
        )
    if computer_cfg.max_sequence_length <= 0:
        raise ConfigurationError(
            f"Invalid max_sequence_length: {computer_cfg.max_sequence_length}. Must be positive.",
            details={"max_sequence_length": computer_cfg.max_sequence_length},
        )
    if computer_cfg.max_click_count <= 0:
        raise ConfigurationError(
            f"Invalid max_click_count: {computer_cfg.max_click_count}. Must be positive.",
            details={"max_click_count": computer_cfg.max_click_count},
        )
    if computer_cfg.max_typed_text_length <= 0:
        raise ConfigurationError(
            f"Invalid max_typed_text_length: {computer_cfg.max_typed_text_length}. Must be positive.",
            details={"max_typed_text_length": computer_cfg.max_typed_text_length},
        )


def validate_filesystem_settings(fs_cfg: FilesystemSettings) -> None:
    """Validate Filesystem Agent subsystem configuration parameters."""
    if fs_cfg.max_read_bytes <= 0:
        raise ConfigurationError(
            f"Invalid max_read_bytes: {fs_cfg.max_read_bytes}. Must be positive.",
            details={"max_read_bytes": fs_cfg.max_read_bytes},
        )
    if fs_cfg.max_write_bytes <= 0:
        raise ConfigurationError(
            f"Invalid max_write_bytes: {fs_cfg.max_write_bytes}. Must be positive.",
            details={"max_write_bytes": fs_cfg.max_write_bytes},
        )
    if fs_cfg.max_search_results <= 0:
        raise ConfigurationError(
            f"Invalid max_search_results: {fs_cfg.max_search_results}. Must be positive.",
            details={"max_search_results": fs_cfg.max_search_results},
        )
    if fs_cfg.max_search_depth <= 0:
        raise ConfigurationError(
            f"Invalid max_search_depth: {fs_cfg.max_search_depth}. Must be positive.",
            details={"max_search_depth": fs_cfg.max_search_depth},
        )
    if fs_cfg.operation_timeout <= 0:
        raise ConfigurationError(
            f"Invalid operation_timeout: {fs_cfg.operation_timeout}. Must be positive.",
            details={"operation_timeout": fs_cfg.operation_timeout},
        )


def validate_application_control_settings(app_cfg: ApplicationControlSettings) -> None:
    """Validate Application Control subsystem configuration parameters."""
    if app_cfg.default_launch_timeout <= 0:
        raise ConfigurationError(
            f"Invalid default_launch_timeout: {app_cfg.default_launch_timeout}. Must be positive.",
            details={"default_launch_timeout": app_cfg.default_launch_timeout},
        )
    if app_cfg.max_instances_per_app <= 0:
        raise ConfigurationError(
            f"Invalid max_instances_per_app: {app_cfg.max_instances_per_app}. Must be positive.",
            details={"max_instances_per_app": app_cfg.max_instances_per_app},
        )
    if app_cfg.max_page_size <= 0:
        raise ConfigurationError(
            f"Invalid max_page_size: {app_cfg.max_page_size}. Must be positive.",
            details={"max_page_size": app_cfg.max_page_size},
        )



