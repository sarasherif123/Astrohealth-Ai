# Bug fixes
1. backend/app/rag_engine.py  - chat keyword matching now whole-word regex ("seems" no longer matches "see"); "loses consciousness" handled.
2. backend/app/crud.py        - flush telemetry reading before inserting alerts (FK IntegrityError whenever an alert fired).
3. backend/app/routers/clinical_router.py - unknown scenario_id now returns 400 INVALID_SCENARIO (was silently CHEST_PAIN).
4. frontend/src/App.jsx       - telemetry poller re-armed per selected astronaut (stale closure); stored session validated via /auth/me, cleared on 401/404.
5. frontend/src/api.js        - Trauma protocols: network -> localStorage cache -> bundled fallback JSON; errors carry .status.
6. backend/tests/test_emergency_and_chat.py - 3 regression tests added (21 total).
