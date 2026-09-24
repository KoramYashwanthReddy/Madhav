import { mobileAgentService } from '../services/MobileAgentService';
import { deviceCapabilityService } from '../services/DeviceCapabilityService';
import { secureStorage } from '../services/SecureStorageService';
import { MobileActionPayload } from '../types';

export async function runMobileUnitTests(): Promise<boolean> {
  console.log('Running Module 36 Mobile Application Unit & Security Tests...');
  let passed = 0;
  let total = 0;

  // Test 1: Secure Storage Encryption
  total++;
  await secureStorage.setToken('auth_token', 'test_bearer_token_123');
  const token = await secureStorage.getToken('auth_token');
  if (token === 'test_bearer_token_123') {
    passed++;
    console.log('✔ Test 1 Passed: Secure Token Storage abstraction works.');
  } else {
    console.error('✖ Test 1 Failed: Secure Token Storage failed.');
  }

  // Test 2: Unauthorized Action Boundary (Module 15 enforcement)
  total++;
  const unauthPayload: MobileActionPayload = {
    action_id: 'act-1',
    device_id: 'mob-dev-1',
    capability: 'OPEN_URL',
    arguments: { url: 'https://example.com' },
    requested_by: 'ai_assistant',
    authorization: { authorized: false },
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 60000).toISOString(),
    idempotency_key: 'idemp-1',
  };
  const unauthRes = await mobileAgentService.validateAndExecuteAction(unauthPayload);
  if (!unauthRes.executed && unauthRes.status === 'DENIED') {
    passed++;
    console.log('✔ Test 2 Passed: Module 15 authorization boundary blocks unauthorized mobile actions.');
  } else {
    console.error('✖ Test 2 Failed: Unauthorized action was not blocked.');
  }

  // Test 3: Action Expiration Check (60s TTL)
  total++;
  const expiredPayload: MobileActionPayload = {
    action_id: 'act-2',
    device_id: 'mob-dev-1',
    capability: 'BATTERY_STATUS',
    arguments: {},
    requested_by: 'ai_assistant',
    authorization: { authorized: true },
    created_at: new Date(Date.now() - 120000).toISOString(),
    expires_at: new Date(Date.now() - 60000).toISOString(), // Expired 60s ago
    idempotency_key: 'idemp-2',
  };
  const expiredRes = await mobileAgentService.validateAndExecuteAction(expiredPayload);
  if (!expiredRes.executed && expiredRes.status === 'EXPIRED') {
    passed++;
    console.log('✔ Test 3 Passed: Expired mobile action (60s TTL) rejected.');
  } else {
    console.error('✖ Test 3 Failed: Expired action was executed.');
  }

  // Test 4: Idempotency Key Deduplication Check
  total++;
  const validPayload: MobileActionPayload = {
    action_id: 'act-3',
    device_id: 'mob-dev-1',
    capability: 'BATTERY_STATUS',
    arguments: {},
    requested_by: 'ai_assistant',
    authorization: { authorized: true },
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 60000).toISOString(),
    idempotency_key: 'idemp-unique-3',
  };
  const exec1 = await mobileAgentService.validateAndExecuteAction(validPayload);
  const exec2 = await mobileAgentService.validateAndExecuteAction(validPayload); // Repeat same idempotency key
  if (exec1.executed && !exec2.executed && exec2.status === 'DUPLICATE') {
    passed++;
    console.log('✔ Test 4 Passed: Duplicate idempotency key blocked duplicate action execution.');
  } else {
    console.error('✖ Test 4 Failed: Idempotency deduplication failed.');
  }

  // Test 5: Emergency Stop Halt
  total++;
  mobileAgentService.triggerEmergencyStop();
  const emergencyPayload: MobileActionPayload = {
    action_id: 'act-4',
    device_id: 'mob-dev-1',
    capability: 'BATTERY_STATUS',
    arguments: {},
    requested_by: 'ai_assistant',
    authorization: { authorized: true },
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 60000).toISOString(),
    idempotency_key: 'idemp-unique-4',
  };
  const emergencyRes = await mobileAgentService.validateAndExecuteAction(emergencyPayload);
  mobileAgentService.resetEmergencyStop();
  if (!emergencyRes.executed && emergencyRes.status === 'EMERGENCY_STOPPED') {
    passed++;
    console.log('✔ Test 5 Passed: Emergency Stop halts active mobile actions.');
  } else {
    console.error('✖ Test 5 Failed: Emergency stop failed.');
  }

  console.log(`Module 36 Unit Tests Complete: ${passed} / ${total} passed.`);
  return passed === total;
}

if (typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).runMobileUnitTests = runMobileUnitTests;
}
