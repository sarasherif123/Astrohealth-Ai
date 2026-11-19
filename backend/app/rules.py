from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple
import uuid

SeverityType = Literal["YELLOW", "RED"]
StatusLevelType = Literal["GREEN", "YELLOW", "RED"]
BodyRegionType = Literal[
    "BRAIN_NEURO",
    "CARDIOVASCULAR",
    "MUSCULOSKELETAL",
    "OCULAR_EYES",
    "GASTROINTESTINAL",
    "SYSTEMIC",
]

ALL_BODY_REGIONS: Tuple[BodyRegionType, ...] = (
    "BRAIN_NEURO",
    "CARDIOVASCULAR",
    "MUSCULOSKELETAL",
    "OCULAR_EYES",
    "GASTROINTESTINAL",
    "SYSTEMIC",
)

SEVERITY_RANK: Dict[StatusLevelType, int] = {
    "GREEN": 0,
    "YELLOW": 1,
    "RED": 2,
}

ROLLING_WINDOW_SIZE: int = 5
MIN_BREACH_PACKETS: int = 3
ALERT_COOLDOWN_SECONDS: int = 300


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class UserBaseline:
    user_id: str
    baseline_hr_bpm: int = 64
    baseline_spo2_pct: float = 98.5
    baseline_sys_bp: int = 118
    baseline_dia_bp: int = 75


@dataclass(frozen=True)
class TelemetryPacket:
    id: str
    user_id: str
    recorded_at: datetime
    heart_rate_bpm: int
    spo2_pct: float
    systolic_bp_mmhg: int
    diastolic_bp_mmhg: int
    core_temp_c: float
    radiation_msv: float
    sleep_score: int
    eeg_fatigue_index: float


@dataclass(frozen=True)
class TriggeredAlertData:
    id: str
    user_id: str
    telemetry_id: str
    rule_id: str
    body_region: BodyRegionType
    severity: SeverityType
    title: str
    micro_intervention: str
    citation_source: str
    is_acknowledged: bool
    created_at: datetime


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    body_region: BodyRegionType
    title: str
    micro_intervention: str
    citation_source: str
    evaluator: Callable[[TelemetryPacket, UserBaseline], Optional[SeverityType]]


def _eval_hr(pkt: TelemetryPacket, base: UserBaseline) -> Optional[SeverityType]:
    delta = pkt.heart_rate_bpm - base.baseline_hr_bpm
    if delta >= 40:
        return "RED"
    if delta >= 20:
        return "YELLOW"
    return None


def _eval_spo2(pkt: TelemetryPacket, _base: UserBaseline) -> Optional[SeverityType]:
    if pkt.spo2_pct < 90.0:
        return "RED"
    if pkt.spo2_pct < 95.0:
        return "YELLOW"
    return None


def _eval_bp(pkt: TelemetryPacket, _base: UserBaseline) -> Optional[SeverityType]:
    if pkt.systolic_bp_mmhg >= 160 or pkt.diastolic_bp_mmhg >= 100:
        return "RED"
    if pkt.systolic_bp_mmhg >= 135 or pkt.diastolic_bp_mmhg >= 85:
        return "YELLOW"
    return None


def _eval_core_temp(pkt: TelemetryPacket, _base: UserBaseline) -> Optional[SeverityType]:
    if pkt.core_temp_c >= 38.5:
        return "RED"
    if pkt.core_temp_c >= 37.8:
        return "YELLOW"
    return None


def _eval_sleep(pkt: TelemetryPacket, _base: UserBaseline) -> Optional[SeverityType]:
    if pkt.sleep_score < 40:
        return "RED"
    if pkt.sleep_score < 60:
        return "YELLOW"
    return None


def _eval_fatigue(pkt: TelemetryPacket, _base: UserBaseline) -> Optional[SeverityType]:
    if pkt.eeg_fatigue_index >= 0.85:
        return "RED"
    if pkt.eeg_fatigue_index >= 0.65:
        return "YELLOW"
    return None


def _eval_radiation(pkt: TelemetryPacket, _base: UserBaseline) -> Optional[SeverityType]:
    if pkt.radiation_msv > 3.0:
        return "RED"
    if pkt.radiation_msv > 1.5:
        return "YELLOW"
    return None


def _eval_sans_cephalad_shift(
    pkt: TelemetryPacket, _base: UserBaseline
) -> Optional[SeverityType]:
    if pkt.systolic_bp_mmhg >= 135 and (pkt.radiation_msv > 1.5 or pkt.sleep_score < 60):
        return "YELLOW"
    return None


RULES: Tuple[RuleDefinition, ...] = (
    RuleDefinition(
        rule_id="RULE_HR_ELEVATED",
        body_region="CARDIOVASCULAR",
        title="Persistent Resting Tachycardia Above Baseline",
        micro_intervention=(
            "Suspend high-intensity resistive exercise for 4 hours, initiate 500 mL oral "
            "electrolyte hydration, and verify Astroskin ECG lead contact."
        ),
        citation_source=(
            "NASA Spaceflight Medical Operations: Cardiovascular, Hypoxia, and Thermal Stabilization Summary, Page 6"
        ),
        evaluator=_eval_hr,
    ),
    RuleDefinition(
        rule_id="RULE_SPO2_HYPOXIA",
        body_region="CARDIOVASCULAR",
        title="Arterial Oxygen Desaturation (Hypoxia Warning)",
        micro_intervention=(
            "Verify habitat cabin O2 partial pressure immediately and don portable supplemental "
            "oxygen mask if SpO2 remains below 92%."
        ),
        citation_source=(
            "NASA Spaceflight Medical Operations: Cardiovascular, Hypoxia, and Thermal Stabilization Summary, Page 14"
        ),
        evaluator=_eval_spo2,
    ),
    RuleDefinition(
        rule_id="RULE_BP_HYPERTENSION",
        body_region="CARDIOVASCULAR",
        title="Elevated Arterial Blood Pressure & Vascular Strain",
        micro_intervention=(
            "Perform seated paced-breathing protocol for 10 minutes and restrict dietary "
            "sodium intake below 2000 mg/day."
        ),
        citation_source=(
            "NASA Spaceflight Medical Operations: Cardiovascular, Hypoxia, and Thermal Stabilization Summary, Page 6"
        ),
        evaluator=_eval_bp,
    ),
    RuleDefinition(
        rule_id="RULE_CORE_HYPERTHERMIA",
        body_region="SYSTEMIC",
        title="Core Body Temperature Elevation (Thermal Strain)",
        micro_intervention=(
            "Reduce habitat ambient workload, increase liquid cooling garment flow rate, and "
            "consume 500 mL chilled electrolyte solution."
        ),
        citation_source=(
            "NASA Spaceflight Medical Operations: Cardiovascular, Hypoxia, and Thermal Stabilization Summary, Page 14"
        ),
        evaluator=_eval_core_temp,
    ),
    RuleDefinition(
        rule_id="RULE_CIRCADIAN_DRIFT",
        body_region="BRAIN_NEURO",
        title="Circadian Desynchrony & Sleep Architecture Degradation",
        micro_intervention=(
            "Configure habitat Solid-State Lighting Assembly (SSLA) to 460nm blue-enriched "
            "spectrum for 30 minutes upon wake and shift to warm red-depleted mode 90 minutes pre-sleep."
        ),
        citation_source=(
            "NASA HRP Evidence Report: Risk of Performance Decrements and Adverse Health Outcomes Resulting from Sleep Loss, Circadian Desynchronization, and Work Overload (Flynn-Evans et al., 2016), Page 28"
        ),
        evaluator=_eval_sleep,
    ),
    RuleDefinition(
        rule_id="RULE_COGNITIVE_FATIGUE",
        body_region="BRAIN_NEURO",
        title="Elevated Prefrontal fNIRS Cognitive Fatigue Index",
        micro_intervention=(
            "Defer safety-critical EVA or robotic arm tasks and schedule a 25-minute restorative "
            "nap window in darkened crew quarters."
        ),
        citation_source=(
            "NASA HRP Evidence Report: Risk of Performance Decrements and Adverse Health Outcomes Resulting from Sleep Loss, Circadian Desynchronization, and Work Overload (Flynn-Evans et al., 2016), Page 51"
        ),
        evaluator=_eval_fatigue,
    ),
    RuleDefinition(
        rule_id="RULE_RADIATION_SPIKE",
        body_region="SYSTEMIC",
        title="Elevated Daily Ionizing Radiation Dosimetry (>1.5 mSv/day)",
        micro_intervention=(
            "Relocate crew activity to high-mass polyethylene storm shelter zone and consume "
            "antioxidant-fortified ration pack with 1500 mL hydration."
        ),
        citation_source=(
            "NASA HRP Evidence Report: Risk of Acute Radiation Syndromes Due to Solar Particle Events (Townsend et al., 2018), Page 19"
        ),
        evaluator=_eval_radiation,
    ),
    RuleDefinition(
        rule_id="RULE_SANS_OCULAR_SHIFT",
        body_region="OCULAR_EYES",
        title="SANS Risk Pattern (Proxy): Cephalad Fluid Shift & Vascular Load",
        micro_intervention=(
            "Schedule a 30-minute Lower Body Negative Pressure (LBNP) session at -25 mmHg and "
            "perform near-vision Amsler grid check."
        ),
        citation_source=(
            "NASA HRP Evidence Report: Risk of Spaceflight Associated Neuro-ocular Syndrome (SANS) (Stenger et al., 2017), Page 4"
        ),
        evaluator=_eval_sans_cephalad_shift,
    ),
)


class RollingWindowAnomalyEngine:
    def __init__(self, cooldown_seconds: int = ALERT_COOLDOWN_SECONDS) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_fired_at: Dict[Tuple[str, str], datetime] = {}
        self._last_severity: Dict[Tuple[str, str], StatusLevelType] = {}

    def reset_state(self, user_id: Optional[str] = None) -> None:
        if user_id is None:
            self._last_fired_at.clear()
            self._last_severity.clear()
        else:
            for store in (self._last_fired_at, self._last_severity):
                keys = [k for k in store if k[0] == user_id]
                for k in keys:
                    del store[k]

    def evaluate_window(
        self,
        recent_packets: Sequence[TelemetryPacket],
        baseline: UserBaseline,
        existing_last_fired: Optional[Dict[str, datetime]] = None,
        existing_last_severity: Optional[Dict[str, SeverityType]] = None,
    ) -> Tuple[StatusLevelType, Dict[BodyRegionType, StatusLevelType], List[TriggeredAlertData]]:
        region_statuses: Dict[BodyRegionType, StatusLevelType] = {
            region: "GREEN" for region in ALL_BODY_REGIONS
        }

        ordered = sorted(recent_packets, key=lambda p: ensure_utc(p.recorded_at))[
            -ROLLING_WINDOW_SIZE:
        ]

        if len(ordered) < MIN_BREACH_PACKETS:
            return "GREEN", region_statuses, []

        required_count = MIN_BREACH_PACKETS
        latest_pkt = ordered[-1]
        now = ensure_utc(latest_pkt.recorded_at)

        overall_status: StatusLevelType = "GREEN"
        triggered_alerts: List[TriggeredAlertData] = []

        for rule in RULES:
            severities: List[SeverityType] = []
            for pkt in ordered:
                sev = rule.evaluator(pkt, baseline)
                if sev is not None:
                    severities.append(sev)

            cooldown_key = (baseline.user_id, rule.rule_id)

            if len(severities) < required_count:
                self._last_severity[cooldown_key] = "GREEN"
                continue

            red_count = sum(1 for s in severities if s == "RED")
            active_severity: SeverityType = "RED" if red_count >= required_count else "YELLOW"

            if SEVERITY_RANK[active_severity] > SEVERITY_RANK[region_statuses[rule.body_region]]:
                region_statuses[rule.body_region] = active_severity
            if SEVERITY_RANK[active_severity] > SEVERITY_RANK[overall_status]:
                overall_status = active_severity

            last_time = self._last_fired_at.get(cooldown_key)
            if existing_last_fired and rule.rule_id in existing_last_fired:
                db_time = ensure_utc(existing_last_fired[rule.rule_id])
                if last_time is None or db_time > last_time:
                    last_time = db_time

            last_sev: StatusLevelType = self._last_severity.get(cooldown_key, "GREEN")
            if existing_last_severity and rule.rule_id in existing_last_severity:
                db_sev = existing_last_severity[rule.rule_id]
                if SEVERITY_RANK[db_sev] > SEVERITY_RANK[last_sev]:
                    last_sev = db_sev

            escalated = SEVERITY_RANK[active_severity] > SEVERITY_RANK[last_sev]
            if (
                last_time is not None
                and (now - last_time).total_seconds() < self.cooldown_seconds
                and not escalated
            ):
                continue

            self._last_fired_at[cooldown_key] = now
            self._last_severity[cooldown_key] = active_severity

            triggered_alerts.append(
                TriggeredAlertData(
                    id=str(uuid.uuid4()),
                    user_id=baseline.user_id,
                    telemetry_id=latest_pkt.id,
                    rule_id=rule.rule_id,
                    body_region=rule.body_region,
                    severity=active_severity,
                    title=rule.title,
                    micro_intervention=rule.micro_intervention,
                    citation_source=rule.citation_source,
                    is_acknowledged=False,
                    created_at=now,
                )
            )

        return overall_status, region_statuses, triggered_alerts


def create_anomaly_engine(
    cooldown_seconds: int = ALERT_COOLDOWN_SECONDS,
) -> RollingWindowAnomalyEngine:
    return RollingWindowAnomalyEngine(cooldown_seconds=cooldown_seconds)


anomaly_engine = create_anomaly_engine()
