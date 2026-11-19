# V2.2 Complete Next.js Frontend MVP (`frontend/`)

This document contains every configuration file, TypeScript interface, API/WebSocket hook, and React component required to build and run the AstroHealth AI frontend MVP in strict alignment with the V2.2 backend:

1. `frontend/package.json` & `frontend/tsconfig.json`
2. `frontend/src/types/astrohealth.ts`
3. `frontend/src/lib/apiClient.ts` (with offline `trauma_protocols.fallback.json` & `localStorage` cache)
4. `frontend/src/app/login/page.tsx`
5. `frontend/src/components/TraumaOverrideModal.tsx` (zero-latency cached checklists + `window.speechSynthesis`)
6. `frontend/src/hooks/useTelemetrySocket.ts` (WebSocket stream updating `overall_status` & `region_statuses`)
7. `frontend/src/components/TelemetryCharts.tsx`
8. `frontend/src/components/DigitalTwinSvg.tsx` (2D interactive SVG driven by `region_statuses`)
9. `frontend/src/components/AnomalyAlertsFeed.tsx`
10. `frontend/src/components/RagDiagnosticsPanel.tsx` (with **"Protocol Retrieval Match"** & citation `provenance` badges)
11. `frontend/src/components/CountermeasureList.tsx`
12. `frontend/src/components/MissionSyncPanel.tsx` (with HMAC-SHA256 verification & Tamper Demo trigger)
13. `frontend/src/components/Navbar.tsx` (with persistent medical disclaimer banner, AI mode badge & scenario injector)
14. `frontend/src/app/layout.tsx` & `frontend/src/app/page.tsx`

---

## 1. `frontend/package.json` & `frontend/tsconfig.json`

### `frontend/package.json`
```json
{
  "name": "astrohealth-ai-frontend",
  "version": "2.2.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "clsx": "2.1.1",
    "lucide-react": "0.446.0",
    "next": "^14.2.25",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "recharts": "2.12.7",
    "tailwind-merge": "2.5.2"
  },
  "devDependencies": {
    "@types/node": "20.16.10",
    "@types/react": "18.3.10",
    "@types/react-dom": "18.3.0",
    "autoprefixer": "10.4.20",
    "postcss": "8.4.47",
    "tailwindcss": "3.4.13",
    "typescript": "5.6.2"
  }
}
```

### `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

## 2. `frontend/src/types/astrohealth.ts`

```typescript
export type RoleType = "ASTRONAUT" | "CMO" | "FLIGHT_SURGEON";
export type StatusLevelType = "GREEN" | "YELLOW" | "RED";
export type SeverityType = "YELLOW" | "RED";
export type ExecutionModeType =
  | "ONLINE_GEMINI"
  | "OFFLINE_FALLBACK"
  | "DETERMINISTIC_REFUSAL";

export type BodyRegionType =
  | "BRAIN_NEURO"
  | "CARDIOVASCULAR"
  | "MUSCULOSKELETAL"
  | "OCULAR_EYES"
  | "GASTROINTESTINAL"
  | "SYSTEMIC";

export type ScenarioType =
  | "NOMINAL_BASELINE"
  | "SANS_OCULAR_AND_RADIATION_SPIKE"
  | "CIRCADIAN_FATIGUE_DRIFT"
  | "CARDIO_HYPERTENSION"
  | "STOP";

export type TaskCategoryType =
  | "MEDICATION"
  | "EXERCISE"
  | "NUTRITION"
  | "HABITAT_ADJUSTMENT";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: RoleType;
  baseline_hr_bpm: number;
  baseline_spo2_pct: number;
  baseline_sys_bp: number;
  baseline_dia_bp: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface HealthCheckResponse {
  status: string;
  ai_provider_mode: ExecutionModeType;
  live_model_verified: boolean | null;
  model_detail: string;
  kb_chunks_loaded: number;
}

export interface TelemetryReading {
  id: string;
  user_id: string;
  recorded_at: string;
  heart_rate_bpm: number;
  spo2_pct: number;
  systolic_bp_mmhg: number;
  diastolic_bp_mmhg: number;
  core_temp_c: number;
  radiation_msv: number;
  sleep_score: number;
  eeg_fatigue_index: number;
  status_level: StatusLevelType;
}

export interface AnomalyAlert {
  id: string;
  user_id: string;
  telemetry_id: string | null;
  rule_id: string;
  body_region: BodyRegionType;
  severity: SeverityType;
  title: string;
  micro_intervention: string;
  citation_source: string;
  is_acknowledged: boolean;
  created_at: string;
}

export type RegionStatusMap = Record<BodyRegionType, StatusLevelType>;

export interface LatestTelemetrySummary {
  user_id: string;
  overall_status: StatusLevelType;
  region_statuses: RegionStatusMap;
  readings: TelemetryReading[];
  active_alerts: AnomalyAlert[];
}

export interface TelemetryWsFrame {
  type: "telemetry";
  reading: TelemetryReading;
  overall_status: StatusLevelType;
  region_statuses: RegionStatusMap;
  alerts: AnomalyAlert[];
}

export interface CitationItem {
  document_title: string;
  page_number: number;
  snippet: string;
  provenance?: string;
}

export interface TreatmentTask {
  id: string;
  countermeasure_id: string;
  task_type: TaskCategoryType;
  title: string;
  instructions: string;
  scheduled_for: string;
  is_completed: boolean;
  completed_at?: string | null;
}

export interface DiagnosticConsultation {
  id: string;
  user_id: string;
  body_region: BodyRegionType;
  symptom_query: string;
  voice_stress_score: number | null;
  ai_diagnosis: string;
  confidence_score: number;
  execution_mode: ExecutionModeType;
  citations: CitationItem[];
  generated_tasks: TreatmentTask[];
  created_at: string;
}

export interface TraumaProtocol {
  id: string;
  code_name: string;
  title: string;
  body_region: string;
  steps: string[];
  nasa_reference: string;
}

export interface SyncReport {
  id: string;
  user_id: string;
  generated_by: string;
  integrity_hmac: string;
  summary: {
    astronaut_id: string;
    astronaut_name: string;
    overall_status?: StatusLevelType;
    telemetry_samples_count: number;
    active_anomalies_count: number;
    active_alerts?: Array<{
      rule_id: string;
      severity: string;
      title: string;
      created_at: string;
    }>;
    consultations_count: number;
    recent_consultations?: Array<{
      body_region: string;
      execution_mode: string;
      ai_diagnosis: string;
      citation_titles: string[];
    }>;
    pending_tasks_count: number;
    snapshot_utc: string;
  };
  sync_status: string;
  created_at: string;
}

export interface SyncReportVerifyResponse {
  report_id: string;
  verified: boolean;
  stored_hmac: string;
  computed_hmac: string;
  algorithm: string;
}
```

---

## 3. `frontend/src/lib/apiClient.ts`

```typescript
import {
  ConsultationResponse,
  DiagnosticConsultation,
  HealthCheckResponse,
  LatestTelemetrySummary,
  LoginResponse,
  ScenarioType,
  SyncReport,
  SyncReportVerifyResponse,
  TraumaProtocol,
  TreatmentTask,
  BodyRegionType,
} from "@/types/astrohealth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost:8000/ws/telemetry";

const TOKEN_STORAGE_KEY = "astrohealth_jwt_token";
const USER_STORAGE_KEY = "astrohealth_user_profile";
const TRAUMA_CACHE_KEY = "astrohealth_trauma_protocols_cache_v2";

const BUILTIN_TRAUMA_FALLBACK: TraumaProtocol[] = [
  {
    id: "e55e8400-e29b-41d4-a716-446655440555",
    code_name: "ACUTE_HEMORRHAGE_MICROGRAVITY",
    title: "Acute External Hemorrhage & Microgravity Restraint Stabilization",
    body_region: "CARDIOVASCULAR",
    steps: [
      "STEP 1: Secure patient and responder to the habitat restraint grid before intervention to prevent microgravity recoil.",
      "STEP 2: Apply direct, continuous manual pressure over the bleeding site using sterile gauze for a minimum of 3 minutes.",
      "STEP 3: If severe extremity bleeding continues, apply an arterial tourniquet proximal to the wound and record the exact UTC time.",
      "STEP 4: Continuously monitor heart rate, blood pressure, and SpO2 while alerting the Crew Medical Officer.",
    ],
    nasa_reference:
      "NASA ISS Integrated Medical Group (IMG) First-Aid Stabilization Checklist (Illustrative Prototype Summary)",
  },
  {
    id: "e55e8400-e29b-41d4-a716-446655440556",
    code_name: "ACUTE_HYPOXIA_CABIN_DEPRESSURIZATION",
    title: "Acute Cabin Depressurization & Supplemental Oxygen Protocol",
    body_region: "BRAIN_NEURO",
    steps: [
      "STEP 1: Don emergency portable 100% oxygen mask immediately and verify facepiece seal.",
      "STEP 2: Seal affected module hatch and verify cabin total pressure and oxygen partial pressure gauges.",
      "STEP 3: Exhale normally during any rapid pressure transition; never hold breath during decompression.",
      "STEP 4: Maintain continuous pulse oximetry (SpO2) monitoring and restrict physical exertion.",
    ],
    nasa_reference:
      "NASA Spaceflight Medical Operations Emergency Depressurization Procedure (Illustrative Prototype Summary)",
  },
  {
    id: "e55e8400-e29b-41d4-a716-446655440557",
    code_name: "OCULAR_CONTAMINANT_IRRIGATION",
    title: "Acute Ocular Particulate or Chemical Irritation Washout",
    body_region: "OCULAR_EYES",
    steps: [
      "STEP 1: Don protective breathing apparatus if airborne habitat contaminant is suspected.",
      "STEP 2: Position zero-gravity sealed ocular irrigation eyewear over the affected eye(s).",
      "STEP 3: Flush continuously with sterile isotonic saline for 15 minutes from nasal to temporal corner.",
      "STEP 4: Avoid rubbing the eye and perform visual acuity and pH verification with the Crew Medical Officer.",
    ],
    nasa_reference:
      "NASA Crew Health Care System (CHeCS) Ocular Washout Protocol (Illustrative Prototype Summary)",
  },
];

let memoryTraumaCache: TraumaProtocol[] = BUILTIN_TRAUMA_FALLBACK;

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredAuth(data: LoginResponse): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
  window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(USER_STORAGE_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  requireAuth = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (requireAuth) {
    const token = getStoredToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`;
    try {
      const errBody = await response.json();
      if (errBody?.error?.message) {
        errorMessage = `[${errBody.error.code}] ${errBody.error.message}`;
      }
    } catch {
      // Fallback to status text
    }
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}

/**
 * Synchronously returns cached Trauma Override protocols in <1ms so emergency
 * checklists never wait on network I/O or fail on expired JWTs.
 */
export function getInstantTraumaProtocols(): TraumaProtocol[] {
  if (typeof window !== "undefined") {
    const raw = window.localStorage.getItem(TRAUMA_CACHE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as TraumaProtocol[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          memoryTraumaCache = parsed;
          return parsed;
        }
      } catch {
        // Ignore corrupt localStorage
      }
    }
  }
  return memoryTraumaCache;
}

/**
 * Prefetches Trauma Protocols from static public fallback JSON first, then refreshes
 * from the public backend endpoint `/api/v1/trauma-protocols`.
 */
export async function prefetchTraumaProtocols(): Promise<TraumaProtocol[]> {
  if (typeof window !== "undefined") {
    try {
      const staticRes = await fetch("/trauma_protocols.fallback.json");
      if (staticRes.ok) {
        const staticData = (await staticRes.json()) as TraumaProtocol[];
        if (Array.isArray(staticData) && staticData.length > 0) {
          memoryTraumaCache = staticData;
          window.localStorage.setItem(TRAUMA_CACHE_KEY, JSON.stringify(staticData));
        }
      }
    } catch {
      // Static file optional if built-in fallback is present
    }
  }

  try {
    const liveData = await request<TraumaProtocol[]>(
      "/trauma-protocols",
      { method: "GET" },
      false
    );
    if (Array.isArray(liveData) && liveData.length > 0) {
      memoryTraumaCache = liveData;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(TRAUMA_CACHE_KEY, JSON.stringify(liveData));
      }
    }
  } catch {
    // Offline mode: silently retain cached / fallback protocols
  }

  return memoryTraumaCache;
}

export const apiClient = {
  getHealth: (liveCheck = false) =>
    request<HealthCheckResponse>(
      `/health?live_check=${liveCheck ? "true" : "false"}`,
      { method: "GET" },
      false
    ),

  login: (email: string, password: string) =>
    request<LoginResponse>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
      false
    ),

  getLatestTelemetry: (userId?: string, limit = 30) => {
    const query = new URLSearchParams({ limit: String(limit) });
    if (userId) query.set("user_id", userId);
    return request<LatestTelemetrySummary>(`/telemetry/latest?${query.toString()}`);
  },

  simulateScenario: (
    scenario: ScenarioType,
    targetUserId?: string,
    timeCompression = 1.0
  ) =>
    request<{
      target_user_id: string;
      active_scenario: ScenarioType;
      status_level: string;
      alerts_triggered: number;
    }>("/telemetry/simulate-scenario", {
      method: "POST",
      body: JSON.stringify({
        scenario,
        target_user_id: targetUserId,
        time_compression: timeCompression,
      }),
    }),

  acknowledgeAlert: (alertId: string) =>
    request<{ id: string; is_acknowledged: boolean }>(
      `/alerts/${alertId}/acknowledge`,
      { method: "PATCH" }
    ),

  createConsultation: (payload: {
    target_user_id?: string;
    body_region: BodyRegionType;
    symptom_query: string;
    voice_stress_score: number | null;
  }) =>
    request<DiagnosticConsultation>("/consultations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listConsultations: (userId?: string) => {
    const q = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return request<DiagnosticConsultation[]>(`/consultations${q}`);
  },

  listTasks: (userId?: string) => {
    const q = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return request<TreatmentTask[]>(`/tasks${q}`);
  },

  completeTask: (taskId: string) =>
    request<{ id: string; is_completed: boolean; completed_at: string }>(
      `/tasks/${taskId}/complete`,
      { method: "PATCH" }
    ),

  createSyncReport: (targetUserId?: string) =>
    request<SyncReport>("/reports/sync", {
      method: "POST",
      body: JSON.stringify({ target_user_id: targetUserId }),
    }),

  listSyncReports: (userId?: string) => {
    const q = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return request<SyncReport[]>(`/reports${q}`);
  },

  verifySyncReport: (reportId: string) =>
    request<SyncReportVerifyResponse>(`/reports/${reportId}/verify`),

  tamperSyncReportDemo: (reportId: string) =>
    request<{ report_id: string; tampered: boolean }>(
      `/reports/${reportId}/tamper-demo`,
      { method: "POST" }
    ),
};
```

---

## 4. `frontend/src/app/login/page.tsx`

```tsx
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, Rocket, UserCheck } from "lucide-react";
import { apiClient, setStoredAuth, prefetchTraumaProtocols } from "@/lib/apiClient";

const DEMO_ACCOUNTS = [
  {
    label: "Cmdr. Mark Watney (Astronaut)",
    email: "mark.watney@nasa.gov",
    role: "ASTRONAUT",
  },
  {
    label: "Dr. Melissa Lewis (Crew Medical Officer)",
    email: "cmo.lewis@nasa.gov",
    role: "CMO",
  },
  {
    label: "Dr. Elena Cruz (Flight Surgeon - Earth)",
    email: "surgeon.cruz@nasa.gov",
    role: "FLIGHT_SURGEON",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("mark.watney@nasa.gov");
  const [password, setPassword] = useState("MarsMission2026!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiClient.login(email, password);
      setStoredAuth(res);
      await prefetchTraumaProtocols();
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      <div className="bg-amber-950/90 border-b border-amber-700 px-4 py-2 text-center text-xs font-mono text-amber-200 flex items-center justify-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          CLINICAL DECISION-SUPPORT PROTOTYPE — SYNTHETIC DEMO DATA ONLY — NOT A
          CERTIFIED MEDICAL DEVICE
        </span>
      </div>

      <div className="max-w-md w-full mx-auto my-auto p-8 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-lg bg-cyan-950 border border-cyan-700 text-cyan-400">
            <Rocket className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              AstroHealth AI
            </h1>
            <p className="text-xs text-slate-400">
              Autonomous Deep-Space Medical Telemetry & RAG Console
            </p>
          </div>
        </div>

        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Quick-Select Synthetic Crew Profile
          </p>
          <div className="space-y-2">
            {DEMO_ACCOUNTS.map((acct) => (
              <button
                key={acct.email}
                type="button"
                onClick={() => {
                  setEmail(acct.email);
                  setPassword("MarsMission2026!");
                }}
                className={`w-full text-left px-3 py-2 rounded-lg border text-xs flex items-center justify-between transition ${
                  email === acct.email
                    ? "bg-cyan-950/70 border-cyan-500 text-cyan-200"
                    : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                }`}
              >
                <span className="flex items-center gap-2">
                  <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                  {acct.label}
                </span>
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                  {acct.role}
                </span>
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Crew Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Mission Passkey
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-950/80 border border-red-700 text-xs text-red-200">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition"
          >
            {loading ? "Initializing Onboard Console..." : "Authenticate Crew Console"}
          </button>
        </form>
      </div>

      <footer className="py-3 text-center text-xs text-slate-500 font-mono">
        NASA Space Apps 2026 Prototype • Edge-First Medical Decision Support
      </footer>
    </div>
  );
}
```

---

## 5. `frontend/src/components/TraumaOverrideModal.tsx`

```tsx
"use client";

import React, { useEffect, useState } from "react";
import { AlertOctagon, Volume2, VolumeX, X, CheckCircle2 } from "lucide-react";
import { getInstantTraumaProtocols } from "@/lib/apiClient";
import { TraumaProtocol } from "@/types/astrohealth";

interface TraumaOverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function TraumaOverrideModal({
  isOpen,
  onClose,
}: TraumaOverrideModalProps) {
  const [protocols, setProtocols] = useState<TraumaProtocol[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Record<number, boolean>>({});
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Zero-latency synchronous read from memory/localStorage/built-in fallback
      const cached = getInstantTraumaProtocols();
      setProtocols(cached);
      setSelectedIdx(0);
      setCompletedSteps({});
    } else if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const activeProtocol = protocols[selectedIdx];

  const speakProtocolAloud = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window) || !activeProtocol) {
      return;
    }
    window.speechSynthesis.cancel();
    const fullText = `${activeProtocol.title}. ${activeProtocol.steps.join(" ")}`;
    const utterance = new SpeechSynthesisUtterance(fullText);
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeech = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-red-950/95 backdrop-blur-md flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-slate-950 border-2 border-red-500 rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-red-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertOctagon className="w-8 h-8 text-white animate-pulse" />
            <div>
              <h2 className="text-xl font-black tracking-wide text-white uppercase">
                TRAUMA OVERRIDE — ZERO-LATENCY EMERGENCY PROTOCOL
              </h2>
              <p className="text-xs text-red-100 font-mono">
                LLM BYPASSED • CACHED ONBOARD CHECKLIST • WORKS OFFLINE & WITHOUT AUTH
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-red-800 hover:bg-red-900 text-white"
            aria-label="Exit Trauma Override"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-red-300 mb-2">
              Select Emergency Checklist
            </p>
            {protocols.map((proto, idx) => (
              <button
                key={proto.id}
                onClick={() => {
                  stopSpeech();
                  setSelectedIdx(idx);
                  setCompletedSteps({});
                }}
                className={`w-full text-left p-3 rounded-xl border text-sm font-semibold transition ${
                  idx === selectedIdx
                    ? "bg-red-900/60 border-red-400 text-white"
                    : "bg-slate-900 border-slate-800 text-slate-300 hover:border-red-800"
                }`}
              >
                <div className="text-[10px] font-mono text-red-300">
                  {proto.body_region}
                </div>
                <div>{proto.title}</div>
              </button>
            ))}
          </div>

          <div className="md:col-span-2 flex flex-col justify-between bg-slate-900 border border-slate-800 rounded-xl p-5">
            {activeProtocol ? (
              <>
                <div>
                  <div className="flex items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-800">
                    <div>
                      <span className="text-xs font-mono text-red-400">
                        CODE: {activeProtocol.code_name}
                      </span>
                      <h3 className="text-lg font-bold text-white">
                        {activeProtocol.title}
                      </h3>
                    </div>
                    <button
                      type="button"
                      onClick={isSpeaking ? stopSpeech : speakProtocolAloud}
                      className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold flex items-center gap-2 shrink-0"
                    >
                      {isSpeaking ? (
                        <>
                          <VolumeX className="w-4 h-4" />
                          Stop Voice Readout
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-4 h-4" />
                          Read Aloud (Web Speech)
                        </>
                      )}
                    </button>
                  </div>

                  <div className="space-y-3">
                    {activeProtocol.steps.map((step, sIdx) => {
                      const done = !!completedSteps[sIdx];
                      return (
                        <div
                          key={sIdx}
                          onClick={() =>
                            setCompletedSteps((prev) => ({
                              ...prev,
                              [sIdx]: !prev[sIdx],
                            }))
                          }
                          className={`p-4 rounded-xl border cursor-pointer flex items-start gap-3 transition ${
                            done
                              ? "bg-emerald-950/40 border-emerald-600 text-emerald-200"
                              : "bg-slate-950 border-slate-800 text-white hover:border-red-500"
                          }`}
                        >
                          <CheckCircle2
                            className={`w-6 h-6 shrink-0 mt-0.5 ${
                              done ? "text-emerald-400" : "text-slate-600"
                            }`}
                          />
                          <span className="text-base font-medium leading-relaxed">
                            {step}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="mt-6 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>REF: {activeProtocol.nasa_reference}</span>
                  <span>LATENCY: &lt;10ms LOCAL CACHE</span>
                </div>
              </>
            ) : (
              <p className="text-sm text-slate-400">No protocols available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 6. `frontend/src/hooks/useTelemetrySocket.ts`

```typescript
"use client";

import { useEffect, useState, useCallback } from "react";
import {
  AnomalyAlert,
  RegionStatusMap,
  StatusLevelType,
  TelemetryReading,
  TelemetryWsFrame,
} from "@/types/astrohealth";
import { apiClient, getStoredToken, WS_BASE_URL } from "@/lib/apiClient";

const DEFAULT_REGIONS: RegionStatusMap = {
  BRAIN_NEURO: "GREEN",
  CARDIOVASCULAR: "GREEN",
  MUSCULOSKELETAL: "GREEN",
  OCULAR_EYES: "GREEN",
  GASTROINTESTINAL: "GREEN",
  SYSTEMIC: "GREEN",
};

export function useTelemetrySocket(targetUserId?: string) {
  const [readings, setReadings] = useState<TelemetryReading[]>([]);
  const [overallStatus, setOverallStatus] = useState<StatusLevelType>("GREEN");
  const [regionStatuses, setRegionStatuses] =
    useState<RegionStatusMap>(DEFAULT_REGIONS);
  const [activeAlerts, setActiveAlerts] = useState<AnomalyAlert[]>([]);
  const [wsConnected, setWsConnected] = useState(false);

  const refreshInitialSnapshot = useCallback(async () => {
    try {
      const summary = await apiClient.getLatestTelemetry(targetUserId, 30);
      setReadings(summary.readings);
      setOverallStatus(summary.overall_status);
      setRegionStatuses(summary.region_statuses);
      setActiveAlerts(summary.active_alerts);
    } catch {
      // Handled by caller or auth redirect
    }
  }, [targetUserId]);

  useEffect(() => {
    refreshInitialSnapshot();
  }, [refreshInitialSnapshot]);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) return;

    const params = new URLSearchParams({ token });
    if (targetUserId) {
      params.set("user_id", targetUserId);
    }

    const ws = new WebSocket(`${WS_BASE_URL}?${params.toString()}`);

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);

    ws.onmessage = (event) => {
      try {
        const frame = JSON.parse(event.data) as TelemetryWsFrame;
        if (frame.type === "telemetry" && frame.reading) {
          setReadings((prev) => [...prev.slice(-29), frame.reading]);
          if (frame.overall_status) {
            setOverallStatus(frame.overall_status);
          }
          if (frame.region_statuses) {
            setRegionStatuses(frame.region_statuses);
          }
          if (Array.isArray(frame.alerts) && frame.alerts.length > 0) {
            setActiveAlerts((prev) => {
              const existingIds = new Set(prev.map((a) => a.id));
              const fresh = frame.alerts.filter((a) => !existingIds.has(a.id));
              return [...fresh, ...prev];
            });
          }
        }
      } catch {
        // Ignore malformed frame
      }
    };

    return () => {
      ws.close();
    };
  }, [targetUserId]);

  return {
    readings,
    overallStatus,
    regionStatuses,
    activeAlerts,
    setActiveAlerts,
    wsConnected,
    refreshInitialSnapshot,
  };
}
```

---

## 7. `frontend/src/components/TelemetryCharts.tsx`

```tsx
"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { Activity, Shield, Moon, HeartPulse } from "lucide-react";
import { TelemetryReading } from "@/types/astrohealth";

interface TelemetryChartsProps {
  readings: TelemetryReading[];
}

export default function TelemetryCharts({ readings }: TelemetryChartsProps) {
  const latest = readings[readings.length - 1];

  const chartData = readings.map((r) => ({
    time: new Date(r.recorded_at).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }),
    hr: r.heart_rate_bpm,
    sys: r.systolic_bp_mmhg,
    dia: r.diastolic_bp_mmhg,
    spo2: r.spo2_pct,
    rad: r.radiation_msv,
    sleep: r.sleep_score,
    fatigue: Math.round(r.eeg_fatigue_index * 100),
  }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Heart Rate & BP</span>
            <HeartPulse className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-1 text-lg font-bold text-white font-mono">
            {latest ? `${latest.heart_rate_bpm} BPM` : "--"}{" "}
            <span className="text-xs text-slate-400">
              ({latest ? `${latest.systolic_bp_mmhg}/${latest.diastolic_bp_mmhg}` : "--"})
            </span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>SpO2 & Core Temp</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-1 text-lg font-bold text-white font-mono">
            {latest ? `${latest.spo2_pct.toFixed(1)}%` : "--"}{" "}
            <span className="text-xs text-slate-400">
              ({latest ? `${latest.core_temp_c.toFixed(1)}°C` : "--"})
            </span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Shielded Habitat Dosimeter</span>
            <Shield className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-1 text-lg font-bold text-white font-mono">
            {latest ? `${latest.radiation_msv.toFixed(2)} mSv/d` : "--"}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Sleep & fNIRS Fatigue</span>
            <Moon className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-1 text-lg font-bold text-white font-mono">
            {latest ? `Sleep ${latest.sleep_score}` : "--"}{" "}
            <span className="text-xs text-slate-400">
              (Fatigue {latest ? `${Math.round(latest.eeg_fatigue_index * 100)}%` : "--"})
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 h-56">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Cardiovascular Stream (HR & Systolic BP)
          </h4>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" hide />
              <YAxis domain={[40, 200]} stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="hr"
                stroke="#f43f5e"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                name="Heart Rate (BPM)"
              />
              <Line
                type="monotone"
                dataKey="sys"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                name="Systolic BP (mmHg)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 h-56">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Circadian Sleep Score & Cognitive Fatigue (%)
          </h4>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="sleep"
                stroke="#818cf8"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                name="Actiwatch Sleep Score"
              />
              <Line
                type="monotone"
                dataKey="fatigue"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                name="fNIRS Fatigue (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
```

---

## 8. `frontend/src/components/DigitalTwinSvg.tsx`

```tsx
"use client";

import React from "react";
import { BodyRegionType, RegionStatusMap, StatusLevelType } from "@/types/astrohealth";

interface DigitalTwinSvgProps {
  regionStatuses: RegionStatusMap;
  selectedRegion: BodyRegionType;
  onSelectRegion: (region: BodyRegionType) => void;
}

const REGION_LABELS: Record<BodyRegionType, string> = {
  BRAIN_NEURO: "Brain & Circadian Neuro",
  OCULAR_EYES: "Ocular / SANS Visual System",
  CARDIOVASCULAR: "Cardiovascular & Cardiopulmonary",
  GASTROINTESTINAL: "Gastrointestinal & Metabolic",
  MUSCULOSKELETAL: "Musculoskeletal & Bone Density",
  SYSTEMIC: "Systemic / Radiation & Thermal",
};

function statusFill(status: StatusLevelType, isSelected: boolean): string {
  if (status === "RED") return isSelected ? "#ef4444" : "#dc2626";
  if (status === "YELLOW") return isSelected ? "#f59e0b" : "#d97706";
  return isSelected ? "#06b6d4" : "#10b981";
}

export default function DigitalTwinSvg({
  regionStatuses,
  selectedRegion,
  onSelectRegion,
}: DigitalTwinSvgProps) {
  return (
    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center">
      <div className="w-full flex items-center justify-between mb-2">
        <h3 className="text-sm font-bold uppercase tracking-wider text-white">
          Personalized 2D Digital Twin
        </h3>
        <span className="text-[11px] font-mono text-cyan-400">
          Click anatomical region to diagnose
        </span>
      </div>

      <svg
        viewBox="0 0 220 400"
        className="w-52 h-80 my-2 select-none"
        aria-label="Astronaut Digital Twin Body Map"
      >
        {/* SYSTEMIC Aura Halo */}
        <rect
          x="15"
          y="10"
          width="190"
          height="380"
          rx="28"
          fill="none"
          stroke={statusFill(regionStatuses.SYSTEMIC, selectedRegion === "SYSTEMIC")}
          strokeWidth={selectedRegion === "SYSTEMIC" ? "4" : "2"}
          strokeDasharray="6 4"
          className="cursor-pointer transition-all"
          onClick={() => onSelectRegion("SYSTEMIC")}
        />

        {/* BRAIN_NEURO (Head Cranium) */}
        <circle
          cx="110"
          cy="52"
          r="28"
          fill={statusFill(regionStatuses.BRAIN_NEURO, selectedRegion === "BRAIN_NEURO")}
          fillOpacity="0.8"
          stroke="#ffffff"
          strokeWidth={selectedRegion === "BRAIN_NEURO" ? "3" : "1"}
          className="cursor-pointer transition-all"
          onClick={() => onSelectRegion("BRAIN_NEURO")}
        />

        {/* OCULAR_EYES (Visor / Ocular Band) */}
        <rect
          x="90"
          y="44"
          width="40"
          height="12"
          rx="6"
          fill={statusFill(regionStatuses.OCULAR_EYES, selectedRegion === "OCULAR_EYES")}
          stroke="#0f172a"
          strokeWidth="2"
          className="cursor-pointer transition-all"
          onClick={() => onSelectRegion("OCULAR_EYES")}
        />

        {/* CARDIOVASCULAR (Thorax / Heart & Lungs) */}
        <rect
          x="75"
          y="92"
          width="70"
          height="68"
          rx="12"
          fill={statusFill(
            regionStatuses.CARDIOVASCULAR,
            selectedRegion === "CARDIOVASCULAR"
          )}
          fillOpacity="0.85"
          stroke="#ffffff"
          strokeWidth={selectedRegion === "CARDIOVASCULAR" ? "3" : "1"}
          className="cursor-pointer transition-all"
          onClick={() => onSelectRegion("CARDIOVASCULAR")}
        />

        {/* GASTROINTESTINAL (Abdomen) */}
        <rect
          x="78"
          y="168"
          width="64"
          height="56"
          rx="10"
          fill={statusFill(
            regionStatuses.GASTROINTESTINAL,
            selectedRegion === "GASTROINTESTINAL"
          )}
          fillOpacity="0.85"
          stroke="#ffffff"
          strokeWidth={selectedRegion === "GASTROINTESTINAL" ? "3" : "1"}
          className="cursor-pointer transition-all"
          onClick={() => onSelectRegion("GASTROINTESTINAL")}
        />

        {/* MUSCULOSKELETAL (Arms & Legs Group) */}
        <g
          fill={statusFill(
            regionStatuses.MUSCULOSKELETAL,
            selectedRegion === "MUSCULOSKELETAL"
          )}
          fillOpacity="0.8"
          stroke="#ffffff"
          strokeWidth={selectedRegion === "MUSCULOSKELETAL" ? "2.5" : "1"}
          className="cursor-pointer transition-all"
          onClick={() => onSelectRegion("MUSCULOSKELETAL")}
        >
          {/* Left & Right Arms */}
          <rect x="44" y="96" width="24" height="110" rx="10" />
          <rect x="152" y="96" width="24" height="110" rx="10" />
          {/* Left & Right Legs */}
          <rect x="78" y="232" width="28" height="135" rx="12" />
          <rect x="114" y="232" width="28" height="135" rx="12" />
        </g>
      </svg>

      <div className="w-full grid grid-cols-2 gap-1.5 mt-2">
        {(Object.keys(REGION_LABELS) as BodyRegionType[]).map((region) => {
          const st = regionStatuses[region];
          const active = selectedRegion === region;
          return (
            <button
              key={region}
              type="button"
              onClick={() => onSelectRegion(region)}
              className={`px-2.5 py-1.5 rounded-lg border text-left text-xs flex items-center justify-between transition ${
                active
                  ? "bg-cyan-950/80 border-cyan-400 text-white"
                  : "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              <span className="truncate pr-1">{REGION_LABELS[region]}</span>
              <span
                className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                  st === "RED"
                    ? "bg-red-500"
                    : st === "YELLOW"
                    ? "bg-amber-400"
                    : "bg-emerald-400"
                }`}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
```

---

## 9. `frontend/src/components/AnomalyAlertsFeed.tsx`

```tsx
"use client";

import React from "react";
import { BellRing, Check, BookOpen } from "lucide-react";
import { AnomalyAlert } from "@/types/astrohealth";

interface AnomalyAlertsFeedProps {
  alerts: AnomalyAlert[];
  onAcknowledge: (alertId: string) => Promise<void>;
}

export default function AnomalyAlertsFeed({
  alerts,
  onAcknowledge,
}: AnomalyAlertsFeedProps) {
  return (
    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BellRing className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-white">
            Proactive Anomaly Micro-Interventions
          </h3>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
          {alerts.length} Active
        </span>
      </div>

      {alerts.length === 0 ? (
        <div className="p-6 text-center text-xs text-slate-400 bg-slate-950 rounded-lg border border-slate-800/60">
          All rolling 5-packet biometric windows are within nominal crew baseline.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-xl border ${
                alert.severity === "RED"
                  ? "bg-red-950/50 border-red-600"
                  : "bg-amber-950/40 border-amber-600/80"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded mr-2 ${
                      alert.severity === "RED"
                        ? "bg-red-600 text-white"
                        : "bg-amber-500 text-slate-950"
                    }`}
                  >
                    {alert.severity} • {alert.body_region}
                  </span>
                  <h4 className="text-xs font-bold text-white inline">
                    {alert.title}
                  </h4>
                </div>
                <button
                  type="button"
                  onClick={() => onAcknowledge(alert.id)}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-200 flex items-center gap-1 shrink-0"
                >
                  <Check className="w-3 h-3" />
                  Ack
                </button>
              </div>

              <p className="text-xs text-slate-200 mt-2 leading-relaxed">
                {alert.micro_intervention}
              </p>

              <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center gap-1.5 text-[11px] text-slate-400 font-mono">
                <BookOpen className="w-3 h-3 text-cyan-400 shrink-0" />
                <span className="truncate">{alert.citation_source}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 10. `frontend/src/components/RagDiagnosticsPanel.tsx`

```tsx
"use client";

import React, { useState } from "react";
import { Stethoscope, Send, FileText, Info } from "lucide-react";
import { BodyRegionType, DiagnosticConsultation } from "@/types/astrohealth";

interface RagDiagnosticsPanelProps {
  selectedRegion: BodyRegionType;
  consultations: DiagnosticConsultation[];
  onSubmitConsultation: (
    region: BodyRegionType,
    query: string,
    voiceStress: number
  ) => Promise<void>;
}

const CANNED_DEMO_QUERIES: Record<BodyRegionType, string> = {
  OCULAR_EYES:
    "My eyes feel blurry when reading panels over the past 4 days with mild retro-orbital headache.",
  BRAIN_NEURO:
    "Experiencing fragmented sleep below 6 hours, daytime drowsiness, and cognitive fatigue.",
  SYSTEMIC:
    "Habitat radiation dosimeter spiked above 1.8 mSv/day with mild nausea and systemic fatigue.",
  CARDIOVASCULAR:
    "Noticeable resting palpitations and elevated blood pressure after microgravity fluid shift.",
  MUSCULOSKELETAL:
    "Lower back stiffness and leg muscle soreness after resistive exercise session.",
  GASTROINTESTINAL:
    "Mild appetite reduction and slower gastric motility during transit.",
};

export default function RagDiagnosticsPanel({
  selectedRegion,
  consultations,
  onSubmitConsultation,
}: RagDiagnosticsPanelProps) {
  const [query, setQuery] = useState(CANNED_DEMO_QUERIES[selectedRegion]);
  const [voiceStress, setVoiceStress] = useState<number>(0.35);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadPreset = () => {
    setQuery(CANNED_DEMO_QUERIES[selectedRegion]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmitConsultation(selectedRegion, query, voiceStress);
    } catch (err: any) {
      setError(err.message || "Consultation request failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const latest = consultations[0];

  return (
    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Stethoscope className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-white">
            NASA HRP Grounded RAG Clinical Consultation
          </h3>
        </div>
        <button
          type="button"
          onClick={handleLoadPreset}
          className="text-xs text-cyan-400 hover:underline font-mono"
        >
          Load Region Sample Query ({selectedRegion})
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <textarea
            rows={2}
            required
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe crew symptoms for the selected anatomical region..."
            className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400 font-mono">
              Simulated Voice Stress Heuristic:{" "}
              <span className="text-cyan-300 font-bold">
                {voiceStress.toFixed(2)}
              </span>
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={voiceStress}
              onChange={(e) => setVoiceStress(parseFloat(e.target.value))}
              className="w-28 accent-cyan-500"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            {submitting ? "Synthesizing..." : "Run RAG Assessment"}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-2.5 rounded-lg bg-red-950/80 border border-red-700 text-xs text-red-200">
          {error}
        </div>
      )}

      {latest && (
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800">
            <span className="text-xs font-mono font-bold text-cyan-300">
              REGION: {latest.body_region}
            </span>
            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                  latest.execution_mode === "ONLINE_GEMINI"
                    ? "bg-emerald-950 text-emerald-300 border border-emerald-700"
                    : latest.execution_mode === "OFFLINE_FALLBACK"
                    ? "bg-amber-950 text-amber-300 border border-amber-700"
                    : "bg-rose-950 text-rose-300 border border-rose-700"
                }`}
              >
                MODE: {latest.execution_mode}
              </span>
              <span className="text-xs font-mono text-slate-300">
                Protocol Retrieval Match:{" "}
                <strong>{Math.round(latest.confidence_score * 100)}%</strong>
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-200 leading-relaxed">
            {latest.ai_diagnosis}
          </p>

          {latest.citations.length > 0 && (
            <div className="space-y-2 pt-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Verified Onboard NASA HRP Citations
              </p>
              {latest.citations.map((cit, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between text-cyan-300 font-mono text-[11px]">
                    <span className="flex items-center gap-1.5 font-semibold">
                      <FileText className="w-3.5 h-3.5 shrink-0" />
                      {cit.document_title}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800 shrink-0">
                      Section / Page {cit.page_number}
                    </span>
                  </div>
                  <p className="text-slate-300 italic text-[11px]">
                    &ldquo;{cit.snippet}&rdquo;
                  </p>
                  <div className="flex items-center gap-1 text-[10px] text-amber-300/90 font-mono pt-0.5">
                    <Info className="w-3 h-3 shrink-0" />
                    <span>
                      {cit.provenance ||
                        "Illustrative page reference, paraphrased prototype KB based on NASA HRP themes."}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 11. `frontend/src/components/CountermeasureList.tsx`

```tsx
"use client";

import React from "react";
import { CheckSquare, Clock } from "lucide-react";
import { TreatmentTask } from "@/types/astrohealth";

interface CountermeasureListProps {
  tasks: TreatmentTask[];
  onCompleteTask: (taskId: string) => Promise<void>;
}

export default function CountermeasureList({
  tasks,
  onCompleteTask,
}: CountermeasureListProps) {
  return (
    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <CheckSquare className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-white">
            Allowlisted Countermeasure Schedule
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {tasks.filter((t) => !t.is_completed).length} Pending
        </span>
      </div>

      {tasks.length === 0 ? (
        <p className="text-xs text-slate-400 p-4 bg-slate-950 rounded-lg border border-slate-800">
          No countermeasure tasks scheduled yet. Run a RAG consultation to
          materialize protocol tasks from the allowlisted catalog.
        </p>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`p-3 rounded-lg border flex items-start justify-between gap-3 ${
                task.is_completed
                  ? "bg-slate-950/40 border-slate-800/60 opacity-60"
                  : "bg-slate-950 border-slate-800"
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                    {task.countermeasure_id} • {task.task_type}
                  </span>
                  <span className="text-xs font-bold text-white">
                    {task.title}
                  </span>
                </div>
                <p className="text-xs text-slate-300">{task.instructions}</p>
                <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
                  <Clock className="w-3 h-3" />
                  <span>
                    Scheduled:{" "}
                    {new Date(task.scheduled_for).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>

              {!task.is_completed && (
                <button
                  type="button"
                  onClick={() => onCompleteTask(task.id)}
                  className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shrink-0"
                >
                  Complete
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 12. `frontend/src/components/MissionSyncPanel.tsx`

```tsx
"use client";

import React, { useState } from "react";
import { Radio, ShieldCheck, ShieldX, Bug } from "lucide-react";
import { SyncReport, SyncReportVerifyResponse } from "@/types/astrohealth";

interface MissionSyncPanelProps {
  reports: SyncReport[];
  onGenerateReport: () => Promise<void>;
  onVerifyReport: (reportId: string) => Promise<SyncReportVerifyResponse>;
  onTamperReport: (reportId: string) => Promise<void>;
}

export default function MissionSyncPanel({
  reports,
  onGenerateReport,
  onVerifyReport,
  onTamperReport,
}: MissionSyncPanelProps) {
  const [verifications, setVerifications] = useState<
    Record<string, SyncReportVerifyResponse>
  >({});
  const [busyId, setBusyId] = useState<string | null>(null);

  const handleVerify = async (reportId: string) => {
    setBusyId(reportId);
    try {
      const res = await onVerifyReport(reportId);
      setVerifications((prev) => ({ ...prev, [reportId]: res }));
    } finally {
      setBusyId(null);
    }
  };

  const handleTamper = async (reportId: string) => {
    setBusyId(reportId);
    try {
      await onTamperReport(reportId);
      const res = await onVerifyReport(reportId);
      setVerifications((prev) => ({ ...prev, [reportId]: res }));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-white">
            Asynchronous Earth Mission Control Sync (HMAC-SHA256)
          </h3>
        </div>
        <button
          type="button"
          onClick={onGenerateReport}
          className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold"
        >
          Generate Signed Digest
        </button>
      </div>

      {reports.length === 0 ? (
        <p className="text-xs text-slate-400 p-3 bg-slate-950 rounded-lg border border-slate-800">
          No asynchronous Mission Control digests queued yet.
        </p>
      ) : (
        <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
          {reports.map((rep) => {
            const v = verifications[rep.id];
            return (
              <div
                key={rep.id}
                className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-white">
                    {rep.summary.astronaut_name} • Status:{" "}
                    {rep.summary.overall_status || "NOMINAL"}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={busyId === rep.id}
                      onClick={() => handleVerify(rep.id)}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 font-mono text-[11px]"
                    >
                      Verify HMAC
                    </button>
                    <button
                      type="button"
                      disabled={busyId === rep.id}
                      onClick={() => handleTamper(rep.id)}
                      className="px-2 py-1 rounded bg-rose-950 hover:bg-rose-900 border border-rose-700 text-rose-200 font-mono text-[11px] flex items-center gap-1"
                      title="Dev-only demo: mutates summary_json without updating HMAC"
                    >
                      <Bug className="w-3 h-3" />
                      Tamper Demo
                    </button>
                  </div>
                </div>

                <div className="font-mono text-[10px] text-slate-400 break-all">
                  HMAC-SHA256: {rep.integrity_hmac}
                </div>

                {v && (
                  <div
                    className={`p-2 rounded border flex items-center gap-2 font-mono text-[11px] ${
                      v.verified
                        ? "bg-emerald-950/60 border-emerald-600 text-emerald-200"
                        : "bg-red-950/70 border-red-600 text-red-200"
                    }`}
                  >
                    {v.verified ? (
                      <>
                        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>
                          INTEGRITY VERIFIED (HMAC-SHA256 match confirmed)
                        </span>
                      </>
                    ) : (
                      <>
                        <ShieldX className="w-4 h-4 text-red-400 shrink-0" />
                        <span>
                          TAMPER DETECTED! Stored HMAC does not match canonical
                          payload.
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

---

## 13. `frontend/src/components/Navbar.tsx`

```tsx
"use client";

import React from "react";
import {
  ShieldAlert,
  AlertOctagon,
  Wifi,
  WifiOff,
  LogOut,
  Sliders,
} from "lucide-react";
import {
  ExecutionModeType,
  ScenarioType,
  StatusLevelType,
  UserProfile,
} from "@/types/astrohealth";

interface NavbarProps {
  user: UserProfile | null;
  overallStatus: StatusLevelType;
  wsConnected: boolean;
  aiMode: ExecutionModeType;
  onTriggerScenario: (scenario: ScenarioType) => Promise<void>;
  onOpenTraumaModal: () => void;
  onLogout: () => void;
}

export default function Navbar({
  user,
  overallStatus,
  wsConnected,
  aiMode,
  onTriggerScenario,
  onOpenTraumaModal,
  onLogout,
}: NavbarProps) {
  return (
    <header className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur border-b border-slate-800">
      {/* Persistent Regulatory Medical Prototype Disclaimer Banner */}
      <div className="bg-amber-950/90 border-b border-amber-700/80 px-4 py-1.5 text-center text-[11px] font-mono text-amber-200 flex items-center justify-center gap-2">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>
          CLINICAL DECISION-SUPPORT PROTOTYPE — SYNTHETIC DEMO DATA ONLY — NOT A
          CERTIFIED MEDICAL DEVICE
        </span>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold ${
              overallStatus === "RED"
                ? "bg-red-600 text-white animate-pulse"
                : overallStatus === "YELLOW"
                ? "bg-amber-400 text-slate-950"
                : "bg-emerald-500 text-slate-950"
            }`}
          >
            STATUS: {overallStatus}
          </span>
          <div>
            <h1 className="text-base font-bold text-white leading-tight">
              AstroHealth AI Console
            </h1>
            <p className="text-xs text-slate-400 font-mono">
              {user ? `${user.full_name} [${user.role}]` : "Unauthenticated"}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* WebSocket Stream Status */}
          <span
            className={`px-2.5 py-1 rounded-lg border text-xs font-mono flex items-center gap-1.5 ${
              wsConnected
                ? "bg-slate-900 border-emerald-700 text-emerald-300"
                : "bg-slate-900 border-rose-700 text-rose-300"
            }`}
          >
            {wsConnected ? (
              <Wifi className="w-3.5 h-3.5" />
            ) : (
              <WifiOff className="w-3.5 h-3.5" />
            )}
            {wsConnected ? "TELEMETRY LIVE (2s)" : "WS OFFLINE"}
          </span>

          {/* AI Engine Mode Badge */}
          <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-cyan-300">
            AI: {aiMode}
          </span>

          {/* Golden Scenario Injector Dropdown */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            <select
              aria-label="Inject Golden Spaceflight Scenario"
              defaultValue="NOMINAL_BASELINE"
              onChange={(e) =>
                onTriggerScenario(e.target.value as ScenarioType)
              }
              className="bg-transparent text-xs text-white font-mono focus:outline-none"
            >
              <option value="NOMINAL_BASELINE" className="bg-slate-900">
                Scenario: Nominal Baseline (GREEN)
              </option>
              <option
                value="SANS_OCULAR_AND_RADIATION_SPIKE"
                className="bg-slate-900"
              >
                Scenario: SANS + Radiation Spike (4 YELLOW)
              </option>
              <option value="CIRCADIAN_FATIGUE_DRIFT" className="bg-slate-900">
                Scenario: Circadian Fatigue Drift (3 YELLOW)
              </option>
              <option value="CARDIO_HYPERTENSION" className="bg-slate-900">
                Scenario: Cardio Hypertension (RED Escalation)
              </option>
              <option value="STOP" className="bg-slate-900">
                Scenario: Pause Simulator (STOP)
              </option>
            </select>
          </div>

          {/* Persistent Zero-Latency Red Button */}
          <button
            type="button"
            onClick={onOpenTraumaModal}
            className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-black text-xs tracking-wider uppercase flex items-center gap-1.5 shadow-lg shadow-red-900/50"
          >
            <AlertOctagon className="w-4 h-4" />
            TRAUMA OVERRIDE
          </button>

          <button
            type="button"
            onClick={onLogout}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
```

---

## 14. `frontend/src/app/layout.tsx` & `frontend/src/app/page.tsx`

### `frontend/src/app/layout.tsx`
```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AstroHealth AI — Autonomous Spaceflight Medical Console",
  description:
    "Edge-computed space health telemetry, Digital Twin, and NASA HRP RAG prototype.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
```

### `frontend/src/app/page.tsx`
```tsx
"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import TelemetryCharts from "@/components/TelemetryCharts";
import DigitalTwinSvg from "@/components/DigitalTwinSvg";
import AnomalyAlertsFeed from "@/components/AnomalyAlertsFeed";
import RagDiagnosticsPanel from "@/components/RagDiagnosticsPanel";
import CountermeasureList from "@/components/CountermeasureList";
import MissionSyncPanel from "@/components/MissionSyncPanel";
import TraumaOverrideModal from "@/components/TraumaOverrideModal";
import { useTelemetrySocket } from "@/hooks/useTelemetrySocket";
import {
  apiClient,
  clearStoredAuth,
  getStoredToken,
  prefetchTraumaProtocols,
} from "@/lib/apiClient";
import {
  BodyRegionType,
  DiagnosticConsultation,
  ExecutionModeType,
  ScenarioType,
  SyncReport,
  TreatmentTask,
  UserProfile,
} from "@/types/astrohealth";

export default function MissionControlDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [aiMode, setAiMode] = useState<ExecutionModeType>("OFFLINE_FALLBACK");
  const [selectedRegion, setSelectedRegion] =
    useState<BodyRegionType>("OCULAR_EYES");
  const [consultations, setConsultations] = useState<DiagnosticConsultation[]>(
    []
  );
  const [tasks, setTasks] = useState<TreatmentTask[]>([]);
  const [reports, setReports] = useState<SyncReport[]>([]);
  const [traumaOpen, setTraumaOpen] = useState(false);

  const {
    readings,
    overallStatus,
    regionStatuses,
    activeAlerts,
    setActiveAlerts,
    wsConnected,
    refreshInitialSnapshot,
  } = useTelemetrySocket();

  const loadClinicalRecords = useCallback(async () => {
    try {
      const [health, consultList, taskList, reportList] = await Promise.all([
        apiClient.getHealth(false),
        apiClient.listConsultations(),
        apiClient.listTasks(),
        apiClient.listSyncReports(),
      ]);
      setAiMode(health.ai_provider_mode);
      setConsultations(consultList);
      setTasks(taskList);
      setReports(reportList);
    } catch {
      // Handled gracefully
    }
  }, []);

  useEffect(() => {
    prefetchTraumaProtocols();
    const token = getStoredToken();
    if (!token) {
      router.push("/login");
      return;
    }
    const rawUser = window.localStorage.getItem("astrohealth_user_profile");
    if (rawUser) {
      try {
        setUser(JSON.parse(rawUser));
      } catch {
        // Ignore parse error
      }
    }
    loadClinicalRecords();
  }, [router, loadClinicalRecords]);

  const handleTriggerScenario = async (scenario: ScenarioType) => {
    await apiClient.simulateScenario(scenario, user?.id, 1.0);
    await refreshInitialSnapshot();
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    await apiClient.acknowledgeAlert(alertId);
    setActiveAlerts((prev) => prev.filter((a) => a.id !== alertId));
    await refreshInitialSnapshot();
  };

  const handleSubmitConsultation = async (
    region: BodyRegionType,
    symptomQuery: string,
    voiceStress: number
  ) => {
    const created = await apiClient.createConsultation({
      body_region: region,
      symptom_query: symptomQuery,
      voice_stress_score: voiceStress,
    });
    setAiMode(created.execution_mode);
    setConsultations((prev) => [created, ...prev]);
    if (created.generated_tasks.length > 0) {
      setTasks((prev) => [...created.generated_tasks, ...prev]);
    }
  };

  const handleCompleteTask = async (taskId: string) => {
    await apiClient.completeTask(taskId);
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, is_completed: true } : t))
    );
  };

  const handleGenerateReport = async () => {
    const created = await apiClient.createSyncReport(user?.id);
    setReports((prev) => [created, ...prev]);
  };

  const handleLogout = () => {
    clearStoredAuth();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        user={user}
        overallStatus={overallStatus}
        wsConnected={wsConnected}
        aiMode={aiMode}
        onTriggerScenario={handleTriggerScenario}
        onOpenTraumaModal={() => setTraumaOpen(true)}
        onLogout={handleLogout}
      />

      <main className="max-w-7xl w-full mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 2D SVG Digital Twin & Proactive Anomaly Alerts (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <DigitalTwinSvg
            regionStatuses={regionStatuses}
            selectedRegion={selectedRegion}
            onSelectRegion={setSelectedRegion}
          />
          <AnomalyAlertsFeed
            alerts={activeAlerts}
            onAcknowledge={handleAcknowledgeAlert}
          />
        </div>

        {/* Right Column: Live Telemetry Charts, RAG Diagnostics, Tasks & Earth Sync (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          <TelemetryCharts readings={readings} />
          <RagDiagnosticsPanel
            selectedRegion={selectedRegion}
            consultations={consultations}
            onSubmitConsultation={handleSubmitConsultation}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <CountermeasureList
              tasks={tasks}
              onCompleteTask={handleCompleteTask}
            />
            <MissionSyncPanel
              reports={reports}
              onGenerateReport={handleGenerateReport}
              onVerifyReport={(id) => apiClient.verifySyncReport(id)}
              onTamperReport={(id) =>
                apiClient.tamperSyncReportDemo(id).then(() => undefined)
              }
            />
          </div>
        </div>
      </main>

      <TraumaOverrideModal
        isOpen={traumaOpen}
        onClose={() => setTraumaOpen(false)}
      />
    </div>
  );
}
```