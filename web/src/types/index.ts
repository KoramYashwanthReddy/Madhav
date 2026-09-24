export type NavSection =
  | 'home'
  | 'chat'
  | 'tasks'
  | 'automations'
  | 'memory'
  | 'knowledge'
  | 'agents'
  | 'tools'
  | 'integrations'
  | 'notifications'
  | 'activity'
  | 'evaluations'
  | 'system'
  | 'settings';

export type AutonomyLevel = 'strict' | 'guarded' | 'autonomous';

export interface BackendHealth {
  status: 'ok' | 'degraded' | 'error';
  version: string;
  uptime_seconds: number;
  active_modules: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: string;
  model_id?: string;
  execution_steps?: ExecutionStep[];
  sources?: KnowledgeSource[];
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ExecutionStep {
  id: string;
  step_type: 'reasoning' | 'tool_call' | 'memory_retrieval' | 'agent_delegation';
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  tool_name?: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  duration_ms?: number;
}

export interface KnowledgeSource {
  id: string;
  title: string;
  snippet: string;
  score: number;
  source_type: 'document' | 'memory' | 'web' | 'code';
}

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  updated_at: string;
  assigned_agent?: string;
  progress_percentage: number;
  steps_total: number;
  steps_completed: number;
  result_summary?: string;
}

export interface AutomationJob {
  id: string;
  name: string;
  description: string;
  cron_expression: string;
  enabled: boolean;
  last_run_at?: string;
  next_run_at?: string;
  status: 'active' | 'paused' | 'running' | 'failed';
  action_type: string;
  target_tool: string;
}

export interface MemoryEntry {
  id: string;
  memory_type: 'fact' | 'preference' | 'concept' | 'event';
  content: string;
  importance: number; // 0.0 to 1.0
  confidence: number;
  created_at: string;
  last_accessed_at: string;
  tags: string[];
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  node_type: 'entity' | 'concept' | 'document' | 'project';
  properties: Record<string, unknown>;
}

export interface KnowledgeGraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  relation: string;
  weight: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  description: string;
  status: 'idle' | 'active' | 'busy' | 'disabled';
  module_number: number;
  capabilities: string[];
  tasks_completed: number;
}

export interface ToolDefinition {
  name: string;
  description: string;
  category: 'system' | 'filesystem' | 'terminal' | 'browser' | 'code' | 'github' | 'document';
  requires_approval: boolean;
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
  }>;
}

export interface IntegrationConnector {
  id: string;
  name: string;
  category: 'developer' | 'system' | 'browser' | 'communication';
  connected: boolean;
  auth_status: 'authenticated' | 'unauthenticated' | 'expired' | 'configured';
  last_synced?: string;
}

export interface ProactiveNotification {
  id: string;
  title: string;
  message: string;
  category: 'info' | 'suggestion' | 'alert' | 'approval';
  read: boolean;
  timestamp: string;
  action_url?: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  module_origin: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  details: string;
  user_id: string;
  timestamp: string;
}

export interface EvaluationMetric {
  id: string;
  run_name: string;
  timestamp: string;
  faithfulness_score: number; // 0.0 - 1.0
  relevance_score: number;
  tool_precision: number;
  latency_avg_ms: number;
  safety_score: number;
}

export interface SystemResourceStatus {
  cpu_usage_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  active_agent_count: number;
  active_tasks_count: number;
  active_websocket_connections: number;
  model_providers: Array<{
    name: string;
    status: 'online' | 'degraded' | 'offline';
    latency_ms: number;
  }>;
}

export interface SecurityApprovalRequest {
  id: string;
  tool_name: string;
  description: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  arguments: Record<string, unknown>;
  requested_at: string;
}

export interface UserPreferences {
  theme: 'dark' | 'glass' | 'high-contrast';
  autonomy_level: AutonomyLevel;
  primary_model: string;
  api_endpoint: string;
  enable_sound_effects: boolean;
  reduced_motion: boolean;
}
