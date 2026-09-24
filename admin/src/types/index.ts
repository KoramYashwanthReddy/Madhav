export type AdminSection =
  | 'dashboard'
  | 'runtime'
  | 'models'
  | 'agents'
  | 'tools'
  | 'security'
  | 'tasks'
  | 'automations'
  | 'devices'
  | 'integrations'
  | 'notifications'
  | 'observability'
  | 'audit'
  | 'evaluations'
  | 'configuration'
  | 'diagnostics'
  | 'settings';

export type AdminRole = 'SUPER_ADMIN' | 'SYSTEM_ADMIN' | 'OPERATOR' | 'READ_ONLY_ADMIN';

export type SecurityMode = 'NORMAL' | 'RESTRICTED' | 'LOCKDOWN' | 'MAINTENANCE';

export type ComponentStatus = 'HEALTHY' | 'DEGRADED' | 'UNAVAILABLE' | 'ERROR' | 'UNKNOWN';

export interface ComponentHealth {
  id: string;
  name: string;
  category: 'core' | 'ai' | 'agents' | 'storage' | 'integrations' | 'observability';
  status: ComponentStatus;
  version?: string;
  latency_ms: number;
  last_check: string;
  error_summary?: string;
}

export interface AIRuntimeStatus {
  status: 'active' | 'degraded' | 'offline';
  provider: string;
  active_model: string;
  capabilities: string[];
  latency_ms: number;
  request_count: number;
  tokens_processed: number;
  error_count: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  version: string;
  format: string;
  active: boolean;
  checksum: string;
  latency_ms: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  status: 'idle' | 'running' | 'paused' | 'failed';
  module_number: number;
  capabilities: string[];
  tasks_completed: number;
  current_task_id?: string;
}

export interface ToolDefinition {
  name: string;
  category: string;
  version: string;
  enabled: boolean;
  requires_approval: boolean;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface SecurityPolicy {
  policy_id: string;
  version: string;
  scope: string;
  action: string;
  decision: 'ALLOW' | 'DENY' | 'REQUIRE_APPROVAL';
  enabled: boolean;
}

export interface SecurityViolationEvent {
  id: string;
  timestamp: string;
  subject: string;
  action: string;
  resource: string;
  reason: string;
  trace_id: string;
}

export interface TaskItem {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';
  priority: 'low' | 'medium' | 'high';
  progress_percentage: number;
  assigned_agent?: string;
  created_at: string;
}

export interface AutomationJob {
  id: string;
  name: string;
  cron_expression: string;
  enabled: boolean;
  status: 'active' | 'paused' | 'failed';
  last_run_at?: string;
  next_run_at?: string;
  target_tool: string;
}

export interface RegisteredDevice {
  device_id: string;
  name: string;
  client_type: 'desktop' | 'web' | 'mobile';
  platform: string;
  app_version: string;
  status: 'active' | 'trusted' | 'revoked' | 'expired';
  last_seen: string;
}

export interface IntegrationStatus {
  id: string;
  name: string;
  category: string;
  connected: boolean;
  auth_status: string;
  last_synced?: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  module_origin: string;
  actor: string;
  action: string;
  resource: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  details: string;
  trace_id: string;
  timestamp: string;
}

export interface TraceSpan {
  id: string;
  trace_id: string;
  component: string;
  name: string;
  duration_ms: number;
  status: 'ok' | 'error';
  start_time: string;
}

export interface EvaluationMetric {
  id: string;
  run_name: string;
  timestamp: string;
  faithfulness_score: number;
  relevance_score: number;
  tool_precision: number;
  safety_score: number;
}

export interface ConfigSetting {
  name: string;
  environment: string;
  value: string | number | boolean;
  is_secret: boolean;
  effective_source: string;
  status: 'active' | 'overridden';
}

export interface DiagnosticResult {
  id: string;
  name: string;
  category: string;
  status: 'PASSED' | 'FAILED' | 'WARNING';
  details: string;
  executed_at: string;
}

export interface SystemAlert {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  component: string;
  message: string;
  timestamp: string;
}
