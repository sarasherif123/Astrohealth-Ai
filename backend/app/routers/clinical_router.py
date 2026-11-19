from datetime import datetime, timedelta, timezone
import json
import re
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
from app.crud import compute_canonical_hmac, ingest_telemetry_packet
from app.database import get_db
from app.emergency_scenarios import EMERGENCY_SCENARIOS
from app.models import (
    AnomalyAlert,
    DiagnosticConsultation,
    MissionSyncReport,
    TelemetryReading,
    TraumaProtocol,
    TreatmentTask,
    User,
)
from app.rag_engine import CitationSchema, GeminiProvider, MaterializedTaskSchema, RAGService, get_rag_engine
from app.schemas import (
    AlertResponse,
    ConsultationCreateRequest,
    ConsultationResponse,
    EmergencySimulateRequest,
    EmergencySimulateResponse,
    MedicalChatRequest,
    MedicalChatResponse,
    SyncReportCreateRequest,
    SyncReportResponse,
    SyncReportVerifyResponse,
    TelemetryReadingResponse,
    TraumaProtocolResponse,
)
from app.simulator import simulator_hub

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


@router.post("/reports/{report_id}/tamper-demo")
async def tamper_sync_report_demo(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    row = (
        await db.execute(select(MissionSyncReport).where(MissionSyncReport.id == report_id))
    ).scalar_one_or_none()
    if row is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "REPORT_NOT_FOUND", "Sync report not found.")

    resolve_target_user_id(current_user, row.user_id, allow_flight_surgeon=True)
    summary_dict = json.loads(row.summary_json)
    summary_dict["notes"] = f"[TAMPERED] {summary_dict.get('notes', '')}"
    row.summary_json = json.dumps(summary_dict)
    await db.commit()

    return {"report_id": row.id, "tampered": True}


@router.post("/clinical/chat", response_model=MedicalChatResponse)
async def clinical_chat(
    payload: MedicalChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag: RAGService = Depends(get_rag_engine),
) -> MedicalChatResponse:
    consultation_rate_limiter.check(f"chat:{current_user.id}")
    target_uid = resolve_target_user_id(
        current_user, payload.target_user_id, allow_flight_surgeon=False
    )

    chat_result = await rag.chat(
        message=payload.message,
        history=[h.model_dump() for h in payload.history],
        body_region=payload.body_region,
    )

    # Log consultation to DB so history is preserved in astronaut clinical profile
    now = datetime.now(timezone.utc)
    consultation_id = str(uuid.uuid4())
    record = DiagnosticConsultation(
        id=consultation_id,
        user_id=target_uid,
        body_region=chat_result.get("body_region", payload.body_region or "SYSTEMIC"),
        symptom_query=payload.message,
        voice_stress_score=None,
        ai_diagnosis=chat_result.get("reply", ""),
        confidence_score=0.85 if chat_result.get("execution_mode") == "ONLINE_GEMINI" else 0.70,
        execution_mode=chat_result.get("execution_mode", "OFFLINE_FALLBACK"),
        citations_json=json.dumps([c.model_dump() if hasattr(c, "model_dump") else c for c in chat_result.get("citations", [])]),
        created_at=now,
    )
    db.add(record)
    await db.commit()

    return MedicalChatResponse(
        reply=chat_result.get("reply", ""),
        severity=chat_result.get("severity", "NOMINAL"),
        citations=chat_result.get("citations", []),
        follow_up_questions=chat_result.get("follow_up_questions", []),
        body_region=chat_result.get("body_region", payload.body_region or "SYSTEMIC"),
        execution_mode=chat_result.get("execution_mode", "OFFLINE_FALLBACK"),
        suggested_actions=chat_result.get("suggested_actions", []),
    )


@router.get("/emergency/scenarios")
async def list_emergency_scenarios() -> List[dict]:
    return [
        {
            "scenario_id": v["scenario_id"],
            "title": v["title"],
            "body_region": v["body_region"],
            "severity": v["severity"],
            "default_symptoms": v["default_symptoms"],
            "possible_concerns": v["possible_concerns"],
            "nasa_reference": v["nasa_reference"],
        }
        for v in EMERGENCY_SCENARIOS.values()
    ]


@router.post("/emergency/simulate", response_model=EmergencySimulateResponse, status_code=201)
async def simulate_emergency(
    payload: EmergencySimulateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag: RAGService = Depends(get_rag_engine),
) -> EmergencySimulateResponse:
    target_uid = resolve_target_user_id(
        current_user, payload.target_user_id, allow_flight_surgeon=False
    )
    target_user = (
        await db.execute(select(User).where(User.id == target_uid))
    ).scalar_one_or_none()
    if target_user is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "Target astronaut not found.")

    scen = EMERGENCY_SCENARIOS.get(payload.scenario_id)
    if scen is None:
        raise AppError(status.HTTP_400_BAD_REQUEST, "INVALID_SCENARIO", f"Scenario {payload.scenario_id} not recognized.")

    now = datetime.now(timezone.utc)
    simulation_id = str(uuid.uuid4())

    # 1. Build combined query first (needed for consultation record later)
    custom_notes = (f" Astronaut notes: {payload.custom_symptoms}" if payload.custom_symptoms else "")
    combined_query = f"{scen['default_symptoms']}{custom_notes}"

    # 2. Telemetry injection & real-time broadcast if requested
    tel_status = "GREEN"
    alert_count = 0
    if payload.trigger_telemetry and "telemetry_metrics" in scen:
        metrics = scen["telemetry_metrics"]
        reading_row, alert_rows, _ = await ingest_telemetry_packet(
            db,
            target_user,
            recorded_at=now,
            **metrics,
        )
        tel_status = reading_row.status_level
        alert_count = len(alert_rows)
        reading_resp = TelemetryReadingResponse.model_validate(reading_row, from_attributes=True)
        alerts_resp = [AlertResponse.model_validate(a, from_attributes=True) for a in alert_rows]
        await simulator_hub.broadcast_frame(target_uid, reading_resp, alerts_resp)

    # 3. Grounded AI Assessment (citations)

    # Retrieve top chunks for citations
    chunks, _, _ = await rag.retrieve_top_chunks(combined_query, scen["body_region"], top_k=2)
    citations: List[CitationSchema] = []
    for ch in chunks:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", ch["content"].strip()) if len(s.strip()) > 20]
        snippet = sentences[0] if sentences else ch["content"][:220].strip()
        citations.append(CitationSchema(
            document_title=ch["document_title"],
            page_number=int(ch["page_number"]),
            snippet=snippet,
        ))
    if not citations:
        citations.append(CitationSchema(
            document_title=scen["nasa_reference"],
            page_number=1,
            snippet=scen["default_symptoms"],
        ))

    assessment = (
        f"[Emergency Medical Assessment — {scen['title']}]\n"
        f"Grounded in {scen['nasa_reference']}. Astronaut {target_user.full_name} exhibits clinical indicators of "
        f"{scen['title'].lower()}. Reported symptoms: {combined_query}. "
        f"Baseline vitals (HR {target_user.baseline_hr_bpm} bpm, SpO2 {target_user.baseline_spo2_pct}%) compared to current emergency telemetry."
    )

    # 3. Save consultation record FIRST (tasks FK reference it)
    consultation = DiagnosticConsultation(
        id=simulation_id,
        user_id=target_uid,
        body_region=scen["body_region"],
        symptom_query=f"[EMERGENCY SIMULATION: {scen['title']}] {combined_query}",
        voice_stress_score=0.88,
        ai_diagnosis=assessment,
        confidence_score=0.95,
        execution_mode="ONLINE_GEMINI" if isinstance(rag.provider, GeminiProvider) else "OFFLINE_FALLBACK",
        citations_json=json.dumps([c.model_dump() for c in citations]),
        created_at=now,
    )
    db.add(consultation)
    await db.flush()  # write consultation so FK constraint is satisfied

    # 4. Materialize treatment tasks (FK → consultation)
    gen_tasks: List[MaterializedTaskSchema] = []
    for cid in scen.get("countermeasure_ids", []):
        if cid in rag.catalog:
            entry = rag.catalog[cid]
            t_id = str(uuid.uuid4())
            offset = int(entry.get("scheduled_offset_hours", 0))
            task_obj = TreatmentTask(
                id=t_id,
                user_id=target_uid,
                consultation_id=simulation_id,
                countermeasure_id=cid,
                task_type=entry["task_type"],
                title=f"[Emergency] {entry['title']}",
                instructions=entry["instructions"],
                scheduled_for=now + timedelta(hours=offset),
                is_completed=False,
            )
            db.add(task_obj)
            gen_tasks.append(
                MaterializedTaskSchema(
                    id=t_id,
                    countermeasure_id=cid,
                    task_type=entry["task_type"],
                    title=f"[Emergency] {entry['title']}",
                    instructions=entry["instructions"],
                    scheduled_for=now + timedelta(hours=offset),
                    is_completed=False,
                )
            )

    await db.commit()

    reported_symptoms = [s.strip() for s in scen["default_symptoms"].split(",") if s.strip()]
    if payload.custom_symptoms:
        reported_symptoms.append(f"Crew Note: {payload.custom_symptoms}")

    return EmergencySimulateResponse(
        simulation_id=simulation_id,
        target_user_id=target_uid,
        scenario_id=scen["scenario_id"],
        scenario_title=scen["title"],
        severity=scen["severity"],
        medical_assessment=assessment,
        reported_symptoms=reported_symptoms,
        possible_concerns=scen["possible_concerns"],
        immediate_actions=scen["immediate_actions"],
        monitoring_instructions=scen["monitoring_instructions"],
        ground_medical_support=scen["ground_medical_support"],
        warnings=scen["warnings"],
        follow_up_questions=scen["follow_up_questions"],
        citations=citations,
        generated_tasks=gen_tasks,
        telemetry_status=tel_status,
        alerts_triggered=alert_count,
        created_at=now,
    )


