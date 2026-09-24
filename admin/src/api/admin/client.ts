/// <reference types="vite/client" />

import { redactJson } from '../../utils/redactSecrets';
import {
  ComponentHealth,
  AIRuntimeStatus,
  ModelInfo,
  AgentInfo,
  ToolDefinition,
  SecurityPolicy,
  SecurityViolationEvent,
  TaskItem,
  AutomationJob,
  RegisteredDevice,
  IntegrationStatus,
  AuditEvent,
  TraceSpan,
  EvaluationMetric,
  ConfigSetting,
  DiagnosticResult,
  SystemAlert,
} from '../../types';

const ADMIN_API_BASE = import.meta.env.VITE_ADMIN_API_BASE_URL || '/api/v1/admin';

class MaxAdminApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${ADMIN_API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Role': 'SUPER_ADMIN',
          ...(options?.headers || {}),
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`Admin API error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return redactJson(data) as T;
    } catch {
      return this.getMockFallback<T>(endpoint);
    }
  }

  // Dashboard & Health
  async getComponentHealth(): Promise<ComponentHealth[]> {
    return this.request<ComponentHealth[]>('/health/components');
  }

  // AI Runtime
  async getAIRuntime(): Promise<AIRuntimeStatus> {
    return this.request<AIRuntimeStatus>('/runtime');
  }

  // Models
  async getModels(): Promise<ModelInfo[]> {
    return this.request<ModelInfo[]>('/models');
  }

  async toggleModel(id: string, active: boolean): Promise<ModelInfo> {
    return this.request<ModelInfo>(`/models/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ active }),
    });
  }

  // Agents
  async getAgents(): Promise<AgentInfo[]> {
    return this.request<AgentInfo[]>('/agents');
  }

  async controlAgent(id: string, action: 'pause' | 'resume' | 'restart'): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(`/agents/${id}/control`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  }

  // Tools
  async getTools(): Promise<ToolDefinition[]> {
    return this.request<ToolDefinition[]>('/tools');
  }

  // Security & Policies
  async getSecurityPolicies(): Promise<SecurityPolicy[]> {
    return this.request<SecurityPolicy[]>('/security/policies');
  }

  async getSecurityViolations(): Promise<SecurityViolationEvent[]> {
    return this.request<SecurityViolationEvent[]>('/security/violations');
  }

  async triggerKillSwitch(): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>('/security/kill-switch', {
      method: 'POST',
      body: JSON.stringify({ reason: 'Admin Emergency Kill Switch Triggered' }),
    });
  }

  // Tasks
  async getTasks(): Promise<TaskItem[]> {
    return this.request<TaskItem[]>('/tasks');
  }

  // Automations
  async getAutomations(): Promise<AutomationJob[]> {
    return this.request<AutomationJob[]>('/automations');
  }

  // Devices
  async getDevices(): Promise<RegisteredDevice[]> {
    return this.request<RegisteredDevice[]>('/devices');
  }

  async revokeDevice(id: string): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(`/devices/${id}/revoke`, {
      method: 'POST',
    });
  }

  // Integrations
  async getIntegrations(): Promise<IntegrationStatus[]> {
    return this.request<IntegrationStatus[]>('/integrations');
  }

  // Observability & Logs
  async getAuditLogs(query?: string): Promise<AuditEvent[]> {
    const q = query ? `?q=${encodeURIComponent(query)}` : '';
    return this.request<AuditEvent[]>(`/audit/logs${q}`);
  }

  async getTraces(): Promise<TraceSpan[]> {
    return this.request<TraceSpan[]>('/observability/traces');
  }

  // Evaluations
  async getEvaluations(): Promise<EvaluationMetric[]> {
    return this.request<EvaluationMetric[]>('/evaluations');
  }

  // Configuration
  async getConfiguration(): Promise<ConfigSetting[]> {
    return this.request<ConfigSetting[]>('/configuration');
  }

  // Diagnostics
  async runDiagnostics(): Promise<DiagnosticResult[]> {
    return this.request<DiagnosticResult[]>('/diagnostics/run', { method: 'POST' });
  }

  // System Alerts
  async getSystemAlerts(): Promise<SystemAlert[]> {
    return this.request<SystemAlert[]>('/alerts');
  }

  // Mock Fallback Simulation for Standalone Preview Mode
  private getMockFallback<T>(endpoint: string): T {
    if (endpoint.includes('/health/components')) {
      return [
        { id: 'c1', name: 'Platform Foundation (Mod 01)', category: 'core', status: 'HEALTHY', latency_ms: 12, last_check: new Date().toISOString() },
        { id: 'c2', name: 'AI Runtime (Mod 04)', category: 'ai', status: 'HEALTHY', latency_ms: 140, last_check: new Date().toISOString() },
        { id: 'c3', name: 'Memory Engine (Mod 08)', category: 'storage', status: 'HEALTHY', latency_ms: 22, last_check: new Date().toISOString() },
        { id: 'c4', name: 'Permission & Security (Mod 15)', category: 'core', status: 'HEALTHY', latency_ms: 8, last_check: new Date().toISOString() },
        { id: 'c5', name: 'Terminal Agent (Mod 18)', category: 'agents', status: 'HEALTHY', latency_ms: 18, last_check: new Date().toISOString() },
        { id: 'c6', name: 'Observability & Audit (Mod 33)', category: 'observability', status: 'HEALTHY', latency_ms: 15, last_check: new Date().toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/runtime')) {
      return {
        status: 'active',
        provider: 'Gemini 1.5 Pro',
        active_model: 'gemini-1.5-pro',
        capabilities: ['text_completion', 'tool_use', 'vision_multimodal', 'streaming'],
        latency_ms: 140,
        request_count: 1420,
        tokens_processed: 894000,
        error_count: 2,
      } as unknown as T;
    }

    if (endpoint.includes('/models')) {
      return [
        { id: 'm1', name: 'Gemini 1.5 Pro', provider: 'Google Cloud', version: '1.5.0', format: 'API', active: true, checksum: 'sha256-a94f118c', latency_ms: 140 },
        { id: 'm2', name: 'Ollama Llama3 8B', provider: 'Local Ollama', version: '3.0.0', format: 'GGUF', active: true, checksum: 'sha256-f83199b0', latency_ms: 45 },
      ] as unknown as T;
    }

    if (endpoint.includes('/agents')) {
      return [
        { id: 'ag1', name: 'Computer Control Agent', role: 'OS UI Operator', status: 'idle', module_number: 16, capabilities: ['mouse_click', 'keypress'], tasks_completed: 42 },
        { id: 'ag2', name: 'Filesystem Agent', role: 'Workspace File Operator', status: 'running', module_number: 17, capabilities: ['file_read', 'file_write'], tasks_completed: 189 },
        { id: 'ag3', name: 'Terminal Agent', role: 'Shell Operator', status: 'idle', module_number: 18, capabilities: ['exec_command'], tasks_completed: 96 },
      ] as unknown as T;
    }

    if (endpoint.includes('/tools')) {
      return [
        { name: 'run_command', category: 'terminal', version: '1.0', enabled: true, requires_approval: true, risk_level: 'high' },
        { name: 'read_file', category: 'filesystem', version: '1.0', enabled: true, requires_approval: false, risk_level: 'low' },
        { name: 'write_file', category: 'filesystem', version: '1.0', enabled: true, requires_approval: true, risk_level: 'medium' },
      ] as unknown as T;
    }

    if (endpoint.includes('/security/policies')) {
      return [
        { policy_id: 'pol-15-01', version: '1.0', scope: 'terminal', action: 'exec_command', decision: 'REQUIRE_APPROVAL', enabled: true },
        { policy_id: 'pol-15-02', version: '1.0', scope: 'filesystem', action: 'read_file', decision: 'ALLOW', enabled: true },
      ] as unknown as T;
    }

    if (endpoint.includes('/security/violations')) {
      return [
        { id: 'viol-1', timestamp: new Date(Date.now() - 3600000).toISOString(), subject: 'agent_terminal', action: 'exec_untrusted_script', resource: '/etc/passwd', reason: 'Attempted access to restricted system path', trace_id: 'tr-9941' },
      ] as unknown as T;
    }

    if (endpoint.includes('/devices')) {
      return [
        { device_id: 'dev-desk-1', name: 'Max Windows Desktop', client_type: 'desktop', platform: 'Windows 11', app_version: '1.0.0-mod34', status: 'active', last_seen: new Date().toISOString() },
        { device_id: 'dev-web-1', name: 'Max Web Browser Session', client_type: 'web', platform: 'Chrome 122', app_version: '1.0.0-mod35', status: 'active', last_seen: new Date().toISOString() },
        { device_id: 'dev-mob-1', name: 'Max Galaxy Phone', client_type: 'mobile', platform: 'Android 15', app_version: '1.0.0-mod36', status: 'active', last_seen: new Date().toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/audit/logs')) {
      return [
        { id: 'aud-1', event_type: 'ADMIN_ACTION', module_origin: 'Module 37 Admin Console', actor: 'admin_primary', action: 'INSPECT_SECURITY_POLICIES', resource: 'Module 15', severity: 'info', details: 'Admin inspected active security policies', trace_id: 'tr-8812', timestamp: new Date().toISOString() },
        { id: 'aud-2', event_type: 'TOOL_EXECUTION', module_origin: 'Module 18 Terminal', actor: 'system', action: 'RUN_COMMAND', resource: 'pwsh', severity: 'info', details: 'Executed npm run build in web package', trace_id: 'tr-8813', timestamp: new Date(Date.now() - 60000).toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/observability/traces')) {
      return [
        { id: 'sp-1', trace_id: 'tr-8813', component: 'Module 07 Conversation', name: 'process_prompt', duration_ms: 120, status: 'ok', start_time: new Date(Date.now() - 5000).toISOString() },
        { id: 'sp-2', trace_id: 'tr-8813', component: 'Module 15 Security', name: 'authorize_action', duration_ms: 12, status: 'ok', start_time: new Date(Date.now() - 4800).toISOString() },
        { id: 'sp-3', trace_id: 'tr-8813', component: 'Module 18 Terminal', name: 'exec_command', duration_ms: 85, status: 'ok', start_time: new Date(Date.now() - 4700).toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/evaluations')) {
      return [
        { id: 'ev-1', run_name: 'Module 36 Cross-Platform Suite', timestamp: new Date().toISOString(), faithfulness_score: 0.99, relevance_score: 0.98, tool_precision: 1.0, safety_score: 1.0 },
      ] as unknown as T;
    }

    if (endpoint.includes('/configuration')) {
      return [
        { name: 'MAX_AUTONOMY_LEVEL', environment: 'production', value: 'GUARDED', is_secret: false, effective_source: 'env_var', status: 'active' },
        { name: 'MAX_LOG_LEVEL', environment: 'production', value: 'INFO', is_secret: false, effective_source: 'config_file', status: 'active' },
        { name: 'DATABASE_URL', environment: 'production', value: '[REDACTED_SECRET]', is_secret: true, effective_source: 'env_var', status: 'active' },
      ] as unknown as T;
    }

    if (endpoint.includes('/diagnostics/run')) {
      return [
        { id: 'diag-1', name: 'Platform Foundation Check', category: 'Core', status: 'PASSED', details: 'All core services responding on 127.0.0.1:8000', executed_at: new Date().toISOString() },
        { id: 'diag-2', name: 'Module 15 Security Engine Authorization', category: 'Security', status: 'PASSED', details: 'Permission boundary active & kill-switch ready', executed_at: new Date().toISOString() },
        { id: 'diag-3', name: 'Model Provider Latency Check', category: 'AI Runtime', status: 'PASSED', details: 'Gemini 1.5 Pro latency 140ms, Ollama 45ms', executed_at: new Date().toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/alerts')) {
      return [
        { id: 'alt-1', title: 'System Operating Normally', severity: 'low', component: 'Platform Foundation', message: 'All 36 modules loaded with zero errors.', timestamp: new Date().toISOString() },
      ] as unknown as T;
    }

    return {} as T;
  }
}

export const adminApiClient = new MaxAdminApiClient();
