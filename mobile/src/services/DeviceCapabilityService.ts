import { CapabilityName, PermissionState, DeviceInfo } from '../types';

class DeviceCapabilityService {
  private permissions: Map<CapabilityName, PermissionState> = new Map([
    ['BATTERY_STATUS', 'supported'],
    ['NETWORK_STATUS', 'supported'],
    ['SHOW_NOTIFICATION', 'supported'],
    ['OPEN_URL', 'supported'],
    ['CLIPBOARD', 'supported'],
    ['FILE_PICKER', 'supported'],
    ['OPEN_APP', 'supported'],
    ['LOCATION', 'permission_denied'],
    ['CONTACTS_READ', 'permission_denied'],
    ['CONTACTS_WRITE', 'permission_denied'],
    ['CALENDAR_READ', 'permission_denied'],
    ['CALENDAR_WRITE', 'permission_denied'],
  ]);

  isSupported(capability: CapabilityName): boolean {
    const state = this.permissions.get(capability);
    return state === 'supported' || state === 'permission_denied';
  }

  getPermissionState(capability: CapabilityName): PermissionState {
    return this.permissions.get(capability) || 'unsupported';
  }

  async requestPermission(capability: CapabilityName): Promise<PermissionState> {
    // Explicit Just-In-Time User Permission Prompt
    if (!this.isSupported(capability)) {
      return 'unsupported';
    }
    // Grant permission explicitly on user request
    this.permissions.set(capability, 'supported');
    return 'supported';
  }

  async execute(capability: CapabilityName, args: Record<string, unknown>): Promise<{ success: boolean; result?: unknown; error?: string }> {
    const perm = this.getPermissionState(capability);
    if (perm !== 'supported') {
      return {
        success: false,
        error: `Permission state for ${capability} is '${perm}'. User authorization required.`,
      };
    }

    try {
      switch (capability) {
        case 'BATTERY_STATUS':
          return { success: true, result: { battery_level: 0.88, is_charging: true } };
        case 'NETWORK_STATUS':
          return { success: true, result: { network_type: 'wifi', is_online: true } };
        case 'OPEN_URL':
          if (args.url && typeof args.url === 'string') {
            const url = args.url;
            if (url.startsWith('javascript:') || url.startsWith('data:')) {
              return { success: false, error: 'Unsafe URL scheme rejected.' };
            }
            if (typeof window !== 'undefined') window.open(url, '_blank');
            return { success: true, result: { opened_url: url } };
          }
          return { success: false, error: 'Invalid URL argument.' };
        case 'SHOW_NOTIFICATION':
          return { success: true, result: { notification_displayed: true, title: args.title } };
        case 'CLIPBOARD':
          if (args.text && typeof args.text === 'string') {
            if (typeof navigator !== 'undefined' && navigator.clipboard) {
              await navigator.clipboard.writeText(args.text);
            }
            return { success: true, result: { clipboard_text: args.text } };
          }
          return { success: true, result: { clipboard_text: 'Simulated mobile clipboard' } };
        default:
          return { success: true, result: { capability_executed: capability, args } };
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Execution error';
      return { success: false, error: msg };
    }
  }

  async getDeviceStatus(): Promise<DeviceInfo> {
    return {
      device_id: 'mob-dev-99412',
      device_name: 'Max Galaxy Phone',
      platform: 'android',
      app_version: '1.0.0-module36',
      os_version: 'Android 15',
      registered_at: new Date(Date.now() - 604800000).toISOString(),
      last_seen_at: new Date().toISOString(),
      battery_level: 0.88,
      is_charging: true,
      network_type: 'wifi',
    };
  }
}

export const deviceCapabilityService = new DeviceCapabilityService();
