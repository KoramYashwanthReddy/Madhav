export type BottomTab = 'home' | 'chat' | 'tasks' | 'notifications' | 'more';

export type MobileView =
  | 'home'
  | 'chat'
  | 'voice'
  | 'tasks'
  | 'automations'
  | 'memory'
  | 'knowledge'
  | 'notifications'
  | 'activity'
  | 'integrations'
  | 'profile'
  | 'settings'
  | 'device'
  | 'help';

export type ConnectionMode = 'LOCAL' | 'REMOTE' | 'OFFLINE' | 'UNKNOWN';

export type VoiceState =
  | 'IDLE'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'THINKING'
  | 'SPEAKING'
  | 'STOPPED'
  | 'ERROR';

export type CapabilityName =
  | 'BATTERY_STATUS'
  | 'NETWORK_STATUS'
  | 'OPEN_APP'
  | 'OPEN_URL'
  | 'SHOW_NOTIFICATION'
  | 'CALENDAR_READ'
  | 'CALENDAR_WRITE'
  | 'CONTACTS_READ'
  | 'CONTACTS_WRITE'
  | 'LOCATION'
  | 'FILE_PICKER'
  | 'CLIPBOARD';

export type PermissionState = 'supported' | 'unsupported' | 'permission_denied' | 'unavailable';

export interface MobileActionPayload {
  action_id: string;
  device_id: string;
  capability: CapabilityName;
  arguments: Record<string, unknown>;
  requested_by: string;
  authorization: {
    authorized: boolean;
    approval_id?: string;
    risk_level?: 'low' | 'medium' | 'high' | 'critical';
  };
  created_at: string;
  expires_at: string; // 60s TTL
  idempotency_key: string;
}

export interface DeviceInfo {
  device_id: string;
  device_name: string;
  platform: 'android' | 'ios' | 'web';
  app_version: string;
  os_version: string;
  registered_at: string;
  last_seen_at: string;
  battery_level: number; // 0.0 - 1.0
  is_charging: boolean;
  network_type: 'wifi' | 'cellular' | 'none';
  push_token?: string;
}

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
  execution_steps?: Array<{
    id: string;
    description: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
  }>;
  sources?: Array<{
    id: string;
    title: string;
    snippet: string;
  }>;
}

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  assigned_agent?: string;
  progress_percentage: number;
  steps_total: number;
  steps_completed: number;
}

export interface AutomationJob {
  id: string;
  name: string;
  description: string;
  cron_expression: string;
  enabled: boolean;
  last_run_at?: string;
  next_run_at?: string;
  status: 'active' | 'paused' | 'failed';
  target_tool: string;
}

export interface MemoryEntry {
  id: string;
  memory_type: 'fact' | 'preference' | 'concept';
  content: string;
  importance: number;
  confidence: number;
  created_at: string;
  tags: string[];
}

export interface KnowledgeNode {
  id: string;
  label: string;
  node_type: string;
  properties: Record<string, unknown>;
}

export interface ProactiveNotification {
  id: string;
  title: string;
  message: string;
  category: 'info' | 'suggestion' | 'alert' | 'approval';
  read: boolean;
  timestamp: string;
}

export interface IntegrationConnector {
  id: string;
  name: string;
  category: string;
  connected: boolean;
  auth_status: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  module_origin: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  details: string;
  timestamp: string;
}

export interface SecurityApprovalRequest {
  id: string;
  tool_name: string;
  description: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  arguments: Record<string, unknown>;
  requested_at: string;
}

export interface UserProfile {
  name: string;
  email: string;
  preferred_language: string;
  time_zone: string;
}
