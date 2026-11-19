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
