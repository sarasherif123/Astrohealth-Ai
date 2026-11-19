from typing import Optional
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AppError, decode_access_token, get_current_user, resolve_target_user_id
from app.config import settings
from app.crud import _orm_to_packet, ingest_telemetry_packet
from app.database import AsyncSessionLocal, get_db
from app.models import AnomalyAlert, TelemetryReading, User
from app.rules import ALL_BODY_REGIONS, UserBaseline, anomaly_engine
from app.schemas import (
    AlertResponse,
    LatestTelemetrySummaryResponse,
    SimulateScenarioRequest,
    SimulateScenarioResponse,
    TelemetryCreateRequest,
    TelemetryIngestResponse,
    TelemetryReadingResponse,
)
from app.simulator import simulator_hub

router = APIRouter(tags=["Telemetry & Alerts"])


@router.post("/telemetry", response_model=TelemetryIngestResponse, status_code=201)
async def create_telemetry(
    payload: TelemetryCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TelemetryIngestResponse:
    target_uid = resolve_target_user_id(
        current_user, payload.target_user_id, allow_flight_surgeon=False
    )
    target_user = (
        await db.execute(select(User).where(User.id == target_uid))
    ).scalar_one_or_none()
    if target_user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "Target user not found.")

    reading_row, alert_rows, _ = await ingest_telemetry_packet(
        db,
        target_user,
        heart_rate_bpm=payload.heart_rate_bpm,
        spo2_pct=payload.spo2_pct,
        systolic_bp_mmhg=payload.systolic_bp_mmhg,
        diastolic_bp_mmhg=payload.diastolic_bp_mmhg,
        core_temp_c=payload.core_temp_c,
        radiation_msv=payload.radiation_msv,
        sleep_score=payload.sleep_score,
        eeg_fatigue_index=payload.eeg_fatigue_index,
    )

    reading_resp = TelemetryReadingResponse.model_validate(reading_row, from_attributes=True)
    alerts_resp = [AlertResponse.model_validate(a, from_attributes=True) for a in alert_rows]
    await simulator_hub.broadcast_frame(target_uid, reading_resp, alerts_resp)

    return TelemetryIngestResponse(reading=reading_resp, generated_alerts=alerts_resp)


@router.get("/telemetry/latest", response_model=LatestTelemetrySummaryResponse)
async def get_latest_telemetry(
    user_id: Optional[str] = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LatestTelemetrySummaryResponse:
    target_uid = resolve_target_user_id(current_user, user_id, allow_flight_surgeon=True)
    target_user = (
        await db.execute(select(User).where(User.id == target_uid))
    ).scalar_one_or_none()
    if target_user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "Target user not found.")

    rows = (
        await db.execute(
            select(TelemetryReading)
            .where(TelemetryReading.user_id == target_uid)
            .order_by(TelemetryReading.recorded_at.desc())
            .limit(limit)
        )
    ).scalars().all()

    active_alerts = (
        await db.execute(
            select(AnomalyAlert)
            .where(
                AnomalyAlert.user_id == target_uid,
                AnomalyAlert.is_acknowledged.is_(False),
            )
            .order_by(AnomalyAlert.created_at.desc())
        )
    ).scalars().all()

    window_pkts = [_orm_to_packet(r) for r in reversed(rows[:5])]
    baseline = UserBaseline(
        user_id=target_user.id,
        baseline_hr_bpm=target_user.baseline_hr_bpm,
        baseline_spo2_pct=target_user.baseline_spo2_pct,
        baseline_sys_bp=target_user.baseline_sys_bp,
        baseline_dia_bp=target_user.baseline_dia_bp,
    )
    overall_status, region_statuses, _ = anomaly_engine.evaluate_window(
        window_pkts,
        baseline,
        existing_last_fired={r.rule_id: r.created_at for r in active_alerts},
    )

    return LatestTelemetrySummaryResponse(
        user_id=target_uid,
        overall_status=overall_status,
        region_statuses=region_statuses,
        readings=[
            TelemetryReadingResponse.model_validate(r, from_attributes=True)
            for r in reversed(rows)
        ],
        active_alerts=[
            AlertResponse.model_validate(a, from_attributes=True) for a in active_alerts
        ],
    )


@router.post("/telemetry/simulate-scenario", response_model=SimulateScenarioResponse)
async def simulate_scenario(
    payload: SimulateScenarioRequest,
    current_user: User = Depends(get_current_user),
) -> SimulateScenarioResponse:
    target_uid = resolve_target_user_id(
        current_user, payload.target_user_id, allow_flight_surgeon=False
    )
    status_level, count = await simulator_hub.trigger_scenario_burst(
        user_id=target_uid,
        scenario=payload.scenario,
        time_compression=payload.time_compression,
    )
    return SimulateScenarioResponse(
        target_user_id=target_uid,
        active_scenario=payload.scenario,
        status_level=status_level,
        alerts_triggered=count,
    )


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    alert = (
        await db.execute(select(AnomalyAlert).where(AnomalyAlert.id == alert_id))
    ).scalar_one_or_none()
    if alert is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "ALERT_NOT_FOUND", "Alert not found.")

    resolve_target_user_id(current_user, alert.user_id, allow_flight_surgeon=False)
    alert.is_acknowledged = True
    await db.commit()
    return {"id": alert.id, "is_acknowledged": True}
