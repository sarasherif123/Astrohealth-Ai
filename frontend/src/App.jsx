import { useState, useEffect, useRef } from "react";
import { Ic, P } from "./components/Icon";
import { Spark, Chart } from "./components/Charts";
import { wave, SYS, NAV, ALERTS, SYS_MAP } from "./data";
import { api, getStoredUser, clearStoredAuth } from "./api";
import IMG from "./assets/body.jpg";

export default function App() {
  // Navigation & Core States
  const [nav, setNav] = useState("Overview");
  const [sys, setSys] = useState(SYS[0][0]);
  const [part, setPart] = useState("Chest");
  const [txt, setTxt] = useState("");
  const [reply, setReply] = useState("Awaiting clinical input. Enter symptoms above for grounded NASA HRP assessment.");
  const [replyCitations, setReplyCitations] = useState([]);
  const [assessLoading, setAssessLoading] = useState(false);

  // Astronaut & Auth
  const [user, setUser] = useState(getStoredUser() || {
    id: "550e8400-e29b-41d4-a716-446655440000",
    full_name: "Cmdr. Mark Watney",
    role: "ASTRONAUT",
    baseline_hr_bpm: 64,
    baseline_spo2_pct: 98.5,
    baseline_sys_bp: 118,
    baseline_dia_bp: 75,
  });
  const [crewList, setCrewList] = useState([]);
  const [crewModal, setCrewModal] = useState(false);
  const [newCrewName, setNewCrewName] = useState("");
  const [newCrewRole, setNewCrewRole] = useState("ASTRONAUT");

  // Vitals & Telemetry
  const [sec, setSec] = useState(12 * 86400 + 4 * 3600 + 32 * 60);
  const [ago, setAgo] = useState(2);
  const [isConnected, setIsConnected] = useState(true);
  const [telemetry, setTelemetry] = useState(null);
  const [activeAlerts, setActiveAlerts] = useState([]);

  // Modals & Trauma
  const [modal, setModal] = useState(false);
  const [traumaProtocols, setTraumaProtocols] = useState([]);

  // Countermeasure Schedule / Tasks
  const [tasks, setTasks] = useState([]);

  // Mission Sync
  const [syncReports, setSyncReports] = useState([]);
  const [syncVerifyStatus, setSyncVerifyStatus] = useState(null);

  // AI Medical Chat View States
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      content: "Hello Commander. I am AstroHealth AI, your onboard flight surgeon assistant. How are you feeling today?",
      severity: "NOMINAL",
      follow_up_questions: [
        "How are your energy and sleep levels today?",
        "Are you experiencing any headache, visual changes, or nausea?",
        "Explain the medical risks of microgravity."
      ],
      citations: [
        {
          document_title: "NASA Spaceflight Medical Operations: Clinical Guidance Summary",
          page_number: 1,
          snippet: "Onboard clinical decision support assists crew members in diagnosing and managing microgravity health concerns."
        }
      ]
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Emergency Simulation States
  const [emergencyScenarios, setEmergencyScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("CHEST_PAIN");
  const [customSymptoms, setCustomSymptoms] = useState("");
  const [emergencyResult, setEmergencyResult] = useState(null);
  const [emergencyLoading, setEmergencyLoading] = useState(false);
  const [pastSimulations, setPastSimulations] = useState([]);

  // Mission Elapsed Time timer
  useEffect(() => {
    const t = setInterval(() => setSec((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const met = `${Math.floor(sec / 86400)}d ${String(Math.floor((sec % 86400) / 3600)).padStart(2, "0")}h ${String(
    Math.floor((sec % 3600) / 60)
  ).padStart(2, "0")}m`;

  // Initial Data Load & Authentication
  useEffect(() => {
    let mounted = true;

    async function init() {
      try {
        // Auto-login as default astronaut if token not present
        let currentUser = getStoredUser();
        if (currentUser) {
          // Stored token may be expired, or the DB may have been re-seeded (user ids changed)
          try {
            const me = await api.getMe();
            currentUser = me;
            if (mounted) setUser(me);
          } catch (e) {
            if (e?.status === 401 || e?.status === 404) {
              console.warn("Stored session invalid, re-authenticating:", e);
              clearStoredAuth();
              currentUser = null;
            } else {
              console.warn("Backend unreachable, keeping stored session:", e);
            }
          }
        }
        if (!currentUser) {
          try {
            const loginRes = await api.login("mark.watney@nasa.gov", "MarsMission2026!");
            if (mounted) {
              currentUser = loginRes.user;
              setUser(currentUser);
            }
          } catch (e) {
            console.warn("Auto-login fallback:", e);
          }
        }

        // Fetch Health
        try {
          const health = await api.health();
          if (mounted) setIsConnected(health.status === "ok");
        } catch {
          if (mounted) setIsConnected(false);
        }

        // Fetch Crew Manifest
        try {
          const crew = await api.listCrew();
          if (mounted && Array.isArray(crew)) setCrewList(crew);
        } catch (e) {
          console.warn("Crew manifest fetch:", e);
        }

        // Fetch Telemetry
        const uid = currentUser?.id || user.id;
        refreshTelemetry(uid);

        // Fetch Trauma Protocols
        try {
          const tp = await api.getTraumaProtocols();
          if (mounted && Array.isArray(tp)) setTraumaProtocols(tp);
        } catch (e) {
          console.warn("Trauma protocols fetch:", e);
        }

        // Fetch Emergency Scenarios
        try {
          const scens = await api.listEmergencyScenarios();
          if (mounted && Array.isArray(scens)) {
            setEmergencyScenarios(scens);
            if (scens.length > 0 && !selectedScenarioId) {
              setSelectedScenarioId(scens[0].scenario_id);
            }
          }
        } catch (e) {
          console.warn("Emergency scenarios fetch:", e);
        }

        // Fetch Tasks
        refreshTasks(uid);

        // Fetch Consultations / Past Simulations
        refreshConsultations(uid);

        // Fetch Sync Reports
        refreshSyncReports(uid);
      } catch (err) {
        console.error("Initialization error:", err);
      }
    }

    init();

    return () => {
      mounted = false;
    };
  }, []);

  // Poll telemetry & alerts for the *currently selected* astronaut (re-armed on crew switch)
  useEffect(() => {
    if (!user?.id) return undefined;
    const uid = user.id;
    const poller = setInterval(() => refreshTelemetry(uid), 4000);
    return () => clearInterval(poller);
  }, [user?.id]);

  async function refreshTelemetry(uid) {
    try {
      const data = await api.getLatestTelemetry(uid, 30);
      setTelemetry(data);
      if (data?.active_alerts) {
        setActiveAlerts(data.active_alerts);
      }
      setIsConnected(true);
    } catch (e) {
      // Offline fallback
      setIsConnected(false);
    }
  }

  async function refreshTasks(uid) {
    try {
      const t = await api.listTasks(uid);
      if (Array.isArray(t)) setTasks(t);
    } catch (e) {
      console.warn("Tasks fetch error:", e);
    }
  }

  async function refreshConsultations(uid) {
    try {
      const c = await api.listConsultations(uid);
      if (Array.isArray(c)) setPastSimulations(c);
    } catch (e) {
      console.warn("Consultations fetch error:", e);
    }
  }

  async function refreshSyncReports(uid) {
    try {
      const r = await api.listSyncReports(uid);
      if (Array.isArray(r)) setSyncReports(r);
    } catch (e) {
      console.warn("Sync reports fetch error:", e);
    }
  }

  // Switch astronaut
  async function handleSwitchCrew(selectedUid) {
    try {
      const res = await api.switchUser(selectedUid);
      setUser(res.user);
      setCrewModal(false);
      refreshTelemetry(res.user.id);
      refreshTasks(res.user.id);
      refreshConsultations(res.user.id);
      refreshSyncReports(res.user.id);
    } catch (err) {
      alert("Failed to switch crew: " + err.message);
    }
  }

  // Create new astronaut
  async function handleCreateAstronaut(e) {
    e.preventDefault();
    if (!newCrewName.trim()) return;
    try {
      const res = await api.createAstronaut({
        full_name: newCrewName.trim(),
        role: newCrewRole,
      });
      setUser(res.user);
      setNewCrewName("");
      setCrewModal(false);
      const updatedCrew = await api.listCrew();
      setCrewList(updatedCrew);
      refreshTelemetry(res.user.id);
    } catch (err) {
      alert("Registration error: " + err.message);
    }
  }

  // Quick Assessment on Overview Page
  const assess = async () => {
    if (!txt.trim()) {
      setReply("Please describe your symptoms so the assistant can assess them.");
      setReplyCitations([]);
      return;
    }

    setAssessLoading(true);
    try {
      const bodyRegion = SYS_MAP[part] || "CARDIOVASCULAR";
      const result = await api.createConsultation({
        target_user_id: user?.id,
        body_region: bodyRegion,
        symptom_query: txt.trim(),
        voice_stress_score: 0.15,
      });

      setReply(result.ai_diagnosis);
      setReplyCitations(result.citations || []);
      refreshTasks(user?.id);
      refreshConsultations(user?.id);
    } catch (err) {
      setReply(
        `[Offline Mode] Assessment for ${part.toLowerCase()}: "${txt.trim()}". Vitals are currently monitored. Rest, hydrate, and notify Mission Control if symptoms progress.`
      );
    } finally {
      setAssessLoading(false);
    }
  };

  // Acknowledge Alert
  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      refreshTelemetry(user?.id);
    } catch (err) {
      console.error("Alert acknowledge error:", err);
    }
  };

  // Complete Task
  const handleCompleteTask = async (taskId) => {
    try {
      await api.completeTask(taskId);
      refreshTasks(user?.id);
    } catch (err) {
      alert("Task completion error: " + err.message);
    }
  };

  // Sync now
  const sync = async () => {
    try {
      const report = await api.createSyncReport(user?.id);
      setAgo(0);
      const verify = await api.verifySyncReport(report.id);
      setSyncVerifyStatus(verify);
      refreshSyncReports(user?.id);
    } catch (err) {
      setAgo(0);
      alert("Mission Control sync error: " + err.message);
    }
  };

  // AI Medical Chat Handlers
  const handleSendChat = async (messageText = chatInput) => {
    const textToSend = messageText.trim();
    if (!textToSend || chatLoading) return;

    const newHistory = [...chatMessages, { role: "user", content: textToSend }];
    setChatMessages(newHistory);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await api.sendChatMessage({
        message: textToSend,
        history: chatMessages.slice(-6).map((m) => ({ role: m.role, content: m.content })),
        target_user_id: user?.id,
        body_region: "SYSTEMIC",
      });

      setChatMessages([
        ...newHistory,
        {
          role: "assistant",
          content: res.reply,
          severity: res.severity,
          follow_up_questions: res.follow_up_questions,
          citations: res.citations,
          suggested_actions: res.suggested_actions,
        },
      ]);
      refreshConsultations(user?.id);
    } catch (err) {
      setChatMessages([
        ...newHistory,
        {
          role: "assistant",
          content: `AstroHealth edge diagnostic note: Received inquiry: "${textToSend}". Please verify Astroskin vitals, avoid strenuous exertion, and consult CMO Lewis if symptoms persist. (Error: ${err.message})`,
          severity: "MODERATE",
          follow_up_questions: ["What is your current Astroskin heart rate?", "Are symptoms worsening with movement?"],
          citations: [],
        },
      ]);
    } finally {
      setChatLoading(false);
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  // Start Emergency Simulation
  const handleStartEmergency = async () => {
    setEmergencyLoading(true);
    try {
      const res = await api.simulateEmergency({
        scenario_id: selectedScenarioId,
        custom_symptoms: customSymptoms.trim() || undefined,
        target_user_id: user?.id,
        trigger_telemetry: true,
      });
      setEmergencyResult(res);
      refreshTelemetry(user?.id);
      refreshTasks(user?.id);
      refreshConsultations(user?.id);
    } catch (err) {
      alert("Emergency simulation error: " + err.message);
    } finally {
      setEmergencyLoading(false);
    }
  };

  // End / Reset Simulation
  const handleResetSimulation = async () => {
    try {
      await api.simulateScenario("NOMINAL_BASELINE", user?.id);
      setEmergencyResult(null);
      setCustomSymptoms("");
      refreshTelemetry(user?.id);
    } catch (err) {
      console.error("Reset simulation error:", err);
    }
  };

  // Telemetry metric extraction
  const readings = telemetry?.readings || [];
  const latest = readings[readings.length - 1];

  const hr = latest?.heart_rate_bpm ?? 72;
  const spo2 = latest?.spo2_pct ? `${latest.spo2_pct.toFixed(1)}%` : "98.5%";
  const temp = latest?.core_temp_c ? `${latest.core_temp_c.toFixed(1)}°C` : "36.6°C";
  const sleep = latest?.sleep_score ?? 88;
  const rad = latest?.radiation_msv ? `${latest.radiation_msv.toFixed(2)}` : "0.32";
  const overallStatus = telemetry?.overall_status || "GREEN";

  // Real chart series
  const hrSeries = readings.length > 0 ? readings.map((r) => r.heart_rate_bpm) : wave(72, 5, 24, 0);
  const bpSeries = readings.length > 0 ? readings.map((r) => r.systolic_bp_mmhg) : wave(118, 8, 24, 1.5);
  const sleepSeries = readings.length > 0 ? readings.map((r) => r.sleep_score) : [94, 90, 85, 90, 94, 88, 84, 90, 94];
  const fatigueSeries = readings.length > 0
    ? readings.map((r) => Math.round(r.eeg_fatigue_index * 100))
    : [20, 24, 30, 35, 40, 32, 28, 30, 34];

  // User initials
  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "MW";

  const kp = (t, ic, v, u, d, dn, pts) => (
    <div className="card kpi">
      <h4>
        <Ic d={P[ic]} c="#00e5ff" s={18} />
        {t}
      </h4>
      <div className="v">
        {v}
        <small> {u}</small>
      </div>
      <div className={"d " + (dn ? "dn" : "")}>{d}</div>
      <Spark pts={pts} c={dn ? "#ef4444" : "#00e5ff"} />
    </div>
  );

  return (
    <div className="app">
      {/* Sidebar Navigation */}
      <aside>
        <div className="logo">
          <svg width="44" height="44" viewBox="0 0 48 48" fill="none" stroke="#00e5ff" strokeWidth="2.5">
            <ellipse cx="24" cy="24" rx="20" ry="9" transform="rotate(-30 24 24)" />
            <circle cx="24" cy="24" r="8" fill="rgba(0,229,255,0.15)" />
          </svg>
          <div>
            <b>AstroHealth AI</b>
            <small>Deep Space Medical AI System</small>
          </div>
        </div>

        {NAV.map(([n, i]) => (
          <button key={n} className={"nav " + (nav === n ? "on" : "")} onClick={() => setNav(n)}>
            <Ic d={P[i]} s={20} c={nav === n ? "#00e5ff" : "currentColor"} />
            {n}
          </button>
        ))}

        <div className="nasa">
          <i>NASA</i>
          <span>
            <b>NASA HRP Protocol</b>
            <br />
            Deep Space Mission Tier
          </span>
        </div>
      </aside>

      {/* Main Content Area */}
      <main>
        {/* Header Bar */}
        <header>
          <div className="av" onClick={() => setCrewModal(true)} title="Click to switch crew or register astronaut">
            {initials}
          </div>
          <div className="hl">
            <small>Astronaut / Crew Member</small>
            <b>{user?.full_name || "Cmdr. Mark Watney"}</b>
            <small>Role: {user?.role || "ASTRONAUT"} • Manifest: #{user?.id ? user.id.slice(0, 8) : "WATNEY-01"}</small>
          </div>
          <div className="sep" />
          <div className="hl">
            <small>Mission Elapsed Time</small>
            <b style={{ fontSize: 20, color: "#38bdf8", fontFamily: "monospace" }}>{met}</b>
          </div>
          <div className="sep" />
          <div className="hl">
            <small>Telemetry Link</small>
            <b style={{ fontSize: 18, color: isConnected ? "#10b981" : "#f59e0b" }}>
              <span className="on-dot" style={{ background: isConnected ? "#10b981" : "#f59e0b" }} />
              {isConnected ? "Online (NASA JSC)" : "Offline (Edge Fallback)"}
            </b>
          </div>
          <div className="grow" />
          <div className="bell" onClick={() => setNav("Health Monitoring")} title="Active Anomaly Alerts">
            <Ic d={P.bell} s={24} c="#38bdf8" />
            <em>{activeAlerts.length}</em>
          </div>
          <button
            className="btn sec"
            style={{ display: "flex", gap: 6, alignItems: "center" }}
            onClick={() => setCrewModal(true)}
          >
            <Ic d={P.user} s={16} /> Crew Switcher
          </button>
        </header>

        {/* Global KPIs Bar */}
        <div className="kpis">
          <div className={"card kpi " + (overallStatus === "GREEN" ? "g" : "r")}>
            <span
              style={{
                display: "inline-grid",
                placeItems: "center",
                width: 38,
                height: 38,
                borderRadius: "50%",
                background: overallStatus === "GREEN" ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)",
                margin: "0 auto",
                border: `1px solid ${overallStatus === "GREEN" ? "#10b981" : "#ef4444"}`,
              }}
            >
              <Ic d={overallStatus === "GREEN" ? P.check : P.warn} c={overallStatus === "GREEN" ? "#34d399" : "#f87171"} s={22} />
            </span>
            <h4 style={{ justifyContent: "center", marginTop: 6 }}>Overall Health Status</h4>
            <div className="v">{overallStatus === "GREEN" ? "Nominal" : overallStatus === "YELLOW" ? "Caution" : "Emergency"}</div>
            <small className="s">{overallStatus === "GREEN" ? "All vitals in tolerance" : "Telemetry anomaly detected"}</small>
          </div>

          <div className={"card kpi " + (activeAlerts.length > 0 ? "r" : "g")}>
            <Ic d={P.warn} c={activeAlerts.length > 0 ? "#ef4444" : "#10b981"} s={34} />
            <h4 style={{ justifyContent: "center", marginTop: 4 }}>Active Alerts</h4>
            <div className="v">{activeAlerts.length}</div>
            <small className="s">{activeAlerts.length > 0 ? "Requires medical review" : "Zero pending alerts"}</small>
          </div>

          {kp("Heart Rate", "pulse", hr, "bpm", hr > (user?.baseline_hr_bpm || 64) ? `+${hr - (user?.baseline_hr_bpm || 64)} bpm` : "Nominal", hr > 95, hrSeries.slice(-8))}
          {kp("Blood Oxygen (SpO₂)", "drop", spo2, "", parseFloat(spo2) >= 95 ? "Nominal" : "Low SpO₂", parseFloat(spo2) < 95, readings.map((r) => r.spo2_pct).slice(-8))}
          {kp("Body Temperature", "temp", temp, "", "Nominal", parseFloat(temp) > 37.8, readings.map((r) => r.core_temp_c).slice(-8))}
          {kp("Sleep Score", "moon", sleep, "/100", sleep >= 75 ? "Adequate" : "Sleep Debt", sleep < 75, sleepSeries.slice(-8))}
          {kp("Radiation Exposure", "rad", rad, "mSv", parseFloat(rad) > 1.5 ? "SPE Alert" : "Nominal", parseFloat(rad) > 1.5, readings.map((r) => r.radiation_msv).slice(-8))}
        </div>

        {/* ---------------- VIEW 1: OVERVIEW (ORIGINAL PRESERVED LAYOUT) ---------------- */}
        {nav === "Overview" && (
          <>
            <div className="row r1" style={{ gridTemplateColumns: "1.15fr 1.15fr .8fr" }}>
              <div className="card">
                <h3>
                  <span><Ic d={P.pulse} c="#00e5ff" s={18} /> Cardiovascular Telemetry</span>
                  <span style={{ fontSize: 12, fontWeight: 400, color: "#8b9bb4" }}>Recent 30 Cycles ▾</span>
                </h3>
                <div className="leg">
                  <span><i style={{ background: "#00e5ff" }} /> Heart Rate (bpm)</span>
                  <span><i style={{ background: "#38bdf8" }} /> Blood Pressure (mmHg)</span>
                </div>
                <Chart
                  ymin={40}
                  ymax={180}
                  yt={[40, 80, 120, 160]}
                  xl={["T-30m", "T-20m", "T-15m", "T-10m", "T-5m", "Now"]}
                  series={[
                    { n: "hr", c: "#00e5ff", v: hrSeries, dots: 3 },
                    { n: "bp", c: "#38bdf8", v: bpSeries, dots: 3 },
                  ]}
                />
              </div>

              <div className="card">
                <h3>
                  <span><Ic d={P.moon} c="#a855f7" s={18} /> Sleep Quality and Fatigue Trends</span>
                </h3>
                <div className="leg">
                  <span><i style={{ background: "#00e5ff" }} /> Sleep Quality</span>
                  <span><i style={{ background: "#a855f7" }} /> Fatigue Index</span>
                </div>
                <Chart
                  ymin={0}
                  ymax={100}
                  yt={[0, 25, 50, 75, 100]}
                  xl={["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6"]}
                  series={[
                    { n: "s", c: "#00e5ff", v: sleepSeries, dots: 2 },
                    { n: "f", c: "#a855f7", v: fatigueSeries, dots: 2 },
                  ]}
                />
              </div>

              <div className="card">
                <h3>
                  <span><Ic d={P.user} c="#00e5ff" s={18} /> Digital Twin Telemetry</span>
                </h3>
                <div className="twin">
                  <div className="body">
                    <img src={IMG} alt="Digital twin anatomical body model" />
                  </div>
                  <div className="tabs">
                    {SYS.map(([n, i, key]) => {
                      const regionStatus = telemetry?.region_statuses?.[key] || "GREEN";
                      return (
                        <button
                          key={n}
                          className={"tab " + (sys === n ? "on" : "")}
                          onClick={() => setSys(n)}
                        >
                          <Ic d={P[i]} s={16} c={regionStatus === "RED" ? "#ef4444" : regionStatus === "YELLOW" ? "#f59e0b" : "#38bdf8"} />
                          <span style={{ flex: 1 }}>{n}</span>
                          <span
                            style={{
                              width: 8,
                              height: 8,
                              borderRadius: "50%",
                              background: regionStatus === "RED" ? "#ef4444" : regionStatus === "YELLOW" ? "#f59e0b" : "#10b981",
                            }}
                          />
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

            <div className="row r2" style={{ gridTemplateColumns: "1.15fr 1.15fr .8fr" }}>
              <div className="card">
                <h3>
                  <span><Ic d={P.bell} c="#00e5ff" s={18} /> Active Medical Anomaly Alerts</span>
                  <a
                    href="#"
                    style={{ fontSize: 12, color: "#38bdf8", textDecoration: "none" }}
                    onClick={(e) => {
                      e.preventDefault();
                      setNav("Health Monitoring");
                    }}
                  >
                    View All →
                  </a>
                </h3>
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Severity</th>
                      <th>Issue / Rule</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeAlerts.length > 0 ? (
                      activeAlerts.map((a) => (
                        <tr key={a.id}>
                          <td style={{ fontSize: 11, color: "#8b9bb4" }}>
                            {new Date(a.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </td>
                          <td>
                            <span className={"pill " + a.severity}>{a.severity}</span>
                          </td>
                          <td style={{ fontWeight: 500 }}>{a.title}</td>
                          <td>
                            <button className="btn" onClick={() => handleAcknowledge(a.id)}>
                              Acknowledge
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} style={{ textAlign: "center", color: "#8b9bb4", padding: 18 }}>
                          ✓ No active medical anomalies. All systems nominal.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="card">
                <h3>
                  <span><Ic d={P.chat} c="#00e5ff" s={18} /> AI Medical Assistant (Quick Triage)</span>
                  <button className="btn sec" style={{ fontSize: 11 }} onClick={() => setNav("AI Medical Assistant")}>
                    Open Full Chat →
                  </button>
                </h3>
                <div className="ai">
                  <select value={part} onChange={(e) => setPart(e.target.value)}>
                    {["Chest", "Head", "Abdomen", "Arms", "Legs"].map((o) => (
                      <option key={o}>{o}</option>
                    ))}
                  </select>
                  <input
                    value={txt}
                    onChange={(e) => setTxt(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && assess()}
                    placeholder="Describe symptoms in natural language..."
                    aria-label="Symptoms"
                  />
                  <button className="btn" onClick={assess} disabled={assessLoading}>
                    {assessLoading ? "Assessing..." : "Assess"}
                  </button>
                </div>
                <div className="reply">{reply}</div>
                <div className="ref">
                  References:{" "}
                  {replyCitations.length > 0 ? (
                    replyCitations.map((c, idx) => (
                      <span key={idx} style={{ color: "#38bdf8", marginRight: 8 }}>
                        {c.document_title} (p.{c.page_number})
                      </span>
                    ))
                  ) : (
                    <a href="#" onClick={(e) => e.preventDefault()}>NASA HRP – Spaceflight Clinical Evidence Base ↗</a>
                  )}
                </div>
              </div>

              <div>
                <button className="trauma" onClick={() => setModal(true)}>
                  <Ic d={P.warn} s={32} />
                  <span>
                    <b>Trauma Override</b>
                    <small>Emergency Protocols • Offline Zero-Auth</small>
                  </span>
                  <span style={{ marginLeft: "auto", fontSize: 20 }}>→</span>
                </button>
                <div className="card">
                  <h3>
                    <span><Ic d={P.sync} c="#00e5ff" s={18} /> Mission Control Sync</span>
                    <button className="btn" onClick={sync}>Sync now</button>
                  </h3>
                  <div className="sync">
                    Sync Status: <i />
                    Successful (Houston Link)
                    <br />
                    Last Sync: {ago === 0 ? "just now" : `${ago} min ago`}
                    <br />
                    Data Integrity: <i />
                    Verified (HMAC-SHA256)
                    {syncVerifyStatus?.verified && (
                      <span style={{ display: "block", color: "#34d399", fontSize: 11, marginTop: 4 }}>
                        ✓ Cryptographic signature match ({syncVerifyStatus.stored_hmac.slice(0, 8)}...)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* ---------------- VIEW 2: HEALTH MONITORING (TELEMETRY & SCENARIOS) ---------------- */}
        {nav === "Health Monitoring" && (
          <div className="card" style={{ marginBottom: 14 }}>
            <h3>
              <span><Ic d={P.pulse} c="#00e5ff" s={20} /> Physiological Telemetry & Sensor Burst Hub</span>
              <button className="btn sec" onClick={() => refreshTelemetry(user?.id)}>Refresh Feed</button>
            </h3>
            <p style={{ color: "#8b9bb4", fontSize: 13, lineHeight: 1.6 }}>
              Live biosensor telemetry received from the Astroskin Smart Harness and habitat environmental sensors.
              You can trigger scenario bursts to test real-time rolling-window anomaly rule evaluation.
            </p>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "14px 0" }}>
              <button className="btn sec" onClick={() => api.simulateScenario("NOMINAL_BASELINE", user?.id).then(() => refreshTelemetry(user?.id))}>
                Nominal Baseline
              </button>
              <button className="btn sec" onClick={() => api.simulateScenario("CARDIO_HYPERTENSION", user?.id).then(() => refreshTelemetry(user?.id))}>
                Simulate Cardio Strain (+45 bpm, 168/104)
              </button>
              <button className="btn sec" onClick={() => api.simulateScenario("SANS_OCULAR_AND_RADIATION_SPIKE", user?.id).then(() => refreshTelemetry(user?.id))}>
                Simulate Radiation Spike (2.1 mSv, SANS)
              </button>
              <button className="btn sec" onClick={() => api.simulateScenario("CIRCADIAN_FATIGUE_DRIFT", user?.id).then(() => refreshTelemetry(user?.id))}>
                Simulate Circadian Fatigue (EEG 0.76)
              </button>
            </div>

            <div className="row" style={{ gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 14 }}>
              <div>
                <h4 style={{ color: "#f8fafc", margin: "0 0 8px" }}>Cardiovascular Telemetry (Last 30 Readings)</h4>
                <Chart
                  ymin={40}
                  ymax={180}
                  yt={[40, 80, 120, 160]}
                  xl={["T-30", "T-20", "T-10", "Now"]}
                  series={[
                    { n: "hr", c: "#00e5ff", v: hrSeries, dots: 2 },
                    { n: "bp", c: "#38bdf8", v: bpSeries, dots: 2 },
                  ]}
                />
              </div>
              <div>
                <h4 style={{ color: "#f8fafc", margin: "0 0 8px" }}>Active Anomaly Feed & Interventions</h4>
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Severity</th>
                      <th>Rule</th>
                      <th>Micro-Intervention</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeAlerts.map((a) => (
                      <tr key={a.id}>
                        <td style={{ fontSize: 11, color: "#8b9bb4" }}>
                          {new Date(a.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </td>
                        <td><span className={"pill " + a.severity}>{a.severity}</span></td>
                        <td>{a.title}</td>
                        <td style={{ fontSize: 11.5, color: "#cbd5e1" }}>{a.micro_intervention}</td>
                        <td><button className="btn" onClick={() => handleAcknowledge(a.id)}>Ack</button></td>
                      </tr>
                    ))}
                    {activeAlerts.length === 0 && (
                      <tr>
                        <td colSpan={5} style={{ textAlign: "center", color: "#8b9bb4", padding: 18 }}>
                          No active anomalies.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ---------------- VIEW 3: DIGITAL TWIN (SYSTEM-BY-SYSTEM EXPLORER) ---------------- */}
        {nav === "Digital Twin" && (
          <div className="card">
            <h3><span><Ic d={P.user} c="#00e5ff" s={20} /> Spacecraft Digital Twin Anatomical Model</span></h3>
            <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 20, marginTop: 12 }}>
              <div className="body" style={{ minHeight: 380 }}>
                <img src={IMG} alt="Astronaut Digital Twin Body" style={{ maxHeight: 360 }} />
              </div>
              <div>
                <h4 style={{ color: "#f8fafc", margin: "0 0 10px" }}>Organ System Telemetry & Regional Risk Levels</h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {SYS.map(([n, i, key]) => {
                    const st = telemetry?.region_statuses?.[key] || "GREEN";
                    return (
                      <div
                        key={n}
                        style={{
                          background: "#091322",
                          border: `1px solid ${st === "RED" ? "#ef4444" : st === "YELLOW" ? "#f59e0b" : "rgba(56,189,248,0.15)"}`,
                          borderRadius: 8,
                          padding: 12,
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <b style={{ display: "flex", gap: 8, alignItems: "center", color: "#f1f5f9", fontSize: 13 }}>
                            <Ic d={P[i]} s={18} c="#00e5ff" /> {n}
                          </b>
                          <span className={"pill " + (st === "RED" ? "High" : st === "YELLOW" ? "Medium" : "Low")}>
                            {st}
                          </span>
                        </div>
                        <p style={{ fontSize: 12, color: "#8b9bb4", margin: "8px 0 0" }}>
                          {key === "OCULAR_EYES" && "Monitors SANS, choroidal folds, and hyperopic shifts from cephalad fluid shift."}
                          {key === "CARDIOVASCULAR" && "Baroreceptor unloading and orthostatic stability telemetry."}
                          {key === "BRAIN_NEURO" && "Prefrontal fNIRS cognitive fatigue and vestibular adaptation tracking."}
                          {key === "MUSCULOSKELETAL" && "Bone mineral density and antigravity muscle loading sensors."}
                          {key === "GASTROINTESTINAL" && "Microgravity motility and oral hydration absorption efficiency."}
                          {key === "SYSTEMIC" && "Cumulative ionizing dosimetry and core thermal regulation status."}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ---------------- VIEW 4: AI MEDICAL CHAT (INTERACTIVE ASSISTANT) ---------------- */}
        {nav === "AI Medical Assistant" && (
          <div className="card">
            <h3>
              <span><Ic d={P.chat} c="#00e5ff" s={20} /> Interactive AI Medical Assistant</span>
              <span style={{ fontSize: 12, color: "#8b9bb4" }}>Grounded in NASA HRP Protocols</span>
            </h3>

            <div className="chat-container">
              <div className="chat-messages">
                {chatMessages.map((m, idx) => (
                  <div key={idx} className={"chat-msg " + m.role}>
                    <div style={{ fontSize: 11, color: m.role === "user" ? "#bae6fd" : "#38bdf8", marginBottom: 4, fontWeight: 600 }}>
                      {m.role === "user" ? `Astronaut (${user?.full_name})` : "AstroHealth AI (Flight Surgeon Assistant)"}
                      {m.severity && m.severity !== "NOMINAL" && (
                        <span className={"pill " + (m.severity === "CRITICAL" ? "High" : "Medium")} style={{ marginLeft: 8 }}>
                          {m.severity}
                        </span>
                      )}
                    </div>
                    <div style={{ whiteSpace: "pre-line" }}>{m.content}</div>

                    {m.suggested_actions && m.suggested_actions.length > 0 && (
                      <div style={{ marginTop: 8, padding: 8, background: "rgba(0,0,0,0.25)", borderRadius: 6 }}>
                        <b style={{ fontSize: 11.5, color: "#38bdf8" }}>Immediate Actions:</b>
                        <ul style={{ margin: "4px 0 0 16px", padding: 0, fontSize: 12 }}>
                          {m.suggested_actions.map((act, aIdx) => (
                            <li key={aIdx}>{act}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {m.citations && m.citations.length > 0 && (
                      <div style={{ marginTop: 8, fontSize: 11, color: "#94a3b8", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: 6 }}>
                        <b style={{ color: "#38bdf8" }}>NASA HRP Citations:</b>
                        {m.citations.map((c, cIdx) => (
                          <div key={cIdx} style={{ fontStyle: "italic", marginTop: 2 }}>
                            • {c.document_title} (p.{c.page_number}): "{c.snippet}"
                          </div>
                        ))}
                      </div>
                    )}

                    {m.follow_up_questions && m.follow_up_questions.length > 0 && (
                      <div style={{ marginTop: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {m.follow_up_questions.map((fq, qIdx) => (
                          <button
                            key={qIdx}
                            className="btn sec"
                            style={{ fontSize: 11, padding: "4px 8px" }}
                            onClick={() => handleSendChat(fq)}
                          >
                            💬 {fq}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {chatLoading && (
                  <div className="chat-msg assistant" style={{ fontStyle: "italic", color: "#8b9bb4" }}>
                    AstroHealth AI is synthesizing grounded response from NASA Knowledge Base...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="chat-input-bar">
                <input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                  placeholder="Ask a space medical question (e.g. 'I feel sick', 'Severe headache', 'Symptoms of hypoxia')..."
                  style={{
                    flex: 1,
                    background: "#081220",
                    border: "1px solid rgba(56,189,248,0.2)",
                    borderRadius: 8,
                    padding: "10px 14px",
                    color: "#fff",
                    fontSize: 13,
                  }}
                />
                <button className="btn" onClick={() => handleSendChat()} disabled={chatLoading || !chatInput.trim()}>
                  {chatLoading ? "Sending..." : "Send Question"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ---------------- VIEW 5: COUNTERMEASURE SCHEDULE (TASKS) ---------------- */}
        {nav === "Countermeasure Schedule" && (
          <div className="card">
            <h3>
              <span><Ic d={P.cal} c="#00e5ff" s={20} /> Countermeasure Schedule & Treatment Tasks</span>
              <button className="btn sec" onClick={() => refreshTasks(user?.id)}>Refresh Tasks</button>
            </h3>
            <p style={{ color: "#8b9bb4", fontSize: 13 }}>
              Personalized countermeasure sessions prescribed by AstroHealth AI and Flight Surgeon Cruz to counter microgravity deconditioning.
            </p>

            <table>
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Countermeasure Title</th>
                  <th>Clinical Instructions</th>
                  <th>Scheduled For</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <span className="pill Low">{t.task_type}</span>
                    </td>
                    <td style={{ fontWeight: 600, color: "#f1f5f9" }}>{t.title}</td>
                    <td style={{ fontSize: 12, color: "#cbd5e1", maxWidth: 380 }}>{t.instructions}</td>
                    <td style={{ fontSize: 11, color: "#8b9bb4" }}>
                      {new Date(t.scheduled_for).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td>
                      <span className={"pill " + (t.is_completed ? "Low" : "Medium")}>
                        {t.is_completed ? "Completed" : "Scheduled"}
                      </span>
                    </td>
                    <td>
                      {!t.is_completed && (
                        <button className="btn" onClick={() => handleCompleteTask(t.id)}>
                          Mark Done
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {tasks.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", color: "#8b9bb4", padding: 24 }}>
                      No countermeasure tasks scheduled. Tasks are generated automatically when clinical consultations or emergencies occur.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* ---------------- VIEW 6: EMERGENCY PROTOCOLS (AI EMERGENCY SIMULATION) ---------------- */}
        {nav === "Emergency Protocols" && (
          <div className="card">
            <h3>
              <span><Ic d={P.shield} c="#ef4444" s={20} /> Space Medical AI Emergency Simulation System</span>
              {emergencyResult && (
                <button className="btn danger" onClick={handleResetSimulation}>
                  Reset / Nominal Baseline
                </button>
              )}
            </h3>

            <div className="sim-grid" style={{ marginTop: 12 }}>
              {/* Left Column: Configuration Controls */}
              <div>
                <h4 style={{ color: "#f8fafc", margin: "0 0 8px" }}>1. Select Target Astronaut</h4>
                <select
                  value={user?.id}
                  onChange={(e) => handleSwitchCrew(e.target.value)}
                  style={{
                    width: "100%",
                    background: "#081220",
                    border: "1px solid rgba(56,189,248,0.25)",
                    borderRadius: 6,
                    padding: 9,
                    color: "#fff",
                    marginBottom: 16,
                  }}
                >
                  {crewList.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.full_name} ({c.role}) — Base HR: {c.baseline_hr_bpm} bpm
                    </option>
                  ))}
                </select>

                <h4 style={{ color: "#f8fafc", margin: "0 0 8px" }}>2. Select Predefined Medical Emergency</h4>
                <div style={{ maxHeight: 290, overflowY: "auto", paddingRight: 4 }}>
                  {emergencyScenarios.map((sc) => (
                    <div
                      key={sc.scenario_id}
                      className={"scenario-card " + (selectedScenarioId === sc.scenario_id ? "active" : "")}
                      onClick={() => setSelectedScenarioId(sc.scenario_id)}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <b style={{ fontSize: 13, color: "#f8fafc" }}>{sc.title}</b>
                        <span className={"pill " + (sc.severity === "CRITICAL" ? "High" : "Medium")}>{sc.severity}</span>
                      </div>
                      <small style={{ color: "#8b9bb4", display: "block", marginTop: 4 }}>
                        System: {sc.body_region}
                      </small>
                    </div>
                  ))}
                </div>

                <h4 style={{ color: "#f8fafc", margin: "14px 0 6px" }}>3. Custom Symptoms (Natural Language)</h4>
                <textarea
                  value={customSymptoms}
                  onChange={(e) => setCustomSymptoms(e.target.value)}
                  placeholder="Enter optional natural language notes (e.g. 'Feeling sharp substernal pain radiating down left arm, cold sweats')..."
                  rows={3}
                  style={{
                    width: "100%",
                    background: "#081220",
                    border: "1px solid rgba(56,189,248,0.2)",
                    borderRadius: 6,
                    padding: 8,
                    color: "#fff",
                    fontSize: 12.5,
                  }}
                />

                <button
                  className="trauma"
                  style={{ marginTop: 12, justifyContent: "center" }}
                  onClick={handleStartEmergency}
                  disabled={emergencyLoading}
                >
                  <Ic d={P.warn} s={24} />
                  <span><b>{emergencyLoading ? "Simulating Emergency..." : "Start Emergency Simulation"}</b></span>
                </button>
              </div>

              {/* Right Column: AI Emergency Response Output */}
              <div>
                {emergencyResult ? (
                  <div style={{ background: "#0b1627", border: "1px solid rgba(239,68,68,0.4)", borderRadius: 10, padding: 18 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: 10 }}>
                      <div>
                        <h3 style={{ margin: 0, color: "#fff", fontSize: 17 }}>{emergencyResult.scenario_title}</h3>
                        <small style={{ color: "#8b9bb4" }}>Astronaut: {user?.full_name} • Simulation ID: #{emergencyResult.simulation_id.slice(0, 8)}</small>
                      </div>
                      <span className={"pill " + (emergencyResult.severity === "CRITICAL" ? "CRITICAL" : "High")}>
                        SEVERITY: {emergencyResult.severity}
                      </span>
                    </div>

                    {/* Medical Assessment */}
                    <div style={{ margin: "14px 0" }}>
                      <b style={{ color: "#00e5ff", fontSize: 13 }}>Grounded Medical Assessment:</b>
                      <div className="reply" style={{ marginTop: 6, fontSize: 13, background: "#081426" }}>
                        {emergencyResult.medical_assessment}
                      </div>
                    </div>

                    {/* Reported Symptoms & Possible Concerns */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
                      <div style={{ background: "#081220", padding: 12, borderRadius: 8, border: "1px solid rgba(56,189,248,0.12)" }}>
                        <b style={{ color: "#38bdf8", fontSize: 12.5 }}>Reported Symptoms:</b>
                        <ul style={{ margin: "6px 0 0 16px", padding: 0, fontSize: 12, color: "#cbd5e1" }}>
                          {emergencyResult.reported_symptoms.map((s, idx) => (
                            <li key={idx}>{s}</li>
                          ))}
                        </ul>
                      </div>

                      <div style={{ background: "#081220", padding: 12, borderRadius: 8, border: "1px solid rgba(56,189,248,0.12)" }}>
                        <b style={{ color: "#fbbf24", fontSize: 12.5 }}>Possible Spaceflight Concerns:</b>
                        <small style={{ display: "block", color: "#8b9bb4", fontSize: 10.5 }}>Differentiated from confirmed diagnoses</small>
                        <ul style={{ margin: "6px 0 0 16px", padding: 0, fontSize: 12, color: "#cbd5e1" }}>
                          {emergencyResult.possible_concerns.map((c, idx) => (
                            <li key={idx}>{c}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Immediate Step-by-Step Response Instructions */}
                    <div style={{ marginBottom: 14 }}>
                      <b style={{ color: "#34d399", fontSize: 13 }}>Immediate Step-by-Step Response Instructions:</b>
                      <div style={{ marginTop: 8 }}>
                        {emergencyResult.immediate_actions.map((act, idx) => (
                          <div key={idx} className="step-item">
                            <span style={{ color: "#00e5ff", fontWeight: 700, marginRight: 8 }}>✓</span>
                            {act}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Warnings */}
                    {emergencyResult.warnings && emergencyResult.warnings.length > 0 && (
                      <div className="warning-box">
                        <b>Critical Safety Warnings:</b>
                        {emergencyResult.warnings.map((w, idx) => (
                          <div key={idx} style={{ marginTop: 4 }}>• {w}</div>
                        ))}
                      </div>
                    )}

                    {/* Monitoring & Ground Support */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
                      <div style={{ background: "#081220", padding: 10, borderRadius: 6, fontSize: 12, color: "#cbd5e1" }}>
                        <b style={{ color: "#38bdf8" }}>Monitoring Instructions:</b>
                        <ul style={{ margin: "4px 0 0 14px", padding: 0 }}>
                          {emergencyResult.monitoring_instructions.map((m, idx) => (
                            <li key={idx}>{m}</li>
                          ))}
                        </ul>
                      </div>

                      <div style={{ background: "#081220", padding: 10, borderRadius: 6, fontSize: 12, color: "#cbd5e1" }}>
                        <b style={{ color: "#38bdf8" }}>Ground Medical Support:</b>
                        <p style={{ margin: "4px 0 0" }}>{emergencyResult.ground_medical_support}</p>
                      </div>
                    </div>

                    {/* Citations */}
                    {emergencyResult.citations && emergencyResult.citations.length > 0 && (
                      <div style={{ marginTop: 12, fontSize: 11, color: "#8b9bb4" }}>
                        <b>NASA Flight Citations: </b>
                        {emergencyResult.citations.map((c, idx) => (
                          <span key={idx} style={{ marginRight: 10, color: "#38bdf8" }}>
                            {c.document_title} (Page {c.page_number})
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ background: "#081220", border: "1px dashed rgba(56,189,248,0.2)", borderRadius: 10, padding: 36, textAlign: "center", color: "#8b9bb4" }}>
                    <Ic d={P.shield} s={44} c="#00e5ff" />
                    <h4 style={{ color: "#fff", margin: "12px 0 4px" }}>Ready for Emergency Medical Simulation</h4>
                    <p style={{ maxWidth: 440, margin: "0 auto", fontSize: 13, lineHeight: 1.6 }}>
                      Select an astronaut and predefined scenario on the left, optionally enter custom natural language symptoms, and click "Start Emergency Simulation". The system will execute real AI diagnostic analysis, shift biosensor telemetry, and generate grounded emergency protocols.
                    </p>
                  </div>
                )}

                {/* Review Previous Simulations */}
                <div style={{ marginTop: 18 }}>
                  <h4 style={{ color: "#f8fafc", margin: "0 0 8px" }}>Previous Consultations & Emergency Logs</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>System</th>
                        <th>Query / Scenario</th>
                        <th>Confidence</th>
                        <th>Mode</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pastSimulations.slice(0, 5).map((ps) => (
                        <tr key={ps.id}>
                          <td style={{ fontSize: 11, color: "#8b9bb4" }}>
                            {new Date(ps.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </td>
                          <td><span className="pill Low">{ps.body_region}</span></td>
                          <td style={{ maxWidth: 280, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {ps.symptom_query}
                          </td>
                          <td style={{ color: "#34d399" }}>{(ps.confidence_score * 100).toFixed(0)}%</td>
                          <td><small style={{ color: "#8b9bb4" }}>{ps.execution_mode}</small></td>
                        </tr>
                      ))}
                      {pastSimulations.length === 0 && (
                        <tr>
                          <td colSpan={5} style={{ textAlign: "center", color: "#8b9bb4", padding: 12 }}>
                            No past simulations logged.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ---------------- VIEW 7: MISSION CONTROL SYNC ---------------- */}
        {nav === "Mission Control Sync" && (
          <div className="card">
            <h3>
              <span><Ic d={P.sync} c="#00e5ff" s={20} /> Mission Control Synchronization & Telemetry Integrity</span>
              <button className="btn" onClick={sync}>Generate Sync Report</button>
            </h3>
            <p style={{ color: "#8b9bb4", fontSize: 13 }}>
              Deep-space telemetry sync reports cryptographically signed with HMAC-SHA256 to guarantee flight surgeon record integrity against Mars transit bit rot.
            </p>

            <table>
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Created (UTC)</th>
                  <th>Telemetry Count</th>
                  <th>Alerts</th>
                  <th>Consultations</th>
                  <th>HMAC-SHA256 Hash</th>
                  <th>Verification</th>
                  <th>Demo Tamper</th>
                </tr>
              </thead>
              <tbody>
                {syncReports.map((r) => (
                  <tr key={r.id}>
                    <td><code>#{r.id.slice(0, 8)}</code></td>
                    <td style={{ fontSize: 11, color: "#8b9bb4" }}>
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td>{r.summary?.telemetry_samples_count ?? 30}</td>
                    <td>{r.summary?.active_anomalies_count ?? 0}</td>
                    <td>{r.summary?.consultations_count ?? 0}</td>
                    <td><code style={{ fontSize: 11, color: "#38bdf8" }}>{r.integrity_hmac.slice(0, 16)}...</code></td>
                    <td>
                      <button
                        className="btn sec"
                        style={{ fontSize: 11 }}
                        onClick={async () => {
                          const v = await api.verifySyncReport(r.id);
                          alert(v.verified ? `✓ VERIFIED: HMAC matches stored digest!` : `❌ TAMPER DETECTED! Computed: ${v.computed_hmac.slice(0, 12)} vs Stored: ${v.stored_hmac.slice(0, 12)}`);
                        }}
                      >
                        Verify Hash
                      </button>
                    </td>
                    <td>
                      <button
                        className="btn danger"
                        style={{ fontSize: 10.5 }}
                        onClick={async () => {
                          await api.tamperSyncReportDemo(r.id);
                          alert("Tampering simulated in database record. Click 'Verify Hash' to verify cryptographic detection.");
                        }}
                      >
                        Tamper Test
                      </button>
                    </td>
                  </tr>
                ))}
                {syncReports.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: "center", color: "#8b9bb4", padding: 24 }}>
                      No sync reports generated yet. Click "Generate Sync Report" to create a signed mission telemetry package.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Trauma Override Modal */}
      {modal && (
        <div className="modal" onClick={() => setModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ margin: 0, color: "#ef4444", display: "flex", gap: 8, alignItems: "center" }}>
                <Ic d={P.warn} s={24} c="#ef4444" /> Trauma Override — Offline Zero-Auth Protocols
              </h3>
              <button className="btn sec" onClick={() => setModal(false)}>✕</button>
            </div>
            <p style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.55 }}>
              Zero-latency emergency checklists cached locally. Offline access is guaranteed even when communication links with Mission Control are severed.
            </p>

            <div style={{ maxHeight: 360, overflowY: "auto", margin: "14px 0" }}>
              {traumaProtocols.map((tp) => (
                <div key={tp.id} style={{ background: "#081426", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: 14, marginBottom: 10 }}>
                  <b style={{ color: "#fff", fontSize: 14 }}>{tp.title}</b>
                  <div style={{ fontSize: 11, color: "#38bdf8", margin: "2px 0 8px" }}>
                    Code: {tp.code_name} • System: {tp.body_region}
                  </div>
                  <ol style={{ margin: "0 0 0 16px", padding: 0, fontSize: 12.5, color: "#e2e8f0" }}>
                    {tp.steps.map((st, sIdx) => (
                      <li key={sIdx} style={{ marginBottom: 4 }}>{st}</li>
                    ))}
                  </ol>
                  <small style={{ display: "block", color: "#8b9bb4", fontStyle: "italic", marginTop: 8 }}>
                    NASA Reference: {tp.nasa_reference}
                  </small>
                </div>
              ))}
            </div>

            <button className="btn" style={{ width: "100%" }} onClick={() => setModal(false)}>
              Close Trauma Override
            </button>
          </div>
        </div>
      )}

      {/* Crew Switcher & Registration Modal */}
      {crewModal && (
        <div className="modal" onClick={() => setCrewModal(false)}>
          <div className="modal-box" style={{ borderTop: "5px solid #00e5ff" }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ margin: 0, color: "#f8fafc", display: "flex", gap: 8, alignItems: "center" }}>
                <Ic d={P.user} s={22} c="#00e5ff" /> Crew Manifest & Astronaut Switcher
              </h3>
              <button className="btn sec" onClick={() => setCrewModal(false)}>✕</button>
            </div>

            <h4 style={{ color: "#38bdf8", margin: "14px 0 8px" }}>Active Crew Members</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 200, overflowY: "auto" }}>
              {crewList.map((c) => (
                <div
                  key={c.id}
                  style={{
                    background: c.id === user?.id ? "rgba(2,132,199,0.3)" : "#091322",
                    border: `1px solid ${c.id === user?.id ? "#00e5ff" : "rgba(56,189,248,0.15)"}`,
                    borderRadius: 8,
                    padding: "10px 14px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    cursor: "pointer",
                  }}
                  onClick={() => handleSwitchCrew(c.id)}
                >
                  <div>
                    <b style={{ color: "#fff", fontSize: 13.5 }}>{c.full_name}</b>
                    <small style={{ display: "block", color: "#8b9bb4" }}>
                      {c.role} • Baseline HR: {c.baseline_hr_bpm} bpm • SpO2: {c.baseline_spo2_pct}%
                    </small>
                  </div>
                  {c.id === user?.id ? (
                    <span className="pill Low">Active</span>
                  ) : (
                    <button className="btn sec" style={{ fontSize: 11 }}>Switch</button>
                  )}
                </div>
              ))}
            </div>

            <h4 style={{ color: "#38bdf8", margin: "18px 0 8px" }}>Add / Register New Astronaut</h4>
            <form onSubmit={handleCreateAstronaut} style={{ display: "flex", gap: 8 }}>
              <input
                value={newCrewName}
                onChange={(e) => setNewCrewName(e.target.value)}
                placeholder="Astronaut Full Name (e.g. Dr. Alex Mercer)..."
                style={{
                  flex: 1,
                  background: "#081220",
                  border: "1px solid rgba(56,189,248,0.25)",
                  borderRadius: 6,
                  padding: "8px 10px",
                  color: "#fff",
                  fontSize: 12.5,
                }}
              />
              <select
                value={newCrewRole}
                onChange={(e) => setNewCrewRole(e.target.value)}
                style={{
                  background: "#081220",
                  border: "1px solid rgba(56,189,248,0.25)",
                  borderRadius: 6,
                  padding: "8px 10px",
                  color: "#fff",
                  fontSize: 12.5,
                }}
              >
                <option value="ASTRONAUT">ASTRONAUT</option>
                <option value="CMO">CMO</option>
                <option value="FLIGHT_SURGEON">FLIGHT SURGEON</option>
              </select>
              <button type="submit" className="btn" disabled={!newCrewName.trim()}>
                Add Crew
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
