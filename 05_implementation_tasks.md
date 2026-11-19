# Step-by-Step Implementation Plan: AstroHealth AI (V2.1 - Pre-Build Verified)

## PRE-BUILD CHECKLIST & AGENT RULES
1. **One task at a time.** Do not start the next task until the current task's **"Done When"** check passes.
2. **Fresh Anomaly Engine per test.** Always call `create_anomaly_engine()` in unit tests so cooldown state never leaks across tests.
3. **Never overwrite KB edits.** Run `python -m scripts.seed_db_and_kb` without `--overwrite-kb` during normal operation so manual NASA text updates are preserved.
4. **Never call live Gemini in unit tests.** Use `GET /api/v1/health?live_check=true` once in Block 0 to verify the live model, and mock `LLMProvider` in `pytest`.

---

## Block 0: Environment Spike & Live Model Verification (Hours 0-2)
- [ ] **Task 0.1:** Install `/backend/requirements.txt` (`fastapi==0.115.0`, `uvicorn[standard]==0.30.6`, `sqlalchemy==2.0.35`, `aiosqlite==0.20.0`, `pydantic==2.9.2`, `pydantic-settings==2.5.2`, `PyJWT==2.9.0`, `bcrypt==4.0.1`, `google-genai>=1.10.0`, `numpy==2.1.2`, `pytest==8.3.3`, `pytest-asyncio==0.24.0`, `httpx==0.27.2`).
- [ ] **Task 0.2:** Implement `backend/app/config.py`, `backend/app/database.py`, `backend/app/models.py`, and `backend/app/schemas.py`.
- **Done When:** `GET /api/v1/health?live_check=true` reports the active provider mode cleanly.

## Block 1: Knowledge Base, Catalog & Golden Verification Suite (Hours 2-7)
- [ ] **Task 1.1:** Implement `backend/app/rules.py`, `backend/app/rag_engine.py`, and `backend/scripts/seed_db_and_kb.py`.
- [ ] **Task 1.2:** Run `python -m scripts.seed_db_and_kb --reset --offline-embeddings` from `/backend` to generate the 4 NASA KB files, `countermeasure_catalog.json`, `kb_index.json`, `frontend/public/trauma_protocols.fallback.json`, and SQLite tables.
- [ ] **Task 1.3:** Run `pytest tests/test_v2_1_audit_fixes.py`.
- **Done When:** All 4 golden tests in `test_v2_1_audit_fixes.py` pass (`SANS_OCULAR_AND_RADIATION_SPIKE` fires exact $4$ alerts, single-packet breach returns `GREEN`, `YELLOW` to `RED` escalation bypasses cooldown, and out-of-domain queries trigger `DETERMINISTIC_REFUSAL`).

## Block 2: Core Backend CRUD, Auth/IDOR, Simulator & Routers (Hours 7-22)
- [ ] **Task 2.1:** Implement `backend/app/auth.py`, `backend/app/crud.py`, and `backend/app/simulator.py` (with `target_user_id`, `time_compression`, and $1000$-row retention pruning).
- [ ] **Task 2.2:** Implement `backend/app/routers/auth_router.py`, `backend/app/routers/telemetry_router.py`, `backend/app/routers/clinical_router.py`, and `backend/app/main.py`.
- **Done When:** All REST endpoints and `/ws/telemetry` enforce ownership checks and HMAC report verification returns `{"verified": true}`.

## Block 3: Next.js Frontend MVP & End-to-End Integration (Hours 22-42)
- [ ] **Task 3.1:** Initialize `/frontend` (`next@^14.2.25`), run `npm audit`, and build `apiClient.ts` + `useTelemetrySocket.ts`.
- [ ] **Task 3.2:** Build `Navbar.tsx`, `TraumaOverrideModal.tsx` (backed by `trauma_protocols.fallback.json` + `window.speechSynthesis`), `DigitalTwinSvg.tsx`, `TelemetryCharts.tsx`, `AnomalyAlertsFeed.tsx`, `RagDiagnosticsPanel.tsx` (displaying **"Protocol Retrieval Match"**), `CountermeasureList.tsx`, and `MissionSyncPanel.tsx` (built last).
- **Done When:** `npx tsc --noEmit` passes and `./run_dev.sh` launches the full demo flow.