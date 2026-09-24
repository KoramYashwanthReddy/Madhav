import { MobileActionPayload } from '../types';
import { deviceCapabilityService } from './DeviceCapabilityService';

class MobileAgentService {
  private executedIdempotencyKeys: Set<string> = new Set();
  private isEmergencyStopped: boolean = false;

  triggerEmergencyStop(): void {
    this.isEmergencyStopped = true;
  }

  resetEmergencyStop(): void {
    this.isEmergencyStopped = false;
  }

  getEmergencyStopStatus(): boolean {
    return this.isEmergencyStopped;
  }

  async validateAndExecuteAction(payload: MobileActionPayload): Promise<{
    executed: boolean;
    status: 'AUTHORIZED' | 'DENIED' | 'EXPIRED' | 'DUPLICATE' | 'EMERGENCY_STOPPED';
    result?: unknown;
    error?: string;
  }> {
    if (this.isEmergencyStopped) {
      return {
        executed: false,
        status: 'EMERGENCY_STOPPED',
        error: 'Action cancelled due to active Emergency Stop.',
      };
    }

    // 1. Action Expiration Check (60s TTL)
    const now = new Date().getTime();
    const expires = new Date(payload.expires_at).getTime();
    if (now > expires) {
      return {
        executed: false,
        status: 'EXPIRED',
        error: 'Action authorization expired.',
      };
    }

    // 2. Idempotency Key Deduplication Check
    if (this.executedIdempotencyKeys.has(payload.idempotency_key)) {
      return {
        executed: false,
        status: 'DUPLICATE',
        error: 'Action with this idempotency key was already executed.',
      };
    }

    // 3. Module 15 Security Authorization Boundary Check
    if (!payload.authorization || !payload.authorization.authorized) {
      return {
        executed: false,
        status: 'DENIED',
        error: 'Backend Module 15 authorization is required before executing mobile capability.',
      };
    }

    // Mark idempotency key before execution
    this.executedIdempotencyKeys.add(payload.idempotency_key);

    // Execute through DeviceCapabilityService
    const execRes = await deviceCapabilityService.execute(payload.capability, payload.arguments);

    if (execRes.success) {
      return {
        executed: true,
        status: 'AUTHORIZED',
        result: execRes.result,
      };
    } else {
      return {
        executed: false,
        status: 'DENIED',
        error: execRes.error,
      };
    }
  }
}

export const mobileAgentService = new MobileAgentService();
