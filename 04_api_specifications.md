# API Endpoints & Contracts: AstroHealth AI (V2.1 - IDOR & Scenario Hardened)

Base URL: `http://localhost:8000/api/v1`  
Standard Error Envelope (all non-2xx responses):
```json
{
  "error": {
    "code": "FORBIDDEN_OWNERSHIP",
    "message": "Astronauts may only access their own medical records."
  }
}
```

## 1. Health & Live Gemini Smoke Test (`/health`)
- **Method & Route:** `GET /api/v1/health?live_check=false` (Public)
- **Success Response (`200 OK`):**
```json
{
  "status": "ok",
  "ai_provider_mode": "ONLINE_GEMINI",
  "live_model_verified": true,
  "model_detail": "gemini-2.5-flash",
  "kb_chunks_loaded": 8
}
```

## 2. Authentication (`/auth`)
- `POST /api/v1/auth/login` (Public, rate-limited: $10\text{ req/min/IP}$)
- `GET /api/v1/auth/me` (`ASTRONAUT`, `CMO`, `FLIGHT_SURGEON`)

## 3. Telemetry, Simulator & Alerts (`/telemetry`, `/alerts`)

### 3.1 Fetch Latest Telemetry & Region Statuses
- **Method & Route:** `GET /api/v1/telemetry/latest?user_id=<optional_target_id>&limit=30`
- **Auth & Ownership:** `ASTRONAUT` (may only access own `user_id`), `CMO`, `FLIGHT_SURGEON`.

### 3.2 Trigger / Stop Simulator Scenario
- **Method & Route:** `POST /api/v1/telemetry/simulate-scenario`
- **Auth & Ownership:** `ASTRONAUT` (own `user_id` only), `CMO` (any `target_user_id`).
- **Request Payload:**
```json
{
  "scenario": "SANS_OCULAR_AND_RADIATION_SPIKE",
  "target_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "time_compression": 1.0
}
```
*(Allowed `scenario` values: `"NOMINAL_BASELINE" | "SANS_OCULAR_AND_RADIATION_SPIKE" | "CIRCADIAN_FATIGUE_DRIFT" | "CARDIO_HYPERTENSION" | "STOP"`)*
- **Success Response (`200 OK`):**
```json
{
  "target_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "active_scenario": "SANS_OCULAR_AND_RADIATION_SPIKE",
  "status_level": "YELLOW",
  "alerts_triggered": 4
}
```

### 3.3 Acknowledge Anomaly Alert
- **Method & Route:** `PATCH /api/v1/alerts/{alert_id}/acknowledge`
- **Auth & Ownership:** `ASTRONAUT` (must own alert), `CMO`.

### 3.4 Authenticated WebSocket Telemetry Stream
- **Route:** `WS /ws/telemetry?token=<jwt_access_token>&user_id=<optional_target_id>`
- **Security:** Validates JWT, enforces `Origin` check (`http://localhost:3000`), and enforces ownership (`ASTRONAUT` cannot subscribe to another astronaut's `user_id`).

## 4. Clinical RAG Consultations (`/consultations`)
- `POST /api/v1/consultations` (`ASTRONAUT`, `CMO`, rate-limited: $6\text{ req/min/user}$)
- `GET /api/v1/consultations?user_id=<optional_target_id>` (`ASTRONAUT` own only; `CMO` and `FLIGHT_SURGEON` any crew member)

## 5. Countermeasure Tasks (`/tasks`)
- `GET /api/v1/tasks?user_id=<optional_target_id>` (`ASTRONAUT` own only; `CMO` any)
- `PATCH /api/v1/tasks/{task_id}/complete` (`ASTRONAUT` own only; `CMO` any)

## 6. Trauma Override Protocols (`/trauma-protocols`)
- `GET /api/v1/trauma-protocols` (**Public** — also exported to `frontend/public/trauma_protocols.fallback.json`)

## 7. Mission Control Sync & Integrity Verification (`/reports`)
- `POST /api/v1/reports/sync` (`ASTRONAUT` own only; `CMO` any `target_user_id`)
- `GET /api/v1/reports?user_id=<optional_target_id>` (`ASTRONAUT` scoped to own reports; `CMO` and `FLIGHT_SURGEON` crew-wide)
- `GET /api/v1/reports/{report_id}/verify` (`ASTRONAUT` must own `report.user_id`; `CMO` and `FLIGHT_SURGEON` crew-wide)