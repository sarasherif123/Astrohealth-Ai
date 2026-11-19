# System Architecture & Tech Stack: AstroHealth AI (V2.1 - Pre-Build Verified)

## 1. Tech Stack & Pinned Versions

### Backend (`/backend`)
- **Python:** `3.11+`
- **Web & ASGI:** `fastapi==0.115.0`, `uvicorn[standard]==0.30.6` (Run strictly with `--workers 1` for in-memory WebSocket and simulator state consistency)
- **Database:** `sqlalchemy==2.0.35`, `aiosqlite==0.20.0`, SQLite `3.45+` (`PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;`)
- **Validation:** `pydantic==2.9.2`, `pydantic-settings==2.5.2`
- **Auth & Crypto:** `PyJWT==2.9.0`, `bcrypt==4.0.1`
- **AI & Vector Math:** `google-genai>=1.10.0` (verified live via `/api/v1/health?live_check=true` in Block 0 spike), `numpy==2.1.2`
- **Testing:** `pytest==8.3.3`, `pytest-asyncio==0.24.0`, `httpx==0.27.2`

### Frontend (`/frontend`)
- **Framework:** Latest `next@14.2.x` (`>=14.2.25`), `react@18.3.1`, `typescript@5.6.2`
- **Styling & Visualization:** `tailwindcss@3.4.13`, `lucide-react@0.446.0`, `recharts@2.12.7`
- **Digital Twin:** Pure 2D interactive SVG component (`DigitalTwinSvg.tsx`) with 6 anatomical regions and CSS status glow.

## 2. Repository Directory Structure

```text
astrohealth-ai/
├── docs/
│   ├── 01_PRD.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_DATABASE_SCHEMA.md
│   ├── 04_API_SPEC.md
│   └── 05_TASKS.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, CORS, standard error envelope, routers
│   │   ├── config.py               # Path(__file__) resolved paths & production secret checks
│   │   ├── database.py             # Async SQLite engine with WAL & busy_timeout listener
│   │   ├── models.py               # All 7 SQLAlchemy ORM entities & composite indexes
│   │   ├── schemas.py              # All Pydantic v2 schemas & GeminiStructuredOutput
│   │   ├── crud.py                 # Async DB operations, 1000-row pruning & HMAC reports
│   │   ├── auth.py                 # PyJWT, bcrypt, RBAC, IDOR guards & RateLimiter
│   │   ├── rules.py                # 3-of-5 rolling window, escalation bypass & UTC normalizer
│   │   ├── rag_engine.py           # Pre-boost gate, stopword tokenizer, Gemini + Offline fallback
│   │   ├── simulator.py            # Seeded simulator, target_user_id, time_compression & WS hub
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth_router.py
│   │       ├── telemetry_router.py
│   │       └── clinical_router.py
│   ├── data/
│   │   ├── nasa_kb/
│   │   │   ├── nasa_hrp_sans_stenger_2017.md
│   │   │   ├── nasa_hrp_radiation_spe.md
│   │   │   ├── nasa_hrp_sleep_circadian.md
│   │   │   └── nasa_hrp_cardiovascular_hypoxia.md
│   │   ├── countermeasure_catalog.json
│   │   └── kb_index.json
│   ├── scripts/
│   │   └── seed_db_and_kb.py       # Non-destructive KB seeder (--reset & --overwrite-kb flags)
│   ├── tests/
│   │   └── test_v2_1_audit_fixes.py
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── trauma_protocols.fallback.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   └── tsconfig.json
├── run_dev.sh
└── README.md
```