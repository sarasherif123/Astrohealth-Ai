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

