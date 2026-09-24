use serde::{Deserialize, Serialize};
use std::process::{Child, Command};
use std::sync::Mutex;
use sysinfo::System;
use tauri::{AppHandle, Manager, State};

#[derive(Debug, Serialize, Deserialize)]
pub struct BackendStatusResponse {
    pub is_running: bool,
    pub endpoint: String,
    pub latency_ms: f64,
    pub status_code: u16,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemInfoResponse {
    pub os_name: String,
    pub os_version: String,
    pub host_name: String,
    pub cpu_count: usize,
    pub total_memory_mb: u64,
    pub used_memory_mb: u64,
}

pub struct BackendProcessState {
    pub child: Mutex<Option<Child>>,
    pub endpoint: Mutex<String>,
}

#[tauri::command]
pub async fn check_backend_status(
    state: State<'_, BackendProcessState>,
) -> Result<BackendStatusResponse, String> {
    let endpoint = state.endpoint.lock().unwrap().clone();
    let health_url = format!("{}/api/v1/observability/health", endpoint);

    let start = std::time::Instant::now();
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .map_err(|e| e.to_string())?;

    match client.get(&health_url).send().await {
        Ok(resp) => {
            let latency = start.elapsed().as_secs_f64() * 1000.0;
            let status_code = resp.status().as_u16();
            let is_ok = resp.status().is_success();
            Ok(BackendStatusResponse {
                is_running: is_ok,
                endpoint,
                latency_ms: (latency * 100.0).round() / 100.0,
                status_code,
                message: if is_ok {
                    "MAX Backend Connected".to_string()
                } else {
                    format!("HTTP Status {}", status_code)
                },
            })
        }
        Err(e) => Ok(BackendStatusResponse {
            is_running: false,
            endpoint,
            latency_ms: 0.0,
            status_code: 0,
            message: format!("Backend Unreachable: {}", e),
        }),
    }
}

#[tauri::command]
pub async fn start_backend_process(
    state: State<'_, BackendProcessState>,
) -> Result<String, String> {
    let mut child_lock = state.child.lock().unwrap();
    if child_lock.is_some() {
        return Ok("Backend process already managed by Tauri client.".to_string());
    }

    let spawn_result = Command::new("python")
        .args(["-m", "max.main"])
        .spawn();

    match spawn_result {
        Ok(child) => {
            *child_lock = Some(child);
            Ok("MAX Python Backend process spawned successfully.".to_string())
        }
        Err(e) => Err(format!("Failed to spawn Python backend process: {}", e)),
    }
}

#[tauri::command]
pub async fn stop_backend_process(
    state: State<'_, BackendProcessState>,
) -> Result<String, String> {
    let mut child_lock = state.child.lock().unwrap();
    if let Some(mut child) = child_lock.take() {
        let _ = child.kill();
        Ok("MAX Python Backend process terminated.".to_string())
    } else {
        Ok("No managed backend process was active.".to_string())
    }
}

#[tauri::command]
pub async fn toggle_overlay_window(app_handle: AppHandle) -> Result<bool, String> {
    if let Some(window) = app_handle.get_webview_window("max-overlay") {
        let is_visible = window.is_visible().map_err(|e| e.to_string())?;
        if is_visible {
            window.hide().map_err(|e| e.to_string())?;
            Ok(false)
        } else {
            window.show().map_err(|e| e.to_string())?;
            window.set_focus().map_err(|e| e.to_string())?;
            Ok(true)
        }
    } else {
        Err("Overlay window 'max-overlay' not found.".to_string())
    }
}

#[tauri::command]
pub async fn get_system_info() -> Result<SystemInfoResponse, String> {
    let mut sys = System::new_all();
    sys.refresh_all();

    Ok(SystemInfoResponse {
        os_name: System::name().unwrap_or_else(|| "Windows".to_string()),
        os_version: System::os_version().unwrap_or_else(|| "10/11".to_string()),
        host_name: System::host_name().unwrap_or_else(|| "MAX-HOST".to_string()),
        cpu_count: sys.cpus().len(),
        total_memory_mb: sys.total_memory() / (1024 * 1024),
        used_memory_mb: sys.used_memory() / (1024 * 1024),
    })
}

pub fn run() {
    tauri::Builder::default()
        .manage(BackendProcessState {
            child: Mutex::new(None),
            endpoint: Mutex::new("http://127.0.0.1:8000".to_string()),
        })
        .invoke_handler(tauri::generate_handler![
            check_backend_status,
            start_backend_process,
            stop_backend_process,
            toggle_overlay_window,
            get_system_info
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
