"""Configuration validators and sanity checks for MAX configuration."""

from max.config.enums import Environment
from max.config.errors import ConfigurationError
from max.config.sections import (
    AgentSettings,
    ApplicationControlSettings,
    ApplicationSettings,
    BrowserSettings,
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
    WebIntelligenceSettings,
    CodingAgentSettings,
    DeveloperAgentSettings,
    DocumentSettings,
    VisionSettings,
    SpeechSettings,
    NotificationSettings,
    SchedulerSettings,
    IntegrationsSettings,
    ProactiveSettings,
    PersonalizationSettings,
    EvaluationSettings,
)
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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


def validate_browser_settings(browser_cfg: BrowserSettings) -> None:
    """Validate Browser Agent subsystem configuration parameters."""
    if browser_cfg.navigation_timeout <= 0:
        raise ConfigurationError(
            f"Invalid navigation_timeout: {browser_cfg.navigation_timeout}. Must be positive.",
            details={"navigation_timeout": browser_cfg.navigation_timeout},
        )
    if browser_cfg.action_timeout <= 0:
        raise ConfigurationError(
            f"Invalid action_timeout: {browser_cfg.action_timeout}. Must be positive.",
            details={"action_timeout": browser_cfg.action_timeout},
        )
    if browser_cfg.max_sessions <= 0:
        raise ConfigurationError(
            f"Invalid max_sessions: {browser_cfg.max_sessions}. Must be positive.",
            details={"max_sessions": browser_cfg.max_sessions},
        )
    if browser_cfg.max_tabs_per_session <= 0:
        raise ConfigurationError(
            f"Invalid max_tabs_per_session: {browser_cfg.max_tabs_per_session}. Must be positive.",
            details={"max_tabs_per_session": browser_cfg.max_tabs_per_session},
        )


def validate_web_intelligence_settings(web_cfg: WebIntelligenceSettings) -> None:
    """Validate Web Intelligence subsystem configuration parameters."""
    if web_cfg.max_queries <= 0:
        raise ConfigurationError(
            f"Invalid max_queries: {web_cfg.max_queries}. Must be positive.",
            details={"max_queries": web_cfg.max_queries},
        )
    if web_cfg.max_sources <= 0:
        raise ConfigurationError(
            f"Invalid max_sources: {web_cfg.max_sources}. Must be positive.",
            details={"max_sources": web_cfg.max_sources},
        )
    if web_cfg.max_research_duration_seconds <= 0:
        raise ConfigurationError(
            f"Invalid max_research_duration_seconds: {web_cfg.max_research_duration_seconds}. Must be positive.",
            details={"max_research_duration_seconds": web_cfg.max_research_duration_seconds},
        )


def validate_coding_agent_settings(coding_cfg: CodingAgentSettings) -> None:
    """Validate Coding Agent subsystem configuration parameters."""
    if coding_cfg.max_repository_bytes <= 0:
        raise ConfigurationError(
            f"Invalid max_repository_bytes: {coding_cfg.max_repository_bytes}. Must be positive.",
            details={"max_repository_bytes": coding_cfg.max_repository_bytes},
        )
    if coding_cfg.max_files_per_analysis <= 0:
        raise ConfigurationError(
            f"Invalid max_files_per_analysis: {coding_cfg.max_files_per_analysis}. Must be positive.",
            details={"max_files_per_analysis": coding_cfg.max_files_per_analysis},
        )
    if coding_cfg.max_fix_iterations <= 0:
        raise ConfigurationError(
            f"Invalid max_fix_iterations: {coding_cfg.max_fix_iterations}. Must be positive.",
            details={"max_fix_iterations": coding_cfg.max_fix_iterations},
        )



def validate_developer_agent_settings(dev_cfg: DeveloperAgentSettings) -> None:
    """Validate Developer Agent subsystem configuration parameters."""
    if dev_cfg.max_sessions <= 0:
        raise ConfigurationError(
            f"Invalid max_sessions: {dev_cfg.max_sessions}. Must be positive.",
            details={"max_sessions": dev_cfg.max_sessions},
        )
    if dev_cfg.max_workflows_per_session <= 0:
        raise ConfigurationError(
            f"Invalid max_workflows_per_session: {dev_cfg.max_workflows_per_session}. Must be positive.",
            details={"max_workflows_per_session": dev_cfg.max_workflows_per_session},
        )
    if dev_cfg.git_command_timeout <= 0:
        raise ConfigurationError(
            f"Invalid git_command_timeout: {dev_cfg.git_command_timeout}. Must be positive.",
            details={"git_command_timeout": dev_cfg.git_command_timeout},
        )
    if dev_cfg.max_commit_message_length <= 0:
        raise ConfigurationError(
            f"Invalid max_commit_message_length: {dev_cfg.max_commit_message_length}. Must be positive.",
            details={"max_commit_message_length": dev_cfg.max_commit_message_length},
        )


def validate_document_settings(doc_cfg: DocumentSettings) -> None:
    """Validate Document Intelligence subsystem configuration parameters."""
    if doc_cfg.max_document_size_mb <= 0:
        raise ConfigurationError(
            f"Invalid max_document_size_mb: {doc_cfg.max_document_size_mb}. Must be positive.",
            details={"max_document_size_mb": doc_cfg.max_document_size_mb},
        )
    if doc_cfg.max_pages <= 0:
        raise ConfigurationError(
            f"Invalid max_pages: {doc_cfg.max_pages}. Must be positive.",
            details={"max_pages": doc_cfg.max_pages},
        )
    if doc_cfg.max_processing_time <= 0:
        raise ConfigurationError(
            f"Invalid max_processing_time: {doc_cfg.max_processing_time}. Must be positive.",
            details={"max_processing_time": doc_cfg.max_processing_time},
        )


def validate_vision_settings(vis_cfg: VisionSettings) -> None:
    """Validate Vision System subsystem configuration parameters."""
    if vis_cfg.max_image_size_mb <= 0:
        raise ConfigurationError(
            f"Invalid max_image_size_mb: {vis_cfg.max_image_size_mb}. Must be positive.",
            details={"max_image_size_mb": vis_cfg.max_image_size_mb},
        )
    if vis_cfg.max_pixels <= 0:
        raise ConfigurationError(
            f"Invalid max_pixels: {vis_cfg.max_pixels}. Must be positive.",
            details={"max_pixels": vis_cfg.max_pixels},
        )
    if vis_cfg.max_processing_time <= 0:
        raise ConfigurationError(
            f"Invalid max_processing_time: {vis_cfg.max_processing_time}. Must be positive.",
            details={"max_processing_time": vis_cfg.max_processing_time},
        )
    if vis_cfg.high_confidence_threshold < vis_cfg.medium_confidence_threshold:
        raise ConfigurationError(
            "Vision confidence thresholds invalid: high_confidence_threshold must be >= medium.",
            details={
                "high": vis_cfg.high_confidence_threshold,
                "medium": vis_cfg.medium_confidence_threshold,
            },
        )
    if vis_cfg.medium_confidence_threshold < vis_cfg.low_confidence_threshold:
        raise ConfigurationError(
            "Vision confidence thresholds invalid: medium_confidence_threshold must be >= low.",
            details={
                "medium": vis_cfg.medium_confidence_threshold,
                "low": vis_cfg.low_confidence_threshold,
            },
        )


def validate_speech_settings(speech_cfg: SpeechSettings) -> None:
    """Validate Speech System subsystem configuration parameters."""
    if speech_cfg.max_audio_size_mb <= 0:
        raise ConfigurationError(
            f"Invalid max_audio_size_mb: {speech_cfg.max_audio_size_mb}. Must be positive.",
            details={"max_audio_size_mb": speech_cfg.max_audio_size_mb},
        )
    if speech_cfg.max_audio_duration_seconds <= 0:
        raise ConfigurationError(
            f"Invalid max_audio_duration_seconds: {speech_cfg.max_audio_duration_seconds}. Must be positive.",
            details={"max_audio_duration_seconds": speech_cfg.max_audio_duration_seconds},
        )
    if speech_cfg.vad_speech_threshold < speech_cfg.vad_silence_threshold:
        raise ConfigurationError(
            "VAD thresholds invalid: vad_speech_threshold must be >= vad_silence_threshold.",
            details={
                "speech_threshold": speech_cfg.vad_speech_threshold,
                "silence_threshold": speech_cfg.vad_silence_threshold,
            },
        )


def validate_notification_settings(notif_cfg: NotificationSettings) -> None:
    """Validate Notification System subsystem configuration parameters."""
    if notif_cfg.max_title_length <= 0:
        raise ConfigurationError(
            f"Invalid max_title_length: {notif_cfg.max_title_length}. Must be positive.",
            details={"max_title_length": notif_cfg.max_title_length},
        )
    if notif_cfg.max_body_length <= 0:
        raise ConfigurationError(
            f"Invalid max_body_length: {notif_cfg.max_body_length}. Must be positive.",
            details={"max_body_length": notif_cfg.max_body_length},
        )
    if notif_cfg.max_retries < 0:
        raise ConfigurationError(
            f"Invalid max_retries: {notif_cfg.max_retries}. Cannot be negative.",
            details={"max_retries": notif_cfg.max_retries},
        )


def validate_scheduler_settings(sched_cfg: SchedulerSettings) -> None:
    """Validate Module 28 — Scheduler System subsystem configuration parameters."""
    if sched_cfg.poll_interval <= 0:
        raise ConfigurationError(
            f"Invalid poll_interval: {sched_cfg.poll_interval}. Must be positive.",
            details={"poll_interval": sched_cfg.poll_interval},
        )
    if sched_cfg.max_concurrency <= 0:
        raise ConfigurationError(
            f"Invalid max_concurrency: {sched_cfg.max_concurrency}. Must be positive.",
            details={"max_concurrency": sched_cfg.max_concurrency},
        )
    try:
        ZoneInfo(sched_cfg.timezone)
    except (ZoneInfoNotFoundError, Exception) as exc:
        raise ConfigurationError(
            f"Invalid IANA timezone: {sched_cfg.timezone}.",
            details={"timezone": sched_cfg.timezone, "error": str(exc)},
        )


def validate_integrations_settings(integrations_cfg: IntegrationsSettings) -> None:
    """Validate Module 29 — External Integrations subsystem configuration parameters."""
    if integrations_cfg.request_timeout_seconds <= 0:
        raise ConfigurationError(
            f"Invalid request_timeout_seconds: {integrations_cfg.request_timeout_seconds}. Must be positive.",
            details={"request_timeout_seconds": integrations_cfg.request_timeout_seconds},
        )
    if integrations_cfg.rate_limit_per_minute <= 0:
        raise ConfigurationError(
            f"Invalid rate_limit_per_minute: {integrations_cfg.rate_limit_per_minute}. Must be positive.",
            details={"rate_limit_per_minute": integrations_cfg.rate_limit_per_minute},
        )


def validate_proactive_settings(proactive_cfg: ProactiveSettings) -> None:
    """Validate Module 30 — Proactive Intelligence Engine subsystem configuration parameters."""
    if proactive_cfg.mode.upper() not in ("PASSIVE", "NORMAL", "PROACTIVE", "AUTONOMOUS"):
        raise ConfigurationError(
            f"Invalid proactive mode: {proactive_cfg.mode}.",
            details={"mode": proactive_cfg.mode},
        )
    if proactive_cfg.max_notifications_per_hour <= 0:
        raise ConfigurationError(
            f"Invalid max_notifications_per_hour: {proactive_cfg.max_notifications_per_hour}. Must be positive.",
            details={"max_notifications_per_hour": proactive_cfg.max_notifications_per_hour},
        )


def validate_personalization_settings(personalization_cfg: PersonalizationSettings) -> None:
    """Validate Module 31 — Learning & Personalization Engine configuration parameters."""
    valid_modes = {"OFF", "EXPLICIT_ONLY", "ASSISTED", "ADAPTIVE"}
    if personalization_cfg.mode.upper() not in valid_modes:
        raise ConfigurationError(
            f"Invalid learning mode: {personalization_cfg.mode}. Must be one of {sorted(valid_modes)}.",
            details={"mode": personalization_cfg.mode},
        )
    if not (0.0 <= personalization_cfg.min_confidence <= 1.0):
        raise ConfigurationError(
            f"Invalid min_confidence: {personalization_cfg.min_confidence}. Must be between 0.0 and 1.0.",
            details={"min_confidence": personalization_cfg.min_confidence},
        )
    if personalization_cfg.min_evidence < 1:
        raise ConfigurationError(
            f"Invalid min_evidence: {personalization_cfg.min_evidence}. Must be at least 1.",
            details={"min_evidence": personalization_cfg.min_evidence},
        )


def validate_evaluation_settings(evaluation_cfg: EvaluationSettings) -> None:
    """Validate Module 32 — Evaluation System configuration parameters."""
    if evaluation_cfg.timeout_seconds <= 0:
        raise ConfigurationError(
            f"Invalid timeout_seconds: {evaluation_cfg.timeout_seconds}. Must be positive.",
            details={"timeout_seconds": evaluation_cfg.timeout_seconds},
        )
    if evaluation_cfg.max_cases_per_run < 1:
        raise ConfigurationError(
            f"Invalid max_cases_per_run: {evaluation_cfg.max_cases_per_run}. Must be at least 1.",
            details={"max_cases_per_run": evaluation_cfg.max_cases_per_run},
        )
    if not (0.0 <= evaluation_cfg.regression_threshold <= 1.0):
        raise ConfigurationError(
            f"Invalid regression_threshold: {evaluation_cfg.regression_threshold}. Must be between 0.0 and 1.0.",
            details={"regression_threshold": evaluation_cfg.regression_threshold},
        )





