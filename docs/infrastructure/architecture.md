# MAX Infrastructure & Production Deployment Architecture

## Overview
Module 38 provides provider-neutral, highly reliable, resource-conscious infrastructure to run MAX across local development, local production-like environments, personal remote servers, and future cloud environments.

## Core Principle
**Infrastructure is NOT intelligence.**
All AI reasoning, planning, memory engines, agent autonomy, and permission validations remain securely encapsulated within Python backend application modules (01–37). Infrastructure strictly provides compute, containerization, network routing, TLS termination, secret management, persistent storage, process isolation, health checks, and CI/CD pipelines.

## Target Architecture Topology

```
                         INTERNET
                            │
                          HTTPS
                            │
                            ▼
                    Reverse Proxy / Gateway (Caddy / Nginx)
                            │
                   ┌────────┴────────┐
                   │                 │
                   ▼                 ▼
              Web Frontend       Max API Gateway
             (Module 35/37)          │
                           ┌────────┼─────────┐
                           │        │         │
                           ▼        ▼         ▼
                         Redis   PostgreSQL  MinIO
                           │        │         │
                           └────────┼─────────┘
                                    │
                                    ▼
                              Max Backend
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
             Workers             Scheduler          AI Runtime
          (Module 12)           (Module 28)             │
                                             ┌──────────┴──────────┐
                                             ▼                     ▼
                                        Local Models        External Models
                                     (RTX 3050 / CPU)
```

## Client Topology
All client applications connect to the unified MAX API Gateway:
- **Desktop Application (Module 34)**: Tauri/Rust native client -> HTTPS/WSS -> Secure Proxy -> MAX API
- **Web Application (Module 35)**: React/Vite SPA -> HTTPS -> Caddy/Nginx -> MAX API
- **Mobile Application (Module 36)**: React Native iOS/Android -> HTTPS/WSS -> Reverse Proxy -> MAX API
- **Admin System Console (Module 37)**: React Enterprise Console -> HTTPS -> /admin/ -> MAX API

## Network Segmentation
Isolated Docker container networks ensure zero direct public exposure of internal storage or database services:
- **`max-public`**: Public reverse proxy network exposing ports 80/443.
- **`max-app`**: Internal application bridge connecting proxy, Web SPA, Admin Console, and MAX Backend.
- **`max-data`**: Isolated data bridge connecting MAX Backend, Worker, Scheduler, PostgreSQL (5432), Redis (6379), and MinIO (9000). Isolated from external internet routing.
