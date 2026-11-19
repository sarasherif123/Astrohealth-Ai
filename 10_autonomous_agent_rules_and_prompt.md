# Autonomous Agent Rules (`GEMINI.md` / `AGENTS.md`) & Zero-Interruption Prompt

Save Section 1 below as both `GEMINI.md` and `AGENTS.md` in the root of your project folder. Then copy and paste Section 2 directly into the Antigravity IDE chat window.

---

## 1. Save as `GEMINI.md` (and `AGENTS.md`) in Project Root

```markdown
# Autonomous Execution Rules for AstroHealth AI (V2.2)

You are an autonomous Senior Software Engineer executing a complete, pre-audited specification package located in `/docs`.

## Mandatory Operating Directives
1. **ZERO USER INTERRUPTIONS:** Do NOT ask the user for confirmation, clarification, or permission between steps. Do NOT ask "Should I proceed?" or "Would you like me to create the frontend now?". Execute every phase sequentially until the entire backend and frontend build and all tests pass.
2. **SINGLE SOURCE OF TRUTH:** Every file's exact code is already written and audited inside:
   - `/docs/06_BACKEND_RAG_AND_SEED_CODE.md`
   - `/docs/07_BACKEND_CORE_AND_ROUTERS.md`
   - `/docs/08_FRONTEND_COMPONENTS.md`
   - `/docs/09_CONFIGS_ENV_AND_RUNNERS.md`
   Transcribe those exact files into `/backend`, `/frontend`, and the workspace root without inventing conflicting schemas, routes, or field names.
3. **OFFLINE DETERMINISTIC TESTS:** Never call the live Gemini API inside `pytest`. All unit and security tests must run 100% offline.
4. **AUTOMATIC SELF-HEALING:** If any command (`pytest`, `seed_db_and_kb`, `tsc --noEmit`, or `npm run build`) reports an error, diagnose and fix the code immediately and re-run the verification command until it exits with code `0`.
```

---

## 2. Copy-Paste Master Prompt for Antigravity IDE (`Gemini 3.8 Flash Medium`)

Copy the block below and send it as your single message in Antigravity IDE:

```text
AUTONOMOUS FULL-BUILD MODE — DO NOT PAUSE OR ASK FOR CONFIRMATION AT ANY STEP.

Read `GEMINI.md` and all files inside `/docs` (`01_PRD.md` through `09_CONFIGS_ENV_AND_RUNNERS.md`). Your job is to build, seed, test, and verify the entire **AstroHealth AI V2.2** application end-to-end in one uninterrupted run without asking me any questions.

Execute the following steps in exact order:

STEP 1 — BACKEND CREATION:
- Create the `/backend` directory structure and write every file verbatim from `/docs/06_BACKEND_RAG_AND_SEED_CODE.md`, `/docs/07_BACKEND_CORE_AND_ROUTERS.md`, and `/docs/09_CONFIGS_ENV_AND_RUNNERS.md`:
  - `backend/requirements.txt`
  - `backend/pytest.ini`
  - `backend/.env.example` and copy it to `backend/.env`
  - `backend/scripts/__init__.py` and `backend/scripts/seed_db_and_kb.py`
  - `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/database.py`, `backend/app/models.py`, `backend/app/schemas.py`, `backend/app/rules.py`, `backend/app/rag_engine.py`, `backend/app/auth.py`, `backend/app/crud.py`, `backend/app/simulator.py`, `backend/app/main.py`
  - `backend/app/routers/__init__.py`, `backend/app/routers/auth_router.py`, `backend/app/routers/telemetry_router.py`, `backend/app/routers/clinical_router.py`
  - `backend/tests/__init__.py`, `backend/tests/test_v2_1_audit_fixes.py`, `backend/tests/test_api_security.py`

STEP 2 — BACKEND VENV, SEED & PYTEST VERIFICATION:
- Inside `/backend`, create a Python virtual environment (`.venv`), install all packages from `requirements.txt`, and run:
  `python -m scripts.seed_db_and_kb --reset --overwrite-kb --offline-embeddings`
- Run `pytest` inside `/backend`. If any test fails, fix the issue immediately and re-run `pytest` until 100% of tests in `test_v2_1_audit_fixes.py` and `test_api_security.py` pass.

STEP 3 — FRONTEND CREATION & BUILD VERIFICATION:
- Create the `/frontend` directory and write every file verbatim from `/docs/08_FRONTEND_COMPONENTS.md` and `/docs/09_CONFIGS_ENV_AND_RUNNERS.md`:
  - `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, `frontend/next.config.mjs`
  - `frontend/src/app/globals.css`, `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/app/login/page.tsx`
  - `frontend/src/types/astrohealth.ts`, `frontend/src/lib/apiClient.ts`, `frontend/src/hooks/useTelemetrySocket.ts`
  - `frontend/src/components/Navbar.tsx`, `frontend/src/components/TraumaOverrideModal.tsx`, `frontend/src/components/TelemetryCharts.tsx`, `frontend/src/components/DigitalTwinSvg.tsx`, `frontend/src/components/AnomalyAlertsFeed.tsx`, `frontend/src/components/RagDiagnosticsPanel.tsx`, `frontend/src/components/CountermeasureList.tsx`, `frontend/src/components/MissionSyncPanel.tsx`
- Inside `/frontend`, run `npm install`, then run `npx tsc --noEmit` and `npm run build`. Fix any TypeScript or build issues automatically until both commands succeed with exit code 0.

STEP 4 — ROOT RUNNERS & README:
- Create `run_dev.ps1`, `run_dev.sh`, and `README.md` in the project root from `/docs/09_CONFIGS_ENV_AND_RUNNERS.md`.
- Only reply to me AFTER `pytest`, `npx tsc --noEmit`, and `npm run build` have all passed 100%, and print a final summary of the test and build outputs.
```