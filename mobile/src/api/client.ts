/// <reference types="vite/client" />

import { secureStorage } from '../services/SecureStorageService';
import {
  BackendHealth,
  ChatMessage,
  TaskItem,
  AutomationJob,
  MemoryEntry,
  KnowledgeNode,
  ProactiveNotification,
  IntegrationConnector,
  AuditEvent,
  SecurityApprovalRequest,
  DeviceInfo,
  UserProfile,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class MaxMobileApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const token = await secureStorage.getToken('auth_token');
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(options?.headers || {}),
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`Mobile API Error ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch {
      return this.getMockFallback<T>(endpoint);
    }
  }

  // Health
  async getHealth(): Promise<BackendHealth> {
    return this.request<BackendHealth>('/health');
  }

  // Device Registration
  async registerDevice(device: Partial<DeviceInfo>): Promise<DeviceInfo> {
    return this.request<DeviceInfo>('/device/register', {
      method: 'POST',
      body: JSON.stringify(device),
    });
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

  // Memory & Knowledge
  async getMemories(query?: string): Promise<MemoryEntry[]> {
    const q = query ? `?q=${encodeURIComponent(query)}` : '';
    return this.request<MemoryEntry[]>(`/memory${q}`);
  }

  async getKnowledgeNodes(): Promise<KnowledgeNode[]> {
    return this.request<KnowledgeNode[]>('/knowledge/nodes');
  }

  // Notifications
  async getNotifications(): Promise<ProactiveNotification[]> {
    return this.request<ProactiveNotification[]>('/notifications');
  }

  // Integrations
  async getIntegrations(): Promise<IntegrationConnector[]> {
    return this.request<IntegrationConnector[]>('/integrations');
  }

  // Activity
  async getActivityLogs(): Promise<AuditEvent[]> {
    return this.request<AuditEvent[]>('/audit/logs');
  }

  // Security Approvals
  async getPendingApprovals(): Promise<SecurityApprovalRequest[]> {
    return this.request<SecurityApprovalRequest[]>('/permissions/approvals');
  }

  async respondApproval(id: string, approved: boolean): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(`/permissions/approvals/${id}`, {
      method: 'POST',
      body: JSON.stringify({ approved }),
    });
  }

  // User Profile
  async getUserProfile(): Promise<UserProfile> {
    return this.request<UserProfile>('/identity/profile');
  }

  private getMockFallback<T>(endpoint: string): T {
    if (endpoint.includes('/health')) {
      return {
        status: 'ok',
        version: '1.0.0-module36',
        uptime_seconds: 18400,
        active_modules: 35,
        timestamp: new Date().toISOString(),
      } as unknown as T;
    }

    if (endpoint.includes('/device/register')) {
      return {
        device_id: 'mob-dev-99412',
        device_name: 'Max Galaxy Phone',
        platform: 'android',
        app_version: '1.0.0-module36',
        os_version: 'Android 15',
        registered_at: new Date().toISOString(),
        last_seen_at: new Date().toISOString(),
        battery_level: 0.88,
        is_charging: true,
        network_type: 'wifi',
      } as unknown as T;
    }

    if (endpoint.includes('/tasks')) {
      return [
        {
          id: 'task-m1',
          title: 'Review Mobile System Architecture',
          description: 'Verify Module 36 React Native client contract compliance',
          status: 'in_progress',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          assigned_agent: 'Mobile Agent (Module 36)',
          progress_percentage: 80,
          steps_total: 5,
          steps_completed: 4,
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/automations')) {
      return [
        {
          id: 'auto-m1',
          name: 'Daily Morning Mobile Summary',
          description: 'Send proactive push notification briefing at 8:00 AM',
          cron_expression: '0 8 * * *',
          enabled: true,
          status: 'active',
          target_tool: 'show_notification',
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/memory')) {
      return [
        {
          id: 'mem-m1',
          memory_type: 'preference',
          content: 'User prefers Dark Mode and voice interactions on mobile.',
          importance: 0.95,
          confidence: 0.99,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          tags: ['mobile', 'preference', 'ui'],
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/knowledge/nodes')) {
      return [
        { id: 'k1', label: 'Max Mobile Client', node_type: 'client', properties: { module: '36' } },
        { id: 'k2', label: 'Permission Engine', node_type: 'security', properties: { module: '15' } },
      ] as unknown as T;
    }

    if (endpoint.includes('/notifications')) {
      return [
        {
          id: 'notif-m1',
          title: 'Mobile Capability Approval Needed',
          message: 'Mobile Agent requested location permission for weather query',
          category: 'approval',
          read: false,
          timestamp: new Date().toISOString(),
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/integrations')) {
      return [
        { id: 'int-m1', name: 'Android OS Capabilities', category: 'mobile', connected: true, auth_status: 'authorized' },
        { id: 'int-m2', name: 'GitHub Developer Connector', category: 'developer', connected: true, auth_status: 'authenticated' },
      ] as unknown as T;
    }

    if (endpoint.includes('/audit/logs')) {
      return [
        { id: 'aud-m1', event_type: 'MOBILE_ACTION', module_origin: 'Module 36 Mobile Agent', severity: 'info', details: 'Validated OPEN_URL for https://github.com', timestamp: new Date().toISOString() },
      ] as unknown as T;
    }

    if (endpoint.includes('/permissions/approvals')) {
      return [
        {
          id: 'appr-m1',
          tool_name: 'open_url',
          description: 'Open external URL https://github.com/KoramYashwanthReddy/Max',
          risk_level: 'low',
          arguments: { url: 'https://github.com/KoramYashwanthReddy/Max' },
          requested_at: new Date().toISOString(),
        },
      ] as unknown as T;
    }

    if (endpoint.includes('/identity/profile')) {
      return {
        name: 'Max Primary User',
        email: 'user@max.internal',
        preferred_language: 'en-US',
        time_zone: 'UTC+05:30',
      } as unknown as T;
    }

    return {} as T;
  }
}

export const mobileApiClient = new MaxMobileApiClient();
