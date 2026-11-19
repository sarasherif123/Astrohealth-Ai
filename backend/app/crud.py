from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Dict, List, Optional, Tuple
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    AnomalyAlert,
    DiagnosticConsultation,
    MissionSyncReport,
    TelemetryReading,
    TraumaProtocol,
    TreatmentTask,
    User,
)
from app.rules import (
    BodyRegionType,
    RollingWindowAnomalyEngine,
    SeverityType,
    StatusLevelType,
    TelemetryPacket,
    TriggeredAlertData,
    UserBaseline,
    anomaly_engine,
    ensure_utc,
)


def _orm_to_packet(row: TelemetryReading) -> TelemetryPacket:
    return TelemetryPacket(
        id=row.id,
        user_id=row.user_id,
        recorded_at=ensure_utc(row.recorded_at),
        heart_rate_bpm=row.heart_rate_bpm,
        spo2_pct=row.spo2_pct,
        systolic_bp_mmhg=row.systolic_bp_mmhg,
        diastolic_bp_mmhg=row.diastolic_bp_mmhg,
        core_temp_c=row.core_temp_c,
        radiation_msv=row.radiation_msv,
        sleep_score=row.sleep_score,
        eeg_fatigue_index=row.eeg_fatigue_index,
    )


async def ingest_telemetry_packet(
    db: AsyncSession,
    user: User,
    *,
    heart_rate_bpm: int,
    spo2_pct: float,
    systolic_bp_mmhg: int,
    diastolic_bp_mmhg: int,
    core_temp_c: float,
    radiation_msv: float,
    sleep_score: int,
    eeg_fatigue_index: float,
    recorded_at: Optional[datetime] = None,
    engine_instance: RollingWindowAnomalyEngine = anomaly_engine,
) -> Tuple[TelemetryReading, List[AnomalyAlert], Dict[BodyRegionType, StatusLevelType]]:
    now = ensure_utc(recorded_at or datetime.now(timezone.utc))
    reading_id = str(uuid.uuid4())

    # Fetch last 4 readings from DB to form the 5-packet window with the new reading
    prev_rows = (
        await db.execute(
            select(TelemetryReading)
            .where(TelemetryReading.user_id == user.id)
            .order_by(TelemetryReading.recorded_at.desc())
            .limit(4)
        )
    ).scalars().all()

    new_pkt = TelemetryPacket(
        id=reading_id,
        user_id=user.id,
        recorded_at=now,
        heart_rate_bpm=heart_rate_bpm,
        spo2_pct=spo2_pct,
        systolic_bp_mmhg=systolic_bp_mmhg,
        diastolic_bp_mmhg=diastolic_bp_mmhg,
        core_temp_c=core_temp_c,
        radiation_msv=radiation_msv,
        sleep_score=sleep_score,
        eeg_fatigue_index=eeg_fatigue_index,
    )
    window_packets = [_orm_to_packet(r) for r in reversed(prev_rows)] + [new_pkt]

    baseline = UserBaseline(
        user_id=user.id,
        baseline_hr_bpm=user.baseline_hr_bpm,
        baseline_spo2_pct=user.baseline_spo2_pct,
        baseline_sys_bp=user.baseline_sys_bp,
        baseline_dia_bp=user.baseline_dia_bp,
    )

    overall_status, region_statuses, triggered = engine_instance.evaluate_window(
        window_packets, baseline
    )

    reading_row = TelemetryReading(
        id=reading_id,
        user_id=user.id,
        recorded_at=now,
        heart_rate_bpm=heart_rate_bpm,
        spo2_pct=spo2_pct,
        systolic_bp_mmhg=systolic_bp_mmhg,
        diastolic_bp_mmhg=diastolic_bp_mmhg,
        core_temp_c=core_temp_c,
        radiation_msv=radiation_msv,
        sleep_score=sleep_score,
        eeg_fatigue_index=eeg_fatigue_index,
        status_level=overall_status,
    )
    db.add(reading_row)
    # Persist the reading first so alerts referencing it satisfy the FK constraint
    await db.flush()

    alert_rows: List[AnomalyAlert] = []
    for item in triggered:
        alert_row = AnomalyAlert(
            id=item.id,
            user_id=item.user_id,
            telemetry_id=item.telemetry_id,
            rule_id=item.rule_id,
            body_region=item.body_region,
            severity=item.severity,
            title=item.title,
            micro_intervention=item.micro_intervention,
            citation_source=item.citation_source,
            is_acknowledged=False,
            created_at=item.created_at,
        )
        db.add(alert_row)
        alert_rows.append(alert_row)

    # Prune older telemetry rows beyond MAX_TELEMETRY_ROWS_PER_USER
    total_count = (
        await db.execute(
            select(func.count(TelemetryReading.id)).where(TelemetryReading.user_id == user.id)
        )
    ).scalar_one()

    if total_count > settings.MAX_TELEMETRY_ROWS_PER_USER:
        keep_ids_subq = (
            select(TelemetryReading.id)
            .where(TelemetryReading.user_id == user.id)
            .order_by(TelemetryReading.recorded_at.desc())
            .limit(settings.MAX_TELEMETRY_ROWS_PER_USER)
        )
        await db.execute(
            delete(TelemetryReading).where(
                TelemetryReading.user_id == user.id,
                TelemetryReading.id.not_in(keep_ids_subq),
            )
        )

    await db.commit()
    return reading_row, alert_rows, region_statuses


def compute_canonical_hmac(summary_dict: dict) -> Tuple[str, str]:
    canonical_json = json.dumps(summary_dict, sort_keys=True, separators=(",", ":"))
    digest = hmac.new(
        settings.MISSION_HMAC_SECRET.encode("utf-8"),
        canonical_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return canonical_json, digest
