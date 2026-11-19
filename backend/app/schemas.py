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


class CreateUserRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: RoleType = "ASTRONAUT"
    password: Optional[str] = "MarsMission2026!"
    baseline_hr_bpm: int = Field(default=64, ge=30, le=220)
    baseline_spo2_pct: float = Field(default=98.5, ge=70.0, le=100.0)
    baseline_sys_bp: int = Field(default=118, ge=60, le=250)
    baseline_dia_bp: int = Field(default=75, ge=40, le=150)


class SwitchUserRequest(BaseModel):
    user_id: str


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


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class MedicalChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[ChatMessage] = Field(default_factory=list)
    target_user_id: Optional[str] = None
    body_region: Optional[BodyRegionType] = None


class MedicalChatResponse(BaseModel):
    reply: str
    severity: Literal["NOMINAL", "MODERATE", "HIGH", "CRITICAL"] = "NOMINAL"
    citations: List[CitationSchema] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    body_region: BodyRegionType = "SYSTEMIC"
    execution_mode: ExecutionModeType = "ONLINE_GEMINI"
    suggested_actions: List[str] = Field(default_factory=list)


class EmergencySimulateRequest(BaseModel):
    target_user_id: Optional[str] = None
    scenario_id: str = Field(..., description="Scenario identifier e.g. CHEST_PAIN, HYPOXIA, etc.")
    custom_symptoms: Optional[str] = None
    trigger_telemetry: bool = True


class EmergencySimulateResponse(BaseModel):
    simulation_id: str
    target_user_id: str
    scenario_id: str
    scenario_title: str
    severity: Literal["NOMINAL", "MODERATE", "HIGH", "CRITICAL"]
    medical_assessment: str
    reported_symptoms: List[str]
    possible_concerns: List[str]
    immediate_actions: List[str]
    monitoring_instructions: List[str]
    ground_medical_support: str
    warnings: List[str]
    follow_up_questions: List[str]
    citations: List[CitationSchema]
    generated_tasks: List[MaterializedTaskSchema]
    telemetry_status: StatusLevelType
    alerts_triggered: int
    created_at: datetime

