# V2.1 Complete Backend Core, Simulator & FastAPI Routers

This document contains the remaining production-ready backend modules required to run the V2.1 AstroHealth AI server:
1. `backend/app/database.py`
2. `backend/app/models.py`
3. `backend/app/schemas.py`
4. `backend/app/auth.py`
5. `backend/app/crud.py`
6. `backend/app/simulator.py`
7. `backend/app/routers/auth_router.py`
8. `backend/app/routers/telemetry_router.py`
9. `backend/app/routers/clinical_router.py`
10. `backend/app/main.py`

---

## 1. `backend/app/database.py`

```python
from typing import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

---

## 2. `backend/app/models.py`

```python
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="ASTRONAUT")
    baseline_hr_bpm: Mapped[int] = mapped_column(Integer, nullable=False, default=64)
    baseline_spo2_pct: Mapped[float] = mapped_column(Float, nullable=False, default=98.5)
    baseline_sys_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=118)
    baseline_dia_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=75)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    __table_args__ = (
        CheckConstraint(
            "role IN ('ASTRONAUT', 'CMO', 'FLIGHT_SURGEON')",
            name="ck_users_role",
        ),
    )


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    heart_rate_bpm: Mapped[int] = mapped_column(Integer, nullable=False)
    spo2_pct: Mapped[float] = mapped_column(Float, nullable=False)
    systolic_bp_mmhg: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic_bp_mmhg: Mapped[int] = mapped_column(Integer, nullable=False)
    core_temp_c: Mapped[float] = mapped_column(Float, nullable=False)
    radiation_msv: Mapped[float] = mapped_column(Float, nullable=False)
    sleep_score: Mapped[int] = mapped_column(Integer, nullable=False)
    eeg_fatigue_index: Mapped[float] = mapped_column(Float, nullable=False)
    status_level: Mapped[str] = mapped_column(String(10), nullable=False, default="GREEN")

    __table_args__ = (
        Index("idx_telemetry_user_recorded", "user_id", recorded_at.desc()),
        CheckConstraint("heart_rate_bpm BETWEEN 20 AND 260", name="ck_tel_hr"),
        CheckConstraint("spo2_pct BETWEEN 50.0 AND 100.0", name="ck_tel_spo2"),
        CheckConstraint("systolic_bp_mmhg BETWEEN 50 AND 250", name="ck_tel_sys"),
        CheckConstraint("diastolic_bp_mmhg BETWEEN 30 AND 160", name="ck_tel_dia"),
        CheckConstraint("core_temp_c BETWEEN 32.0 AND 43.0", name="ck_tel_temp"),
        CheckConstraint("radiation_msv >= 0.0 AND radiation_msv <= 50.0", name="ck_tel_rad"),
        CheckConstraint("sleep_score BETWEEN 0 AND 100", name="ck_tel_sleep"),
        CheckConstraint("eeg_fatigue_index BETWEEN 0.0 AND 1.0", name="ck_tel_eeg"),
        CheckConstraint("status_level IN ('GREEN', 'YELLOW', 'RED')", name="ck_tel_status"),
    )


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    telemetry_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("telemetry_readings.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(40), nullable=False)
    body_region: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    micro_intervention: Mapped[str] = mapped_column(Text, nullable=False)
    citation_source: Mapped[str] = mapped_column(String(255), nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    __table_args__ = (
        Index("idx_alerts_user_rule_created", "user_id", "rule_id", created_at.desc()),
        CheckConstraint("severity IN ('YELLOW', 'RED')", name="ck_alert_severity"),
    )


class DiagnosticConsultation(Base):
    __tablename__ = "diagnostic_consultations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body_region: Mapped[str] = mapped_column(String(30), nullable=False)
    symptom_query: Mapped[str] = mapped_column(Text, nullable=False)
    voice_stress_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    execution_mode: Mapped[str] = mapped_column(
        String(30), nullable=False, default="ONLINE_GEMINI"
    )
    citations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class TreatmentTask(Base):
    __tablename__ = "treatment_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    consultation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("diagnostic_consultations.id", ondelete="SET NULL"),
        nullable=True,
    )
    countermeasure_id: Mapped[str] = mapped_column(String(40), nullable=False)
    task_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TraumaProtocol(Base):
    __tablename__ = "trauma_protocols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body_region: Mapped[str] = mapped_column(String(30), nullable=False)
    steps_json: Mapped[str] = mapped_column(Text, nullable=False)
    nasa_reference: Mapped[str] = mapped_column(String(255), nullable=False)


class MissionSyncReport(Base):
    __tablename__ = "mission_sync_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    generated_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    integrity_hmac: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
```

---

## 3. `backend/app/schemas.py`

```python
from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field

from app.rag_engine import CitationSchema, ExecutionModeType, MaterializedTaskSchema
from app.rules import BodyRegionType, SeverityType, StatusLevelType

RoleType = Literal["ASTRONAUT", "CMO", "FLIGHT_SURGEON"]
ScenarioType = Literal[
    "NOMINAL_BASELINE",
    "SANS_OCULAR_AND_RADIATION_SPIKE",
    "CIRCADIAN_FATIGUE_DRIFT",
    "CARDIO_HYPERTENSION",
    "STOP",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: RoleType
    baseline_hr_bpm: int
    baseline_spo2_pct: float
    baseline_sys_bp: int
    baseline_dia_bp: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


class TelemetryCreateRequest(BaseModel):
    target_user_id: Optional[str] = None
    heart_rate_bpm: int = Field(..., ge=20, le=260)
    spo2_pct: float = Field(..., ge=50.0, le=100.0)
    systolic_bp_mmhg: int = Field(..., ge=50, le=250)
    diastolic_bp_mmhg: int = Field(..., ge=30, le=160)
    core_temp_c: float = Field(..., ge=32.0, le=43.0)
    radiation_msv: float = Field(..., ge=0.0, le=50.0)
    sleep_score: int = Field(..., ge=0, le=100)
    eeg_fatigue_index: float = Field(..., ge=0.0, le=1.0)


class TelemetryReadingResponse(BaseModel):
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
    status_level: StatusLevelType


class AlertResponse(BaseModel):
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


class TelemetryIngestResponse(BaseModel):
    reading: TelemetryReadingResponse
    generated_alerts: List[AlertResponse]


class LatestTelemetrySummaryResponse(BaseModel):
    user_id: str
    overall_status: StatusLevelType
    region_statuses: Dict[BodyRegionType, StatusLevelType]
    readings: List[TelemetryReadingResponse]
    active_alerts: List[AlertResponse]


class SimulateScenarioRequest(BaseModel):
    scenario: ScenarioType
    target_user_id: Optional[str] = None
    time_compression: float = Field(default=1.0, ge=0.25, le=20.0)


class SimulateScenarioResponse(BaseModel):
    target_user_id: str
    active_scenario: ScenarioType
    status_level: StatusLevelType
    alerts_triggered: int


class ConsultationCreateRequest(BaseModel):
    target_user_id: Optional[str] = None
    body_region: BodyRegionType
    symptom_query: str = Field(..., min_length=5, max_length=2000)
    voice_stress_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ConsultationResponse(BaseModel):
    id: str
    user_id: str
    body_region: BodyRegionType
    symptom_query: str
    voice_stress_score: Optional[float]
    ai_diagnosis: str
    confidence_score: float
    execution_mode: ExecutionModeType
    citations: List[CitationSchema]
    generated_tasks: List[MaterializedTaskSchema]
    created_at: datetime


class TraumaProtocolResponse(BaseModel):
    id: str
    code_name: str
    title: str
    body_region: str
    steps: List[str]
    nasa_reference: str


class SyncReportCreateRequest(BaseModel):
    target_user_id: Optional[str] = None


class SyncReportResponse(BaseModel):
    id: str
    user_id: str
    generated_by: str
    integrity_hmac: str
    summary: dict
    sync_status: str
    created_at: datetime


class SyncReportVerifyResponse(BaseModel):
    report_id: str
    verified: bool
    stored_hmac: str
    computed_hmac: str
    algorithm: str = "HMAC-SHA256"
```

---

## 4. `backend/app/auth.py`

```python
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import time
from typing import Callable, Deque, Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
        )


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "TOKEN_EXPIRED",
            "Authentication token has expired.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_TOKEN",
            "Invalid authentication token.",
        ) from exc


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "NOT_AUTHENTICATED",
            "Missing Bearer authentication token.",
        )
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Missing token subject.")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "USER_NOT_FOUND", "User no longer exists.")
    return user


def require_roles(*allowed_roles: str) -> Callable:
    async def _role_guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AppError(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN_ROLE",
                f"Role '{current_user.role}' is not permitted for this operation.",
            )
        return current_user

    return _role_guard


def resolve_target_user_id(
    current_user: User,
    requested_user_id: Optional[str],
    allow_flight_surgeon: bool = True,
) -> str:
    """
    Central IDOR guard:
    - ASTRONAUT may only access their own user_id.
    - CMO (and FLIGHT_SURGEON when allow_flight_surgeon=True) may access any crew user_id.
    """
    if requested_user_id is None or requested_user_id == current_user.id:
        return current_user.id

    allowed_elevated = {"CMO", "FLIGHT_SURGEON"} if allow_flight_surgeon else {"CMO"}
    if current_user.role not in allowed_elevated:
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN_OWNERSHIP",
            "Astronauts may only access or mutate their own medical records.",
        )
    return requested_user_id


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and (now - bucket[0]) > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise AppError(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "RATE_LIMIT_EXCEEDED",
                "Too many requests. Please wait before retrying.",
            )
        bucket.append(now)


login_rate_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)
consultation_rate_limiter = SlidingWindowRateLimiter(max_requests=6, window_seconds=60)
```

---

## 5. `backend/app/crud.py`

```python
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
```

---

## 6. `backend/app/simulator.py`

```python
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
```

---

## 7. `backend/app/routers/auth_router.py`

```python
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    AppError,
    create_access_token,
    get_current_user,
    login_rate_limiter,
    verify_password,
)
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserProfileResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    login_rate_limiter.check(f"login:{client_ip}")

    user = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "Invalid email or password.",
        )

    token = create_access_token(user_id=user.id, role=user.role)
    return LoginResponse(
        access_token=token,
        user=UserProfileResponse.model_validate(user, from_attributes=True),
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user, from_attributes=True)
```

---

## 8. `backend/app/routers/telemetry_router.py`

```python
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
```

---

## 9. `backend/app/routers/clinical_router.py`

```python
from datetime import datetime, timezone
import json
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    AppError,
    consultation_rate_limiter,
    get_current_user,
    resolve_target_user_id,
)
from app.crud import compute_canonical_hmac
from app.database import get_db
from app.models import (
    AnomalyAlert,
    DiagnosticConsultation,
    MissionSyncReport,
    TelemetryReading,
    TraumaProtocol,
    TreatmentTask,
    User,
)
from app.rag_engine import CitationSchema, MaterializedTaskSchema, RAGService, get_rag_engine
from app.schemas import (
    ConsultationCreateRequest,
    ConsultationResponse,
    SyncReportCreateRequest,
    SyncReportResponse,
    SyncReportVerifyResponse,
    TraumaProtocolResponse,
)

router = APIRouter(tags=["Clinical RAG, Tasks, Trauma & Sync"])


@router.post("/consultations", response_model=ConsultationResponse, status_code=201)
async def create_consultation(
    payload: ConsultationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag: RAGService = Depends(get_rag_engine),
) -> ConsultationResponse:
    consultation_rate_limiter.check(f"consult:{current_user.id}")
    target_uid = resolve_target_user_id(
        current_user, payload.target_user_id, allow_flight_surgeon=False
    )

    rag_result = await rag.diagnose(
        body_region=payload.body_region,
        symptom_query=payload.symptom_query,
        voice_stress_score=payload.voice_stress_score,
    )

    now = datetime.now(timezone.utc)
    consultation_id = str(uuid.uuid4())
    record = DiagnosticConsultation(
        id=consultation_id,
        user_id=target_uid,
        body_region=payload.body_region,
        symptom_query=payload.symptom_query,
        voice_stress_score=payload.voice_stress_score,
        ai_diagnosis=rag_result.ai_diagnosis,
        confidence_score=rag_result.confidence_score,
        execution_mode=rag_result.execution_mode,
        citations_json=json.dumps([c.model_dump() for c in rag_result.citations]),
        created_at=now,
    )
    db.add(record)

    for task_item in rag_result.generated_tasks:
        db.add(
            TreatmentTask(
                id=task_item.id,
                user_id=target_uid,
                consultation_id=consultation_id,
                countermeasure_id=task_item.countermeasure_id,
                task_type=task_item.task_type,
                title=task_item.title,
                instructions=task_item.instructions,
                scheduled_for=task_item.scheduled_for,
                is_completed=False,
            )
        )

    await db.commit()

    return ConsultationResponse(
        id=consultation_id,
        user_id=target_uid,
        body_region=payload.body_region,
        symptom_query=payload.symptom_query,
        voice_stress_score=payload.voice_stress_score,
        ai_diagnosis=rag_result.ai_diagnosis,
        confidence_score=rag_result.confidence_score,
        execution_mode=rag_result.execution_mode,
        citations=rag_result.citations,
        generated_tasks=rag_result.generated_tasks,
        created_at=now,
    )


@router.get("/consultations", response_model=List[ConsultationResponse])
async def list_consultations(
    user_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ConsultationResponse]:
    target_uid = resolve_target_user_id(current_user, user_id, allow_flight_surgeon=True)
    rows = (
        await db.execute(
            select(DiagnosticConsultation)
            .where(DiagnosticConsultation.user_id == target_uid)
            .order_by(DiagnosticConsultation.created_at.desc())
        )
    ).scalars().all()

    results: List[ConsultationResponse] = []
    for row in rows:
        tasks = (
            await db.execute(
                select(TreatmentTask).where(TreatmentTask.consultation_id == row.id)
            )
        ).scalars().all()
        results.append(
            ConsultationResponse(
                id=row.id,
                user_id=row.user_id,
                body_region=row.body_region,
                symptom_query=row.symptom_query,
                voice_stress_score=row.voice_stress_score,
                ai_diagnosis=row.ai_diagnosis,
                confidence_score=row.confidence_score,
                execution_mode=row.execution_mode,
                citations=[CitationSchema(**c) for c in json.loads(row.citations_json)],
                generated_tasks=[
                    MaterializedTaskSchema.model_validate(t, from_attributes=True)
                    for t in tasks
                ],
                created_at=row.created_at,
            )
        )
    return results


@router.get("/tasks", response_model=List[MaterializedTaskSchema])
async def list_tasks(
    user_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaterializedTaskSchema]:
    target_uid = resolve_target_user_id(current_user, user_id, allow_flight_surgeon=True)
    rows = (
        await db.execute(
            select(TreatmentTask)
            .where(TreatmentTask.user_id == target_uid)
            .order_by(TreatmentTask.scheduled_for.asc())
        )
    ).scalars().all()
    return [MaterializedTaskSchema.model_validate(r, from_attributes=True) for r in rows]


@router.patch("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    task = (
        await db.execute(select(TreatmentTask).where(TreatmentTask.id == task_id))
    ).scalar_one_or_none()
    if task is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "TASK_NOT_FOUND", "Task not found.")

    resolve_target_user_id(current_user, task.user_id, allow_flight_surgeon=False)
    task.is_completed = True
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "id": task.id,
        "is_completed": True,
        "completed_at": task.completed_at.isoformat(),
    }


@router.get("/trauma-protocols", response_model=List[TraumaProtocolResponse])
async def get_trauma_protocols(
    db: AsyncSession = Depends(get_db),
) -> List[TraumaProtocolResponse]:
    """Public zero-auth endpoint so emergency overrides never fail on expired tokens."""
    rows = (await db.execute(select(TraumaProtocol))).scalars().all()
    return [
        TraumaProtocolResponse(
            id=r.id,
            code_name=r.code_name,
            title=r.title,
            body_region=r.body_region,
            steps=json.loads(r.steps_json),
            nasa_reference=r.nasa_reference,
        )
        for r in rows
    ]


@router.post("/reports/sync", response_model=SyncReportResponse, status_code=201)
async def create_sync_report(
    payload: SyncReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncReportResponse:
    target_uid = resolve_target_user_id(
        current_user, payload.target_user_id, allow_flight_surgeon=False
    )
    target_user = (
        await db.execute(select(User).where(User.id == target_uid))
    ).scalar_one_or_none()
    if target_user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "Target user not found.")

    tel_count = (
        await db.execute(
            select(func.count(TelemetryReading.id)).where(TelemetryReading.user_id == target_uid)
        )
    ).scalar_one()
    alert_count = (
        await db.execute(
            select(func.count(AnomalyAlert.id)).where(
                AnomalyAlert.user_id == target_uid,
                AnomalyAlert.is_acknowledged.is_(False),
            )
        )
    ).scalar_one()
    consult_count = (
        await db.execute(
            select(func.count(DiagnosticConsultation.id)).where(
                DiagnosticConsultation.user_id == target_uid
            )
        )
    ).scalar_one()
    pending_tasks = (
        await db.execute(
            select(func.count(TreatmentTask.id)).where(
                TreatmentTask.user_id == target_uid,
                TreatmentTask.is_completed.is_(False),
            )
        )
    ).scalar_one()

    now = datetime.now(timezone.utc)
    summary_dict = {
        "astronaut_id": target_user.id,
        "astronaut_name": target_user.full_name,
        "telemetry_samples_count": tel_count,
        "active_anomalies_count": alert_count,
        "consultations_count": consult_count,
        "pending_tasks_count": pending_tasks,
        "snapshot_utc": now.isoformat(),
    }
    canonical_json, hmac_digest = compute_canonical_hmac(summary_dict)

    report_id = str(uuid.uuid4())
    report_row = MissionSyncReport(
        id=report_id,
        user_id=target_uid,
        generated_by=current_user.id,
        integrity_hmac=hmac_digest,
        summary_json=canonical_json,
        sync_status="QUEUED",
        created_at=now,
    )
    db.add(report_row)
    await db.commit()

    return SyncReportResponse(
        id=report_id,
        user_id=target_uid,
        generated_by=current_user.id,
        integrity_hmac=hmac_digest,
        summary=summary_dict,
        sync_status="QUEUED",
        created_at=now,
    )


@router.get("/reports", response_model=List[SyncReportResponse])
async def list_sync_reports(
    user_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SyncReportResponse]:
    stmt = select(MissionSyncReport).order_by(MissionSyncReport.created_at.desc())
    if current_user.role == "ASTRONAUT":
        if user_id and user_id != current_user.id:
            raise AppError(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN_OWNERSHIP",
                "Astronauts may only view their own sync reports.",
            )
        stmt = stmt.where(MissionSyncReport.user_id == current_user.id)
    elif user_id:
        stmt = stmt.where(MissionSyncReport.user_id == user_id)

    rows = (await db.execute(stmt)).scalars().all()
    return [
        SyncReportResponse(
            id=r.id,
            user_id=r.user_id,
            generated_by=r.generated_by,
            integrity_hmac=r.integrity_hmac,
            summary=json.loads(r.summary_json),
            sync_status=r.sync_status,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/reports/{report_id}/verify", response_model=SyncReportVerifyResponse)
async def verify_sync_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncReportVerifyResponse:
    row = (
        await db.execute(select(MissionSyncReport).where(MissionSyncReport.id == report_id))
    ).scalar_one_or_none()
    if row is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "REPORT_NOT_FOUND", "Sync report not found.")

    resolve_target_user_id(current_user, row.user_id, allow_flight_surgeon=True)
    summary_dict = json.loads(row.summary_json)
    _, computed_hmac = compute_canonical_hmac(summary_dict)

    return SyncReportVerifyResponse(
        report_id=row.id,
        verified=(computed_hmac == row.integrity_hmac),
        stored_hmac=row.integrity_hmac,
        computed_hmac=computed_hmac,
    )
```

---

## 10. `backend/app/main.py`

```python
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.auth import AppError, decode_access_token
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import User
from app.rag_engine import GeminiProvider, RAGService, get_rag_engine
from app.routers import auth_router, clinical_router, telemetry_router
from app.simulator import simulator_hub

app = FastAPI(title=settings.PROJECT_NAME, version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc.errors()),
            }
        },
    )


@app.get("/api/v1/health")
async def health_check(
    live_check: bool = Query(default=False),
    rag: RAGService = Depends(get_rag_engine),
) -> dict:
    live_ok = False
    model_detail = "offline_rules_only"
    if isinstance(rag.provider, GeminiProvider):
        model_detail = settings.GEMINI_GENERATION_MODEL
        if live_check:
            live_ok, model_detail = await rag.provider.ping_live_model()
        else:
            live_ok = True

    return {
        "status": "ok",
        "ai_provider_mode": rag.active_mode_name,
        "live_model_verified": live_ok,
        "model_detail": model_detail,
        "kb_chunks_loaded": len(rag.chunks),
    }


@app.websocket("/ws/telemetry")
async def telemetry_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    user_id: Optional[str] = Query(default=None),
) -> None:
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_access_token(token)
        caller_id = payload.get("sub")
        caller_role = payload.get("role", "ASTRONAUT")
    except Exception:
        await websocket.close(code=1008)
        return

    target_uid = user_id or caller_id
    if caller_role == "ASTRONAUT" and target_uid != caller_id:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    simulator_hub.register_ws(target_uid, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        simulator_hub.unregister_ws(target_uid, websocket)


app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(telemetry_router.router, prefix="/api/v1")
app.include_router(clinical_router.router, prefix="/api/v1")
```