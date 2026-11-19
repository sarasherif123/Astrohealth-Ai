# AstroHealth AI — Space Medical AI Emergency System & Health Platform

[![NASA Space Apps 2026](https://img.shields.io/badge/NASA-Space%20Apps%202026-00e5ff.svg)](https://www.spaceappschallenge.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646cff.svg)](https://vitejs.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-Async-003B57.svg)](https://www.sqlite.org/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB.svg)](https://www.python.org/)

> **PROTOTYPE CLINICAL DECISION-SUPPORT SYSTEM — FOR DEMO & MISSION SIMULATION USE ONLY — NOT CERTIFIED AS A PRIMARY MEDICAL DEVICE.**

AstroHealth AI is an integrated medical monitoring and spaceflight clinical decision-support platform designed for deep-space Artemis lunar missions and Mars transit operations. It addresses communication latencies of up to 20 minutes each way by delivering edge-first autonomous medical triage, interactive AI clinical consultations, real-time biosensor telemetry evaluation, and dedicated life-saving AI Emergency Simulations.

---

## 1. Project Requirements

### Programming Languages & Runtimes
- **Python:** Version `3.11` or `3.12` (Python 3.12 recommended).
- **Node.js:** Version `18.x`, `20.x`, or `22.x` (LTS recommended).
- **Package Managers:** `pip` (Python) and `npm` (Node.js).

### Core Frameworks & Libraries
- **Backend:**
  - `FastAPI 0.115.0` (High-performance async ASGI web framework)
  - `uvicorn 0.30.6` (ASGI web server)
  - `SQLAlchemy 2.0.35` (Async ORM)
  - `aiosqlite 0.20.0` (Asynchronous SQLite driver)
  - `pydantic 2.9.2` & `pydantic-settings 2.5.2` (Data validation and configuration management)
  - `PyJWT 2.9.0` (JSON Web Token authentication)
  - `bcrypt 4.0.1` (Password hashing)
  - `google-genai >= 1.10.0` (Google Gemini AI SDK for online clinical synthesis)
  - `numpy 2.1.2` (Deterministic cosine similarity and embedding calculations)
  - `pytest 8.3.3` & `pytest-asyncio 0.24.0` (Automated backend test suite)
- **Frontend:**
  - `React 18.3.1` (UI component library)
  - `Vite 5.4.x` (Fast frontend bundler and development server)
  - Native SVG graphic rendering (Zero external chart bloat)

### Database & Storage
- **Database:** SQLite with asynchronous WAL mode (`astrohealth.db`), automatically created and managed by SQLAlchemy.
- **Knowledge Base:** NASA Human Research Program (HRP) markdown reference index (`backend/data/kb_index.json`).

### Network & Ports
- **Frontend URL:** `http://localhost:3000` (or `http://127.0.0.1:3000`)
- **Backend API URL:** `http://localhost:8000` (or `http://127.0.0.1:8000`)
- **WebSocket Telemetry Stream:** `ws://127.0.0.1:8000/ws/telemetry`

---

## 2. Project Structure

```
astrohealth/
├── backend/                             # PROJECT 2 — Backend (Source of Truth)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── auth.py                      # JWT authentication, password hashing & rate limiting
│   │   ├── config.py                    # Environment settings and CORS configuration
│   │   ├── crud.py                      # Telemetry ingestion, window evaluators & HMAC signatures
│   │   ├── database.py                  # Async SQLAlchemy engine and session factory
│   │   ├── emergency_scenarios.py       # NASA emergency scenarios catalog & clinical metrics
│   │   ├── main.py                      # FastAPI application, exception handlers & WebSocket endpoint
│   │   ├── models.py                    # SQLite database models (User, Telemetry, Alert, Tasks, etc.)
│   │   ├── rag_engine.py                # Dual-mode RAG engine (GeminiProvider + OfflineRulesProvider)
│   │   ├── rules.py                     # 3-of-5 rolling window anomaly rules & threshold engine
│   │   ├── schemas.py                   # Pydantic request and response schemas
│   │   ├── simulator.py                 # Telemetry simulator hub and WebSocket broadcaster
│   │   └── routers/
│   │       ├── auth_router.py           # /auth/login, /auth/me, /auth/users, /auth/switch
│   │       ├── clinical_router.py       # /consultations, /clinical/chat, /emergency/simulate, /tasks, /reports
│   │       └── telemetry_router.py      # /telemetry, /telemetry/latest, /telemetry/simulate-scenario
│   ├── data/
│   │   ├── countermeasure_catalog.json  # NASA prescribed countermeasure protocols
│   │   ├── kb_index.json                # Pre-indexed NASA HRP knowledge base chunks
│   │   └── nasa_kb/                     # Raw NASA HRP evidence report documentation
│   ├── scripts/
│   │   ├── seed_db_and_kb.py            # Database initialization and KB indexer script
│   │   ├── smoke_test.py                # Automated backend verification script
│   │   └── live_test.py                 # Live API integration test suite
│   ├── tests/                           # Pytest automated test suite (18 unit/integration tests)
│   ├── venv/                            # Python virtual environment
│   ├── .env.example                     # Backend environment template
│   └── requirements.txt                 # Backend Python dependencies
│
├── frontend/                            # PROJECT 1 — Frontend (Main User Interface)
│   ├── src/
│   │   ├── assets/
│   │   │   └── body.jpg                 # Digital twin anatomical body model
│   │   ├── components/
│   │   │   ├── Charts.jsx               # High-performance SVG line charts and sparklines
│   │   │   └── Icon.jsx                 # Lightweight SVG icon collection
│   │   ├── api.js                       # Frontend API client communicating with backend
│   │   ├── data.js                      # Navigation, body region mapping, and nominal baseline waves
│   │   ├── index.css                    # NASA Space Theme stylesheet (Deep space navy, cyan accents)
│   │   ├── App.jsx                      # Main application component, navigation, and emergency UI
│   │   └── main.jsx                     # React entry point
│   ├── public/
│   │   └── trauma_protocols.fallback.json # Cached emergency trauma checklists for offline zero-auth access
│   ├── index.html                       # HTML template
│   ├── package.json                     # Frontend dependencies & npm scripts
│   ├── vite.config.js                   # Vite configuration (port 3000, API proxy)
│   └── .env.example                     # Frontend environment template
│
└── README.md                            # Complete project setup and execution guide
```

---

## 3. Environment Setup

### Backend Configuration (`backend/.env`)
Copy `backend/.env.example` to `backend/.env`:

```ini
PROJECT_NAME="AstroHealth AI"
ENV="development"
DATABASE_URL="sqlite+aiosqlite:///./astrohealth.db"
JWT_SECRET_KEY="dev-only-mars-transit-jwt-secret-override-in-prod"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
MISSION_HMAC_SECRET="dev-only-mission-control-hmac-secret-2026"
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:5173","http://127.0.0.1:5173"]

# Leave GEMINI_API_KEY empty to run 100% offline with OfflineRulesProvider,
# or paste your Google AI Studio API key to enable live ONLINE_GEMINI synthesis:
GEMINI_API_KEY=""
GEMINI_GENERATION_MODEL="gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL="gemini-embedding-001"
EMBEDDING_DIMENSION=768
MAX_TELEMETRY_ROWS_PER_USER=1000
```

> **Note on AI Operation:** If `GEMINI_API_KEY` is not provided, the platform automatically runs in `OFFLINE_FALLBACK` mode. All medical chats and emergency simulations synthesize grounded clinical guidance directly from the built-in NASA HRP Knowledge Base (`backend/data/nasa_kb`). No paid account or external internet access is required.

### Frontend Configuration (`frontend/.env`)
Copy `frontend/.env.example` to `frontend/.env`:

```ini
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_WS_URL=ws://127.0.0.1:8000/ws/telemetry
```

---

## 4. Installation Instructions

### Step 1: Install Backend Dependencies
Open a terminal in the project root:

```bash
# Navigate to backend
cd backend

# Create a Python virtual environment (if not already created)
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On macOS/Linux:
source venv/bin/activate

# Install required Python packages
pip install -r requirements.txt
```

### Step 2: Seed Database and Knowledge Base
Initialize the SQLite database with synthetic crew profiles (Mark Watney, Melissa Lewis, Elena Cruz), trauma checklists, and NASA HRP index chunks:

```bash
# Ensure virtual environment is activated and PYTHONPATH includes the backend folder:
# On Windows (PowerShell):
$env:PYTHONPATH = "."
python scripts\seed_db_and_kb.py --offline-embeddings --reset

# On macOS/Linux:
PYTHONPATH=. python scripts/seed_db_and_kb.py --offline-embeddings --reset
```

### Step 3: Install Frontend Dependencies
In a new terminal window:

```bash
# Navigate to frontend
cd frontend

# Install Node modules
npm install
```

---

## 5. Running the Project

Both the backend and frontend must run concurrently. You will need **two terminal tabs/sessions**.

### Terminal 1 — Start Backend Server (Port 8000)

```bash
# In the 'backend' directory with virtual environment activated:
# Windows (PowerShell):
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1

# macOS/Linux:
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

*Successful backend startup will display:*
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Terminal 2 — Start Frontend Development Server (Port 3000)

```bash
# In the 'frontend' directory:
npm run dev
```

*Successful frontend startup will display:*
```
  VITE v5.4.21  ready in 600 ms

  ➜  Local:   http://127.0.0.1:3000/
  ➜  Network: use --host to expose
```

### Access the Application
Open your web browser and navigate to:
👉 **`http://127.0.0.1:3000/`** (or **`http://localhost:3000/`**)

---

## 6. Running in Different IDEs

### Running in Visual Studio Code (VS Code)
1. Open VS Code: `File -> Open Folder...` and select the `astrohealth` root directory.
2. Open the integrated terminal (`Ctrl + ~` or ``Ctrl + ` ``).
3. **Split the terminal** into two panes (`Ctrl + Shift + 5` or click the split icon in the terminal tab):
   - **Pane 1 (Backend):**
     ```powershell
     cd backend
     .\venv\Scripts\Activate.ps1
     $env:PYTHONPATH = "."
     python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
     ```
   - **Pane 2 (Frontend):**
     ```powershell
     cd frontend
     npm run dev
     ```
4. Click on `http://127.0.0.1:3000/` in the terminal to view the application.

### Running in PyCharm / JetBrains WebStorm
1. Open PyCharm and select `Open` on the `astrohealth` folder.
2. In `Settings -> Project: astrohealth -> Python Interpreter`, select the existing interpreter located at `backend/venv/Scripts/python.exe` (or `backend/venv/bin/python`).
3. Create a Run Configuration for the Backend:
   - Type: `Python`
   - Module name: `uvicorn`
   - Parameters: `app.main:app --host 127.0.0.1 --port 8000 --workers 1`
   - Working directory: `<project_root>/backend`
   - Environment variables: `PYTHONPATH=.`
4. For the Frontend, open PyCharm's built-in Terminal:
   ```bash
   cd frontend
   npm run dev
   ```

---

## 7. Key Features & How to Test Them

### Feature 1: NASA Space Theme Medical Dashboard (`Overview`)
- **Visuals:** Sleek deep space navy background (`#060d19`), dark blue card panels (`#0d1829`), soft cyan/electric blue accents (`#00e5ff`), and subtle glowing borders.
- **Vitals Telemetry:** Live KPIs for Heart Rate, Blood Oxygen (SpO2), Body Temperature, Sleep Quality Score, and Radiation Dosimetry with animated sparklines.
- **Cardiovascular & Sleep Charts:** Real-time dual-line SVG telemetry graphs.
- **Digital Twin:** Anatomical body map with real-time status levels across 6 bodily systems.
- **Active Anomaly Feed:** Click **Acknowledge** on any active anomaly alert to record acknowledgment in the database.

### Feature 2: Space Medical AI Emergency Simulation System (`Emergency Protocols`)
Click **Emergency Protocols** in the sidebar:
1. **Select Target Astronaut:** Choose an astronaut from the dropdown manifest (e.g. Cmdr. Mark Watney, Dr. Melissa Lewis, or registered crew).
2. **Select Predefined Emergency Scenario:**
   - Acute Chest Pain & Cardiovascular Decompensation
   - Acute Respiratory Distress & Airway Impairment
   - Acute Hypoxia & Cabin Oxygen Depletion
   - Acute Decompression Sickness (DCS / Bends)
   - Solar Particle Event (SPE) Acute Radiation Overexposure
   - Acute Syncope / Sudden Loss of Consciousness
   - Severe Neuro-Vestibular Disorientation & Space Motion Sickness
   - Acute Hypovolemia & Severe Dehydration
3. **Enter Custom Symptoms:** (Optional) Add free-text observations in natural language (e.g., *"Pain radiating down left arm, cold diaphoresis, feeling dizzy"*).
4. **Click "Start Emergency Simulation":**
   - The system executes real backend AI analysis (`/api/v1/emergency/simulate`).
   - Biosensor telemetry jumps immediately to emergency levels.
   - Anomaly alerts trigger with real-time audio/visual alert badges.
   - Outputs:
     - **Emergency Severity:** `CRITICAL` / `HIGH` / `MODERATE` with pulsing status glow.
     - **Grounded Medical Assessment:** Aerospace clinical analysis citing NASA flight protocols.
     - **Reported Symptoms:** Consolidated natural language indicators.
     - **Possible Medical Concerns:** Distinctly identified clinical concerns (differentiated from confirmed diagnoses).
     - **Step-by-Step Response Instructions:** Sequenced stabilization checklist (restraint grid anchoring, 100% O2, ECG lead check).
     - **Safety Warnings:** Life-safety precautions (e.g., avoiding nitrate administration with low BP, preventing microgravity CPR recoil).
     - **Monitoring Instructions & Ground Medical Support Recommendations.**
     - **NASA Citations & Materialized Countermeasure Tasks.**
5. **Reset Simulation:** Click **Reset / Nominal Baseline** to return astronaut telemetry to nominal green status.

### Feature 3: Interactive AI Medical Assistant (`AI Medical Assistant`)
Click **AI Medical Assistant** in the sidebar:
1. Type free-text space medicine questions:
   - *"I feel sick and my heart rate seems elevated."*
   - *"I have a severe headache and blurred vision."*
   - *"An astronaut is experiencing chest pain."*
   - *"What should we do if a crew member loses consciousness?"*
   - *"Explain the symptoms of hypoxia."*
   - *"What medical risks are associated with long-duration microgravity?"*
2. The AI maintains conversational context across turns, answers natural language questions, evaluates clinical severity, suggests immediate actions, and provides verified NASA HRP citations.
3. Click the interactive follow-up question pills to rapidly continue the diagnostic interview.

### Feature 4: Countermeasure Schedule (`Countermeasure Schedule`)
- Displays real treatment tasks stored in the SQLite database (e.g., LBNP sessions, SSLA 460nm blue light alignment, low-sodium rations, antioxidant hydration).
- Click **Mark Done** to patch task status (`PATCH /api/v1/tasks/{id}/complete`).

### Feature 5: Trauma Override ("Red Button")
- Click the red **Trauma Override** button on the Overview page or in the navigation.
- Instantly opens zero-auth emergency checklists with step-by-step procedures for acute hemorrhage, cabin depressurization, and chemical ocular washout.
- Cached locally in memory and browser storage so checklists load in `<10ms` even if backend connectivity is completely severed.

### Feature 6: Mission Control Sync & Cryptographic Integrity (`Mission Control Sync`)
- Click **Sync now** or **Generate Sync Report** to generate a telemetry snapshot signed with HMAC-SHA256.
- Click **Verify Hash** to verify cryptographic integrity.
- Click **Tamper Test** to inject a simulated bit-flip into the database record and click **Verify Hash** to observe immediate cryptographic tamper detection.

### Feature 7: Crew Manifest & Astronaut Switcher
- Click the astronaut avatar initials or the **Crew Switcher** button in the header.
- Switch between active astronauts (Mark Watney, Melissa Lewis, Elena Cruz) without retyping passwords.
- Register a new astronaut by entering their full name and role; initial baseline vitals and telemetry stream will be created automatically.

---

## 8. Automated Testing

To run the complete automated test suite (18 unit and integration tests covering security, audit compliance, RAG, clinical chat, and emergency simulation):

```bash
# In the 'backend' directory with virtual environment activated:
# Windows (PowerShell):
$env:PYTHONPATH = "."
python -m pytest tests/

# macOS/Linux:
PYTHONPATH=. pytest tests/
```

To run the live server verification script while the backend is running:

```bash
python scripts/live_test.py
```

---

## 9. Troubleshooting Guide

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Port 8000 already in use** | An existing Uvicorn or Python process is running on port 8000. | On Windows: `Get-Process python \| Stop-Process -Force` or run Uvicorn on a different port like `--port 8001` and update `frontend/.env`. |
| **Port 3000 already in use** | Another frontend server or Node process is using port 3000. | Vite will automatically prompt to use another port, or specify `--port 3001` in `frontend/package.json`. Remember to add the new port to `ALLOWED_ORIGINS` in `backend/app/config.py`. |
| **`No module named 'app'`** | Python cannot find the backend package root. | Ensure `PYTHONPATH` includes the `backend` directory: `$env:PYTHONPATH = "."` in PowerShell before launching Python commands. |
| **CORS error in browser console** | Frontend origin is blocked by backend CORS policy. | `backend/app/config.py` allows `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:5173`, and `http://127.0.0.1:5173`. Ensure you are opening one of these URLs. |
| **AI responses say `OFFLINE_FALLBACK`** | No Gemini API key configured in `.env`. | This is expected and normal! AstroHealth AI includes a built-in offline clinical rules provider that synthesizes responses from the local NASA HRP knowledge base without external internet. To use Gemini, add `GEMINI_API_KEY="your-key"` to `backend/.env`. |
| **Database locked error** | Multiple background processes writing to SQLite simultaneously. | The backend uses asynchronous WAL mode with a single worker (`--workers 1`). Do not run multiple backend servers against the same `astrohealth.db` file. |

---

## 10. Verification Checklist

- [x] Backend starts cleanly on `http://127.0.0.1:8000` with 0 startup errors.
- [x] Frontend starts cleanly on `http://127.0.0.1:3000/`.
- [x] Health check endpoint `GET /api/v1/health` returns `status: "ok"`.
- [x] Authentication & crew manifest `GET /api/v1/auth/users` loads real astronaut profiles.
- [x] Real-time telemetry `GET /api/v1/telemetry/latest` streams live vitals.
- [x] AI Medical Chat `POST /api/v1/clinical/chat` answers free-text inquiries with NASA citations.
- [x] AI Emergency Simulation `POST /api/v1/emergency/simulate` returns structured emergency output.
- [x] Countermeasure Schedule `GET /api/v1/tasks` supports task completion.
- [x] Trauma Override `GET /api/v1/trauma-protocols` opens offline emergency checklists.
- [x] Mission Control Sync `POST /api/v1/reports/sync` verifies HMAC-SHA256 signatures.
- [x] Space theme preserves 100% of original layout with professional futuristic NASA aesthetic.

---

**Developed for the NASA Space Apps Challenge 2026.**
*Healthy Crew. Successful Mission.*
