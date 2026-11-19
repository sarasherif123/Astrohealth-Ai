# V2.2 Missing Glue Configs, Environment Files, Runners & Demo README

This file contains every remaining configuration file required so the AI coding agent never has to guess or ask questions about Tailwind, PostCSS, Next.js config, `.env` formatting, or startup scripts on Windows/Linux/macOS:

1. `backend/.env.example`
2. `frontend/tailwind.config.ts`
3. `frontend/postcss.config.js`
4. `frontend/next.config.mjs`
5. `frontend/src/app/globals.css`
6. `run_dev.ps1` (Windows PowerShell One-Command Runner)
7. `run_dev.sh` (Linux / macOS / Git Bash One-Command Runner)
8. `README.md` (Full Architecture Overview & 3-Minute NASA Judges Demo Script)

---

## 1. `backend/.env.example`

Copy this file to `backend/.env` as well during setup so the backend runs out-of-the-box in offline fallback mode (or online mode if `GEMINI_API_KEY` is provided):

```env
PROJECT_NAME="AstroHealth AI"
ENV="development"
DATABASE_URL="sqlite+aiosqlite:///./astrohealth.db"
JWT_SECRET_KEY="dev-only-mars-transit-jwt-secret-override-in-prod"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
MISSION_HMAC_SECRET="dev-only-mission-control-hmac-secret-2026"
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Leave GEMINI_API_KEY empty to run 100% offline with OfflineRulesProvider,
# or paste a Google AI Studio key to enable ONLINE_GEMINI mode:
GEMINI_API_KEY=""
GEMINI_GENERATION_MODEL="gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL="gemini-embedding-001"
EMBEDDING_DIMENSION=768
MAX_TELEMETRY_ROWS_PER_USER=1000
```

---

## 2. `frontend/tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
```

---

## 3. `frontend/postcss.config.js`

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

---

## 4. `frontend/next.config.mjs`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

---

## 5. `frontend/src/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color-scheme: dark;
}

body {
  background-color: #020617;
  color: #f1f5f9;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
```

---

## 6. `run_dev.ps1` (Windows PowerShell One-Command Runner)

```powershell
$ErrorActionPreference = "Stop"

Write-Host "=== AstroHealth AI V2.2: Starting Local Mission Control Stack ===" -ForegroundColor Cyan

# 1. Backend Setup & Seed
Push-Location backend
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Seeding SQLite DB and NASA HRP Knowledge Base Index..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m scripts.seed_db_and_kb --reset --overwrite-kb --offline-embeddings

Write-Host "Starting FastAPI Backend on http://localhost:8000 (workers=1)..." -ForegroundColor Green
$backendProc = Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" -ArgumentList "app.main:app --host 0.0.0.0 --port 8000 --workers 1" -PassThru
Pop-Location

# 2. Frontend Setup & Start
Push-Location frontend
if (-not (Test-Path "node_modules")) {
    npm install
}
Write-Host "Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
try {
    npm run dev
} finally {
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force
    }
    Pop-Location
}
```

---

## 7. `run_dev.sh` (Linux / macOS / Git Bash Runner)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== AstroHealth AI V2.2: Starting Local Mission Control Stack ==="

cd backend
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

python -m scripts.seed_db_and_kb --reset --overwrite-kb --offline-embeddings

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &
BACKEND_PID=$!
cd ..

trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

cd frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev
```

---

## 8. `README.md`

```markdown
# AstroHealth AI (V2.2) — Autonomous Space Health Monitoring Platform

> **CLINICAL DECISION-SUPPORT PROTOTYPE — SYNTHETIC DEMO DATA ONLY — NOT A CERTIFIED MEDICAL DEVICE.**

AstroHealth AI is an edge-first clinical decision-support prototype built for the **NASA Space Apps Challenge 2026 (Health-Monitoring Software for Astronauts on Space Missions)**. It addresses deep-space communication latencies of up to 20 minutes each way during Artemis lunar and Mars transit missions.

## Key Engineering Highlights
1. **Continuous 2-Second Telemetry & 3-of-5 Rolling Window Engine:** Evaluates wearable streams (Astroskin ECG/BP/SpO2, Actiwatch sleep score, fNIRS cognitive fatigue, and shielded habitat dosimetry) against personalized crew baselines with a 300-second cooldown and immediate `YELLOW -> RED` escalation bypass.
2. **Dual-Mode RAG Engine (`GeminiProvider` + `OfflineRulesProvider`):** Uses Google GenAI structured outputs when online and automatically falls back to deterministic local retrieval when offline, enforcing pre-boost similarity gating, citation verification, and allowlisted countermeasure materialization.
3. **Interactive 2D SVG Digital Twin:** Driven in real time by WebSocket `region_statuses` across 6 anatomical systems.
4. **Zero-Latency Trauma Override ("Red Button"):** Publicly cached in memory, `localStorage`, and `trauma_protocols.fallback.json` with Web Speech API voice readout so emergency checklists open in `<10ms` even offline or with an expired JWT.
5. **HMAC-SHA256 Canonical Mission Control Sync & Tamper Detection:** Generates cryptographically signed medical digests with a live tamper-verification demo.

## Security & Architecture Notes
- **Single-Worker Requirement:** Always run Uvicorn with `--workers 1` so in-memory WebSocket subscriptions and the background telemetry simulator share state deterministically.
- **WebSocket Token Note:** For local hackathon simplicity, `/ws/telemetry?token=<jwt>` passes the JWT in the query string (which may appear in local server access logs). Production deployments should exchange the JWT for a single-use short-lived ticket token.
- **Knowledge Base Provenance:** All files in `backend/data/nasa_kb/` are paraphrased prototype summaries based on public NASA Human Research Program (HRP) Evidence Reports (Stenger et al., 2017; Carnell et al., 2016; Flynn-Evans et al., 2016) with illustrative section/page numbers.

## Quick Start
### Windows (PowerShell)
```powershell
.\run_dev.ps1
```
### Linux / macOS / Git Bash
```bash
chmod +x run_dev.sh && ./run_dev.sh
```

## 3-Minute Hackathon Pitch & Live Demo Script
1. **0:00 - 0:40 (The Deep-Space Latency Problem & Live Telemetry):** Log in as **Cmdr. Mark Watney**. Show the 2-second live WebSocket charts and green 2D SVG Digital Twin.
2. **0:40 - 1:25 (Golden Scenario Injection & Proactive Alerts):** Select **"Scenario: SANS + Radiation Spike (4 YELLOW)"** in the top navbar. Watch the Digital Twin illuminate `OCULAR_EYES`, `BRAIN_NEURO`, `CARDIOVASCULAR`, and `SYSTEMIC` in yellow and emit 4 proactive micro-interventions with NASA HRP citations.
3. **1:25 - 2:10 (Grounded RAG Consultation & Allowlisted Tasks):** Click the **Ocular / Visor** region on the Digital Twin and run the SANS symptom query. Highlight the **Protocol Retrieval Match %**, the verified NASA HRP citation card with its provenance badge, and the automatically scheduled **LBNP (`CM_LBNP_01`)** and **Low-Sodium (`CM_LOW_SODIUM_02`)** tasks from the allowlisted catalog.
4. **2:10 - 2:40 (Zero-Latency Trauma Override):** Click the red **TRAUMA OVERRIDE** button. Show instant checklist rendering and click **Read Aloud (Web Speech)**.
5. **2:40 - 3:00 (Earth Sync & Tamper Detection):** Click **Generate Signed Digest**, click **Verify HMAC** (`INTEGRITY VERIFIED`), then click **Tamper Demo** to show immediate cryptographic tamper detection (`TAMPER DETECTED!`).
```