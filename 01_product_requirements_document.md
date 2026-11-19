# Product Requirements Document (PRD): AstroHealth AI (V2.1 - Pre-Build Verified)

## 1. Project Overview & Regulatory Disclaimer
- **Project Name:** AstroHealth AI (Autonomous & Adaptive Space Health Monitoring Platform)
- **Core Value Proposition:** An offline-capable, edge-first clinical decision-support prototype for astronauts on deep-space missions (Artemis and Mars transit) where Earth communication incurs up to 20-minute one-way latency. AstroHealth AI ingests wearable telemetry streams, evaluates multi-packet rolling windows against personalized astronaut baselines, visualizes anatomical risk on an interactive 2D SVG Digital Twin, provides zero-latency cached emergency checklists, and synthesizes clinical consultations using a dual-mode RAG engine (`GeminiProvider` online stand-in for an onboard model + `OfflineRulesProvider` deterministic fallback) grounded in NASA Human Research Program (HRP) themes.
- **Mandatory Medical Disclaimer:** The UI must display a persistent top banner: `"CLINICAL DECISION-SUPPORT PROTOTYPE -- SYNTHETIC DEMO DATA ONLY -- NOT A CERTIFIED MEDICAL DEVICE."`
- **Knowledge Base Provenance Policy:** All files in `backend/data/nasa_kb/` carry an explicit `# PROVENANCE:` header stating they are paraphrased prototype summaries grounded in named NASA HRP Evidence Reports, and every rule `citation_source` in `rules.py` maps 1-to-1 to an indexed chunk in `kb_index.json`.

## 2. Target Users & Strict RBAC / Ownership Model
1. **`ASTRONAUT` (Crew Member):** Views personal telemetry, acknowledges personal anomaly alerts, submits symptom consultations for their own Digital Twin, completes assigned countermeasure tasks, views/verifies only their own sync reports, and triggers Trauma Override. Passing any other crew member's `user_id` returns `403 FORBIDDEN_OWNERSHIP`.
2. **`CMO` (Crew Medical Officer):** Full read/write access to crew-wide telemetry, alerts, consultations, scenario simulation controls (`target_user_id`), and generates HMAC-SHA256 integrity-signed medical digests for Earth sync.
3. **`FLIGHT_SURGEON` (Earth Mission Control):** Read-only access to crew-wide telemetry, consultations, and `GET /api/v1/reports` + `GET /api/v1/reports/{id}/verify` to validate incoming deep-space digests.

## 3. Deterministic Anomaly Detection & Rolling-Window Rules
- **Strict 3-of-5 Windowing Contract:** Telemetry arrives every 2 seconds. Status transitions and alerts evaluate the **last 5 packets** for a user. The engine never fires if fewer than 3 packets exist; a rule triggers only when **at least 3 of the last 5 packets** breach the threshold.
- **Alert Cooldown & Escalation Bypass:** Each `(user_id, rule_id)` pair enforces a **300-second (5-minute) cooldown** based on packet UTC timestamps before firing another alert at the same severity. However, if a rule escalates from `YELLOW` to `RED`, the cooldown is bypassed immediately.
- **Telemetry Retention Pruning:** SQLite retains at most the latest $1000$ telemetry rows per user to prevent unbounded growth.
- **Metric Definitions & Threshold Matrix:**

| Metric (`telemetry_readings`) | Unit / Definition | `YELLOW` Threshold | `RED` Threshold | Mapped `body_region` | `rule_id` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `heart_rate_bpm` | Beats/min vs `baseline_hr_bpm` | $\ge \text{baseline} + 20$ | $\ge \text{baseline} + 40$ | `CARDIOVASCULAR` | `RULE_HR_ELEVATED` |
| `spo2_pct` | Peripheral $\text{SpO}_2$ % | $< 95.0$ | $< 90.0$ | `CARDIOVASCULAR` | `RULE_SPO2_HYPOXIA` |
| `systolic_bp_mmhg` / `diastolic_bp_mmhg` | Arterial BP ($\text{mmHg}$) | $\ge 135$ OR $\ge 85$ | $\ge 160$ OR $\ge 100$ | `CARDIOVASCULAR` | `RULE_BP_HYPERTENSION` |
| `core_temp_c` | Core temperature ($^\circ\text{C}$) | $\ge 37.8$ | $\ge 38.5$ | `SYSTEMIC` | `RULE_CORE_HYPERTHERMIA` |
| `sleep_score` | Actiwatch daily score ($0\text{--}100$) | $< 60$ | $< 40$ | `BRAIN_NEURO` | `RULE_CIRCADIAN_DRIFT` |
| `eeg_fatigue_index` | fNIRS prefrontal fatigue ($0\text{--}1$) | $\ge 0.65$ | $\ge 0.85$ | `BRAIN_NEURO` | `RULE_COGNITIVE_FATIGUE` |
| `radiation_msv` | Cumulative 24h dose ($\text{mSv/day}$) | $> 1.5$ | $> 3.0$ | `SYSTEMIC` | `RULE_RADIATION_SPIKE` |
| Composite SANS Proxy | Sys BP $\ge 135$ AND (Rad $> 1.5$ OR Sleep $< 60$) | Composite breach | N/A | `OCULAR_EYES` | `RULE_SANS_OCULAR_SHIFT` |

## 4. Golden Demo Scenarios (Deterministic Simulator)
The simulator uses a fixed random seed (`seed=42`), accepts `target_user_id` and `time_compression` (which divides the $2.0\text{ s}$ emit interval and scales packet timestamp deltas), and pushes 5 consecutive packets on scenario trigger so the rolling window fires deterministically:

| Scenario Code | Injected Packet Profile | Expected `status_level` | Expected `anomaly_alerts` Fired (Count) |
| :--- | :--- | :--- | :--- |
| `NOMINAL_BASELINE` | HR $\text{baseline} \pm 2$, $\text{SpO}_2$ $98.5$, BP $118/75$, Rad $0.3\text{ mSv/d}$, Sleep $82$, Fatigue $0.20$ | `GREEN` | None ($0$) |
| `SANS_OCULAR_AND_RADIATION_SPIKE` | Sys BP $142$, Dia BP $88$, Rad $2.1\text{ mSv/d}$, Sleep $58$, Fatigue $0.58$ | `YELLOW` | `RULE_BP_HYPERTENSION`, `RULE_RADIATION_SPIKE`, `RULE_CIRCADIAN_DRIFT`, `RULE_SANS_OCULAR_SHIFT` ($4$) |
| `CIRCADIAN_FATIGUE_DRIFT` | Sleep $48$, Fatigue $0.76$, HR $\text{baseline} + 22$ | `YELLOW` | `RULE_CIRCADIAN_DRIFT`, `RULE_COGNITIVE_FATIGUE`, `RULE_HR_ELEVATED` ($3$) |
| `CARDIO_HYPERTENSION` | HR $\text{baseline} + 45$, Sys BP $168$, Dia BP $104$, $\text{SpO}_2$ $93.5$ | `RED` | `RULE_HR_ELEVATED` (`RED`), `RULE_BP_HYPERTENSION` (`RED`), `RULE_SPO2_HYPOXIA` (`YELLOW`) ($3$) |
| `STOP` | Pauses background telemetry loop | Current | None ($0$) |

## 5. User Stories & Acceptance Criteria

### US-01: Dual-Mode RAG Consultation with Pre-Boost Refusal Gate & Chunk-Scoped Catalog
- **Statement:** As an `ASTRONAUT`, I want to select a region on the Digital Twin and submit my symptoms, receiving a diagnosis with verified NASA citations and allowlisted countermeasures that works both online (Gemini) and offline (deterministic fallback).
- **Acceptance Criteria:**
  1. Tokenizer strips English stopwords and uses a denominator floor of $5$ tokens (`max(min(len(query_tokens), 12), 5)`) so short or off-topic queries cannot inflate lexical overlap.
  2. The refusal gate evaluates **pre-boost raw scores**: if raw cosine similarity is below $0.45$ AND raw lexical score is below $0.22$, the backend bypasses the LLM and returns `DETERMINISTIC_REFUSAL` (`confidence_score = 0.10`, `citations = []`, `generated_tasks = []`).
  3. Allowed `countermeasure_ids` passed to the LLM and materialized into tasks are restricted strictly to the union of `default_countermeasure_ids` attached to the top-3 retrieved chunks.
  4. The UI labels the score **"Protocol Retrieval Match"** (capped at $0.70$ in offline mode with no artificial $0.55$ floor).

### US-02: Zero-Latency Cached Trauma Override ("Red Button")
- **Statement:** As any crew member, I want the Trauma Override button to open emergency stabilization checklists in under $100\text{ ms}$ even on a cold offline load or with an expired JWT.
- **Acceptance Criteria:**
  1. `GET /api/v1/trauma-protocols` is public, prefetched into `localStorage`, and backed by a static `frontend/public/trauma_protocols.fallback.json` file generated by the seeder.