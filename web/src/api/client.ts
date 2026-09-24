/// <reference types="vite/client" />

import {
  BackendHealth,
  ChatMessage,
  TaskItem,
  AutomationJob,
  MemoryEntry,
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  AgentInfo,
  ToolDefinition,
  IntegrationConnector,
  ProactiveNotification,
  AuditEvent,
  EvaluationMetric,
  SystemResourceStatus,
  SecurityApprovalRequest,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class MaxWebApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(options?.headers || {}),
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`API Error ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch {
      // Fallback mock handling if backend API is not running live
      return this.getMockFallback<T>(endpoint);
    }
  }

  // Health
  async getHealth(): Promise<BackendHealth> {
    return this.request<BackendHealth>('/health');
  }

  // Chat
  async sendMessage(prompt: string, modelId: string): Promise<ChatMessage> {
    return this.request<ChatMessage>('/chat/completions', {
      method: 'POST',
      body: JSON.stringify({ prompt, model_id: modelId }),
    });
  }

  // Tasks
  async getTasks(): Promise<TaskItem[]> {
    return this.request<TaskItem[]>('/tasks');
  }

  async createTask(title: string, description: string): Promise<TaskItem> {
    return this.request<TaskItem>('/tasks', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    });
  }

  // Automations
  async getAutomations(): Promise<AutomationJob[]> {
    return this.request<AutomationJob[]>('/automations');
  }

  async toggleAutomation(id: string, enabled: boolean): Promise<AutomationJob> {
    return this.request<AutomationJob>(`/automations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    });
  }

  // Memory & Knowledge
  async getMemories(query?: string): Promise<MemoryEntry[]> {
    const q = query ? `?q=${encodeURIComponent(query)}` : '';
    return this.request<MemoryEntry[]>(`/memory${q}`);
  }

  async getKnowledgeGraph(): Promise<{ nodes: KnowledgeGraphNode[]; edges: KnowledgeGraphEdge[] }> {
    return this.request<{ nodes: KnowledgeGraphNode[]; edges: KnowledgeGraphEdge[] }>('/knowledge/graph');
  }

  // Agents & Tools
  async getAgents(): Promise<AgentInfo[]> {
    return this.request<AgentInfo[]>('/agents');
  }

  async getTools(): Promise<ToolDefinition[]> {
    return this.request<ToolDefinition[]>('/tools');
  }

  // Integrations
  async getIntegrations(): Promise<IntegrationConnector[]> {
    return this.request<IntegrationConnector[]>('/integrations');
  }

  // Notifications
  async getNotifications(): Promise<ProactiveNotification[]> {
    return this.request<ProactiveNotification[]>('/notifications');
  }

  // Activity & Audit
  async getActivityLogs(): Promise<AuditEvent[]> {
    return this.request<AuditEvent[]>('/audit/logs');
  }

  // Evaluations
  async getEvaluationMetrics(): Promise<EvaluationMetric[]> {
    return this.request<EvaluationMetric[]>('/evaluations');
  }

  // System
  async getSystemStatus(): Promise<SystemResourceStatus> {
    return this.request<SystemResourceStatus>('/system/status');
  }

  // Approvals
  async getPendingApprovals(): Promise<SecurityApprovalRequest[]> {
    return this.request<SecurityApprovalRequest[]>('/permissions/approvals');
  }

  async respondApproval(id: string, approved: boolean): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(`/permissions/approvals/${id}`, {
      method: 'POST',
      body: JSON.stringify({ approved }),
    });
  }

  // Mock Fallbacks for offline standalone client viewing
  private getMockFallback<T>(endpoint: string): T {
    if (endpoint.includes('/health')) {
      return {
        status: 'ok',
        version: '1.0.0-module35',
        uptime_seconds: 14200,
        active_modules: 34,
        timestamp: new Date().toISOString(),
      } as unknown as T;
    }

    if (endpoint.includes('/tasks')) {
      return [
        {
          id: 'task-101',
          title: 'Analyze Repository Codebase Structure',
          description: 'Scan Python modules 01-34 and verify API contract integration',
          status: 'running',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          updated_at: new Date().toISOString(),
          assigned_agent: 'Coding Agent (Module 22)',
          progress_percentage: 75,
          steps_total: 4,
          steps_completed: 3,
        },
        {
          id: 'task-102',
          title: 'Nightly RAG Knowledge Graph Sync',
          description: 'Vectorize recent document intelligence inputs into memory graph',
          status: 'queued',
          created_at: new Date(Date.now() - 1800000).toISOString(),
          updated_at: new Date().toISOString(),
          assigned_agent: 'RAG & Memory Agent (Module 08-10)',
          progress_percentage: 0,
          steps_total: 5,
          steps_completed: 0,
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/automations')) {
      return [
        {
          id: 'auto-1',
          name: 'Daily Morning Briefing',
          description: 'Summarize calendar events, GitHub issues, and high priority news',
          cron_expression: '0 8 * * *',
          enabled: true,
          last_run_at: new Date(Date.now() - 86400000).toISOString(),
          next_run_at: new Date(Date.now() + 36000000).toISOString(),
          status: 'active',
          action_type: 'Proactive Intelligence',
          target_tool: 'notification_agent',
        },
        {
          id: 'auto-2',
          name: 'System Audit Log Cleanup',
          description: 'Prune telemetry logs older than 30 days',
          cron_expression: '0 0 * * 0',
          enabled: true,
          last_run_at: new Date(Date.now() - 172800000).toISOString(),
          next_run_at: new Date(Date.now() + 432000000).toISOString(),
          status: 'active',
          action_type: 'Observability',
          target_tool: 'audit_service',
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/memory')) {
      return [
        {
          id: 'mem-1',
          memory_type: 'preference',
          content: 'User prefers dark glassmorphism theme and concise technical explanations.',
          importance: 0.95,
          confidence: 0.99,
          created_at: new Date(Date.now() - 604800000).toISOString(),
          last_accessed_at: new Date().toISOString(),
          tags: ['ui', 'user_preference', 'communication'],
        },
        {
          id: 'mem-2',
          memory_type: 'fact',
          content: 'Max architecture uses FastAPI Python backend with Modules 01-34.',
          importance: 0.9,
          confidence: 1.0,
          created_at: new Date(Date.now() - 1209600000).toISOString(),
          last_accessed_at: new Date().toISOString(),
          tags: ['architecture', 'system', 'max'],
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/knowledge/graph')) {
      return {
        nodes: [
          { id: 'n1', label: 'Max AI Core', node_type: 'project', properties: { module: '04' } },
          { id: 'n2', label: 'Memory Engine', node_type: 'concept', properties: { module: '08' } },
          { id: 'n3', label: 'Security Engine', node_type: 'concept', properties: { module: '15' } },
          { id: 'n4', label: 'Web Application', node_type: 'entity', properties: { module: '35' } },
        ],
        edges: [
          { id: 'e1', source_id: 'n4', target_id: 'n1', relation: 'COMMUNICATES_WITH', weight: 1.0 },
          { id: 'e2', source_id: 'n1', target_id: 'n2', relation: 'USES_MEMORY', weight: 0.9 },
          { id: 'e3', source_id: 'n4', target_id: 'n3', relation: 'REQUIRES_APPROVAL', weight: 1.0 },
        ],
      } as unknown as T;
    }

    if (endpoint.includes('/agents')) {
      return [
        { id: 'ag-1', name: 'Computer Control Agent', role: 'OS Automation', description: 'Executes UI clicks and desktop actions', status: 'idle', module_number: 16, capabilities: ['mouse_click', 'keypress'], tasks_completed: 42 },
        { id: 'ag-2', name: 'Filesystem Agent', role: 'File Operations', description: 'Reads, writes, and indexes local file workspace', status: 'active', module_number: 17, capabilities: ['file_read', 'file_write', 'glob_search'], tasks_completed: 189 },
        { id: 'ag-3', name: 'Terminal Agent', role: 'Shell Operator', description: 'Executes commands in isolated pwsh environment', status: 'idle', module_number: 18, capabilities: ['exec_command', 'process_poll'], tasks_completed: 96 },
        { id: 'ag-4', name: 'Browser Agent', role: 'Web Intelligence', description: 'Controls headless browser for web research', status: 'idle', module_number: 20, capabilities: ['navigate', 'scrape', 'element_click'], tasks_completed: 64 },
      ] as unknown as T;
    }

    if (endpoint.includes('/tools')) {
      return [
        { name: 'run_command', description: 'Execute a shell command', category: 'terminal', requires_approval: true, parameters: [{ name: 'command', type: 'string', description: 'Shell string', required: true }] },
        { name: 'read_file', description: 'Read content of target file', category: 'filesystem', requires_approval: false, parameters: [{ name: 'filepath', type: 'string', description: 'Target file path', required: true }] },
        { name: 'search_web', description: 'Search web search engine', category: 'browser', requires_approval: false, parameters: [{ name: 'query', type: 'string', description: 'Search term', required: true }] },
      ] as unknown as T;
    }

    if (endpoint.includes('/integrations')) {
      return [
        { id: 'int-1', name: 'GitHub Developer Connector', category: 'developer', connected: true, auth_status: 'authenticated', last_synced: new Date().toISOString() },
        { id: 'int-2', name: 'Chromium Browser Automation', category: 'browser', connected: true, auth_status: 'configured', last_synced: new Date().toISOString() },
        { id: 'int-3', name: 'Local File System Access', category: 'system', connected: true, auth_status: 'authenticated', last_synced: new Date().toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/notifications')) {
      return [
        { id: 'notif-1', title: 'Security Approval Requested', message: 'Terminal Agent requested permission to run npm build command', category: 'approval', read: false, timestamp: new Date().toISOString() },
        { id: 'notif-2', title: 'Memory Graph Sync Completed', message: 'Indexed 14 new knowledge nodes from Module 34 documentation', category: 'info', read: true, timestamp: new Date(Date.now() - 1800000).toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/audit/logs')) {
      return [
        { id: 'aud-1', event_type: 'TOOL_EXECUTION', module_origin: 'Module 18 Terminal', severity: 'info', details: 'Executed pwsh: node -v', user_id: 'user_primary', timestamp: new Date().toISOString() },
        { id: 'aud-2', event_type: 'SECURITY_CHECK', module_origin: 'Module 15 Security', severity: 'info', details: 'Granted level 2 execution approval for run_command', user_id: 'user_primary', timestamp: new Date(Date.now() - 60000).toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/evaluations')) {
      return [
        { id: 'eval-1', run_name: 'Module 34 Integration Benchmark', timestamp: new Date().toISOString(), faithfulness_score: 0.98, relevance_score: 0.96, tool_precision: 0.99, latency_avg_ms: 320, safety_score: 1.0 },
      ] as unknown as T;
    }

    if (endpoint.includes('/system/status')) {
      return {
        cpu_usage_percent: 18.4,
        memory_used_mb: 412,
        memory_total_mb: 16384,
        active_agent_count: 2,
        active_tasks_count: 1,
        active_websocket_connections: 1,
        model_providers: [
          { name: 'Gemini 1.5 Pro', status: 'online', latency_ms: 180 },
          { name: 'Local Ollama Llama3', status: 'online', latency_ms: 45 },
        ],
      } as unknown as T;
    }

    if (endpoint.includes('/permissions/approvals')) {
      return [
        {
          id: 'appr-1',
          tool_name: 'run_command',
          description: 'Execute npm run build in d:\\Personal AI\\Madhav\\web',
          risk_level: 'medium',
          arguments: { command: 'npm run build', cwd: 'd:\\Personal AI\\Madhav\\web' },
          requested_at: new Date().toISOString(),
        },
      ] as unknown as T;
    }

    return {} as T;
  }
}

export const webApiClient = new MaxWebApiClient();
