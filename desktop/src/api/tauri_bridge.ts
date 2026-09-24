import { invoke } from "@tauri-apps/api/core";
import { BackendStatus, SystemInfo } from "../types";

export const isTauriEnvironment = (): boolean => {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
};

export const checkBackendStatusNative = async (): Promise<BackendStatus> => {
  if (isTauriEnvironment()) {
    try {
      return await invoke<BackendStatus>("check_backend_status");
    } catch (e) {
      console.warn("Tauri invoke error for check_backend_status:", e);
    }
  }

  // Fallback for standard browser execution or when Tauri invoke is unavailable
  try {
    const start = performance.now();
    const resp = await fetch("http://127.0.0.1:8000/api/v1/observability/health", {
      method: "GET",
      headers: { Accept: "application/json" },
    });
    const latency = Math.round((performance.now() - start) * 100) / 100;
    const ok = resp.ok;
    return {
      is_running: ok,
      endpoint: "http://127.0.0.1:8000",
      latency_ms: latency,
      status_code: resp.status,
      message: ok ? "MAX Backend Connected" : `HTTP ${resp.status}`,
    };
  } catch (err) {
    return {
      is_running: false,
      endpoint: "http://127.0.0.1:8000",
      latency_ms: 0,
      status_code: 0,
      message: "Backend Unreachable (http://127.0.0.1:8000)",
    };
  }
};

export const startBackendProcessNative = async (): Promise<string> => {
  if (isTauriEnvironment()) {
    return await invoke<string>("start_backend_process");
  }
  return "Browser environment: Cannot spawn local Python process directly.";
};

export const stopBackendProcessNative = async (): Promise<string> => {
  if (isTauriEnvironment()) {
    return await invoke<string>("stop_backend_process");
  }
  return "Browser environment: Cannot stop local process directly.";
};

export const toggleOverlayWindowNative = async (): Promise<boolean> => {
  if (isTauriEnvironment()) {
    return await invoke<boolean>("toggle_overlay_window");
  }
  return false;
};

export const getSystemInfoNative = async (): Promise<SystemInfo> => {
  if (isTauriEnvironment()) {
    try {
      return await invoke<SystemInfo>("get_system_info");
    } catch (e) {
      console.warn("Tauri invoke error for get_system_info:", e);
    }
  }

  return {
    os_name: "Windows 11",
    os_version: "10.0.22631",
    host_name: "MAX-DESKTOP",
    cpu_count: 12,
    total_memory_mb: 32768,
    used_memory_mb: 12450,
  };
};
