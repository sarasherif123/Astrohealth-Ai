import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import random
from typing import Dict, List, Set

from fastapi import WebSocket
from sqlalchemy import select

from app.crud import ingest_telemetry_packet
from app.database import AsyncSessionLocal
from app.models import User
from app.rules import StatusLevelType, anomaly_engine
from app.schemas import AlertResponse, ScenarioType, TelemetryReadingResponse


class TelemetrySimulatorHub:
    def __init__(self) -> None:
        self._rng = random.Random(42)
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._active_scenario: Dict[str, ScenarioType] = defaultdict(lambda: "NOMINAL_BASELINE")
        self._time_compression: Dict[str, float] = defaultdict(lambda: 1.0)
        self._virtual_clock: Dict[str, datetime] = {}

    def register_ws(self, user_id: str, ws: WebSocket) -> None:
        self._connections[user_id].add(ws)

    def unregister_ws(self, user_id: str, ws: WebSocket) -> None:
        self._connections[user_id].discard(ws)

    async def broadcast_frame(
        self,
        user_id: str,
        reading: TelemetryReadingResponse,
        alerts: List[AlertResponse],
    ) -> None:
        dead: List[WebSocket] = []
        frame = {
            "type": "telemetry",
            "reading": reading.model_dump(mode="json"),
            "alerts": [a.model_dump(mode="json") for a in alerts],
        }
        for ws in list(self._connections.get(user_id, set())):
            try:
                await ws.send_json(frame)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister_ws(user_id, ws)

    def _build_packet_metrics(self, user: User, scenario: ScenarioType) -> dict:
        if scenario == "SANS_OCULAR_AND_RADIATION_SPIKE":
            return {
                "heart_rate_bpm": user.baseline_hr_bpm + 14,
                "spo2_pct": 97.5,
                "systolic_bp_mmhg": 142,
                "diastolic_bp_mmhg": 88,
                "core_temp_c": 37.1,
                "radiation_msv": 2.1,
                "sleep_score": 58,
                "eeg_fatigue_index": 0.58,  # Strictly below 0.65 so exact 4 alerts fire
            }
        if scenario == "CIRCADIAN_FATIGUE_DRIFT":
            return {
                "heart_rate_bpm": user.baseline_hr_bpm + 22,
                "spo2_pct": 98.0,
                "systolic_bp_mmhg": 124,
                "diastolic_bp_mmhg": 78,
                "core_temp_c": 36.9,
                "radiation_msv": 0.40,
                "sleep_score": 48,
                "eeg_fatigue_index": 0.76,
            }
        if scenario == "CARDIO_HYPERTENSION":
            return {
                "heart_rate_bpm": user.baseline_hr_bpm + 45,
                "spo2_pct": 93.5,
                "systolic_bp_mmhg": 168,
                "diastolic_bp_mmhg": 104,
                "core_temp_c": 37.4,
                "radiation_msv": 0.45,
                "sleep_score": 72,
                "eeg_fatigue_index": 0.35,
            }
        # NOMINAL_BASELINE
        jitter = self._rng.choice([-1, 0, 1])
        return {
            "heart_rate_bpm": user.baseline_hr_bpm + jitter,
            "spo2_pct": 98.5,
            "systolic_bp_mmhg": user.baseline_sys_bp + jitter,
            "diastolic_bp_mmhg": user.baseline_dia_bp,
            "core_temp_c": 36.8,
            "radiation_msv": 0.32,
            "sleep_score": 84,
            "eeg_fatigue_index": 0.20,
        }

    async def trigger_scenario_burst(
        self,
        user_id: str,
        scenario: ScenarioType,
        time_compression: float = 1.0,
    ) -> tuple[StatusLevelType, int]:
        self._active_scenario[user_id] = scenario
        self._time_compression[user_id] = time_compression

        if scenario == "STOP":
            return "GREEN", 0

        anomaly_engine.reset_state(user_id=user_id)
        total_alerts = 0
        last_status: StatusLevelType = "GREEN"

        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
            if user is None:
                return "GREEN", 0

            base_clock = self._virtual_clock.get(user_id, datetime.now(timezone.utc))
            step_delta = timedelta(seconds=2.0 * time_compression)

            # Push 5 consecutive packets so the 3-of-5 rolling window triggers immediately
            for idx in range(5):
                pkt_time = base_clock + step_delta * (idx + 1)
                self._virtual_clock[user_id] = pkt_time
                metrics = self._build_packet_metrics(user, scenario)
                reading_row, alert_rows, _ = await ingest_telemetry_packet(
                    db,
                    user,
                    recorded_at=pkt_time,
                    **metrics,
                )
                last_status = reading_row.status_level
                total_alerts += len(alert_rows)

                await self.broadcast_frame(
                    user_id=user.id,
                    reading=TelemetryReadingResponse.model_validate(
                        reading_row, from_attributes=True
                    ),
                    alerts=[
                        AlertResponse.model_validate(a, from_attributes=True)
                        for a in alert_rows
                    ],
                )

        return last_status, total_alerts


simulator_hub = TelemetrySimulatorHub()
