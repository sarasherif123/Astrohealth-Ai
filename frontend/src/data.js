export const wave = (base, amp, n, seed) =>
  Array.from({ length: n }, (_, i) => base + Math.sin(i * 0.9 + seed) * amp + Math.cos(i * 2.3 + seed) * amp * 0.4);

export const SYS = [
  ["Brain & Neurological", "brain", "BRAIN_NEURO"],
  ["Ocular & Eyes", "eye", "OCULAR_EYES"],
  ["Cardiovascular", "heart", "CARDIOVASCULAR"],
  ["Musculoskeletal", "bone", "MUSCULOSKELETAL"],
  ["Gastrointestinal", "gut", "GASTROINTESTINAL"],
  ["Systemic", "gear", "SYSTEMIC"]
];

export const SYS_MAP = {
  "Brain & Neurological": "BRAIN_NEURO",
  "Ocular & Eyes": "OCULAR_EYES",
  "Cardiovascular": "CARDIOVASCULAR",
  "Musculoskeletal": "MUSCULOSKELETAL",
  "Gastrointestinal": "GASTROINTESTINAL",
  "Systemic": "SYSTEMIC"
};

export const NAV = [
  ["Overview", "home"],
  ["Health Monitoring", "pulse"],
  ["Digital Twin", "user"],
  ["AI Medical Assistant", "chat"],
  ["Countermeasure Schedule", "cal"],
  ["Emergency Protocols", "shield"],
  ["Mission Control Sync", "sync"]
];

export const ALERTS = [
  ["2h ago", "High", "Elevated Heart Rate", "Check Vitals"],
  ["5h ago", "Medium", "Increased Fatigue", "Review"],
  ["12h ago", "Low", "Minor Temperature Rise", "Review"]
];
