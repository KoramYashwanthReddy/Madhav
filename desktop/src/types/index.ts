export type ViewType =
  | "chat"
  | "tasks"
  | "memory"
  | "automations"
  | "integrations"
  | "evaluations"
  | "observability"
  | "settings";

export interface BackendStatus {
  is_running: boolean;
  endpoint: string;
  latency_ms: number;
  status_code: number;
  message: string;
}

export interface SystemInfo {
  os_name: string;
  os_version: string;
  host_name: string;
  cpu_count: number;
  total_memory_mb: number;
  used_memory_mb: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  reasoning?: string;
  tools_used?: string[];
  span_id?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface TaskItem {
  id: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed";
  priority: "low" | "medium" | "high" | "urgent";
  progress: number;
  created_at: string;
  subtasks?: string[];
}

export interface AgentRun {
  id: string;
  agent_name: string;
  agent_type: string;
  status: "idle" | "thinking" | "executing" | "completed" | "failed";
  current_step: string;
  duration_ms: number;
}

export interface MemoryItem {
  id: string;
  category: "preference" | "fact" | "habit" | "context";
  content: string;
  confidence: number;
  updated_at: string;
}

export interface KnowledgeDoc {
  id: string;
  title: string;
  source: string;
  content_preview: string;
  file_type: string;
}

export interface AutomationJob {
  id: string;
  name: string;
  cron_expression: string;
  status: "active" | "paused";
  last_run?: string;
  next_run?: string;
}

export interface IntegrationConn {
  id: string;
  name: string;
  provider: "github" | "browser" | "filesystem" | "terminal" | "web";
  status: "connected" | "disconnected" | "error";
  last_sync?: string;
}

export interface EvaluationReport {
  id: string;
  suite_name: string;
  total_cases: number;
  passed_cases: number;
  score: number;
  created_at: string;
}

export interface TraceSummary {
  trace_id: string;
  root_span_id: string;
  duration_ms: number;
  status: string;
  span_count: number;
  error_count: number;
}

export interface AuditRecord {
  event_id: string;
  timestamp: string;
  event_type: string;
  actor: string;
  action: string;
  target: string;
  outcome: string;
  severity: string;
}

export interface SecurityApprovalRequest {
  id: string;
  tool_name: string;
  action: string;
  resource: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  reason: string;
  expires_at: string;
}
