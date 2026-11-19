// AstroHealth AI - Backend API Integration Client

const API_BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "http://127.0.0.1:8000/api/v1";
export const WS_BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_WS_URL) || "ws://127.0.0.1:8000/ws/telemetry";

const TOKEN_KEY = "astrohealth_jwt_token";
const USER_KEY = "astrohealth_user_profile";

export function getStoredToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setStoredAuth(token, user) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch (e) {
    console.error("Failed to store auth:", e);
  }
}

export function clearStoredAuth() {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {}
}

async function request(path, options = {}, requireAuth = true) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (requireAuth) {
    const token = getStoredToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const url = `${API_BASE}${path}`;
  const res = await fetch(url, { ...options, headers });

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      if (err?.error?.message) {
        msg = err.error.message;
      } else if (err?.detail) {
        msg = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
      }
    } catch {}
    const error = new Error(msg);
    error.status = res.status;
    throw error;
  }

  return res.json();
}

export const api = {
  // Health
  health: (live = false) => request(`/health?live_check=${live ? "true" : "false"}`, { method: "GET" }, false),

  // Authentication & Crew Manifest
  login: async (email, password) => {
    const data = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false);
    setStoredAuth(data.access_token, data.user);
    return data;
  },

  getMe: () => request("/auth/me", { method: "GET" }),

  listCrew: () => request("/auth/users", { method: "GET" }, false),

  switchUser: async (userId) => {
    const data = await request("/auth/switch", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }, false);
    setStoredAuth(data.access_token, data.user);
    return data;
  },

  createAstronaut: async (payload) => {
    const data = await request("/auth/users", {
      method: "POST",
      body: JSON.stringify(payload),
    }, false);
    setStoredAuth(data.access_token, data.user);
    return data;
  },

  // Telemetry & Alerts
  getLatestTelemetry: (userId, limit = 30) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (userId) q.set("user_id", userId);
    return request(`/telemetry/latest?${q.toString()}`);
  },

  simulateScenario: (scenario, targetUserId, timeCompression = 1.0) =>
    request("/telemetry/simulate-scenario", {
      method: "POST",
      body: JSON.stringify({
        scenario,
        target_user_id: targetUserId,
        time_compression: timeCompression,
      }),
    }),

  acknowledgeAlert: (alertId) =>
    request(`/alerts/${alertId}/acknowledge`, { method: "PATCH" }),

  // Clinical Consultations & RAG
  createConsultation: (payload) =>
    request("/consultations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listConsultations: (userId) => {
    const q = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return request(`/consultations${q}`);
  },

  // Interactive AI Medical Chat
  sendChatMessage: (payload) =>
    request("/clinical/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Emergency Scenarios & Simulations
  listEmergencyScenarios: () =>
    request("/emergency/scenarios", { method: "GET" }, false),

  simulateEmergency: (payload) =>
    request("/emergency/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Treatment Tasks / Countermeasure Schedule
  listTasks: (userId) => {
    const q = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return request(`/tasks${q}`);
  },

  completeTask: (taskId) =>
    request(`/tasks/${taskId}/complete`, { method: "PATCH" }),

  // Trauma Protocols
  // Zero-auth, offline-safe: network -> localStorage cache -> bundled fallback JSON
  getTraumaProtocols: async () => {
    const CACHE_KEY = "astrohealth_trauma_protocols";
    try {
      const data = await request("/trauma-protocols", { method: "GET" }, false);
      if (Array.isArray(data) && data.length > 0) {
        try { localStorage.setItem(CACHE_KEY, JSON.stringify(data)); } catch {}
        return data;
      }
    } catch {}
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
      if (Array.isArray(cached) && cached.length > 0) return cached;
    } catch {}
    const res = await fetch("/trauma_protocols.fallback.json");
    if (!res.ok) throw new Error("Trauma protocol fallback unavailable");
    return res.json();
  },

  // Mission Control Sync & Integrity
  createSyncReport: (targetUserId) =>
    request("/reports/sync", {
      method: "POST",
      body: JSON.stringify({ target_user_id: targetUserId }),
    }),

  listSyncReports: (userId) => {
    const q = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return request(`/reports${q}`);
  },

  verifySyncReport: (reportId) =>
    request(`/reports/${reportId}/verify`, { method: "GET" }),

  tamperSyncReportDemo: (reportId) =>
    request(`/reports/${reportId}/tamper-demo`, { method: "POST" }),
};
