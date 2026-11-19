import re
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    AppError,
    create_access_token,
    get_current_user,
    hash_password,
    login_rate_limiter,
    verify_password,
)
from app.database import get_db
from app.models import TelemetryReading, User
from app.schemas import (
    CreateUserRequest,
    LoginRequest,
    LoginResponse,
    SwitchUserRequest,
    UserProfileResponse,
)

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


@router.get("/users", response_model=List[UserProfileResponse])
async def list_crew(db: AsyncSession = Depends(get_db)) -> List[UserProfileResponse]:
    result = await db.execute(select(User).order_by(User.created_at.asc()))
    users = result.scalars().all()
    return [UserProfileResponse.model_validate(u, from_attributes=True) for u in users]


@router.post("/users", response_model=LoginResponse, status_code=201)
async def create_astronaut(
    payload: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    email = payload.email
    if not email:
        clean_name = re.sub(r"[^a-zA-Z0-9]+", ".", payload.full_name.strip()).strip(".").lower()
        if not clean_name:
            clean_name = "astronaut"
        candidate_email = f"{clean_name}@nasa.gov"
        existing = (await db.execute(select(User).where(User.email == candidate_email))).scalar_one_or_none()
        if existing:
            candidate_email = f"{clean_name}.{str(uuid.uuid4())[:4]}@nasa.gov"
        email = candidate_email

    existing_user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing_user is not None:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "EMAIL_EXISTS",
            f"An astronaut with email {email} already exists.",
        )

    now = datetime.now(timezone.utc)
    new_id = str(uuid.uuid4())
    pw = payload.password or "MarsMission2026!"
    hashed_pw = hash_password(pw)

    new_user = User(
        id=new_id,
        email=email,
        password_hash=hashed_pw,
        full_name=payload.full_name.strip(),
        role=payload.role,
        baseline_hr_bpm=payload.baseline_hr_bpm,
        baseline_spo2_pct=payload.baseline_spo2_pct,
        baseline_sys_bp=payload.baseline_sys_bp,
        baseline_dia_bp=payload.baseline_dia_bp,
        created_at=now,
    )
    db.add(new_user)
    await db.flush()

    # Seed initial nominal baseline telemetry reading so graphs and indicators stream immediately
    initial_reading = TelemetryReading(
        id=str(uuid.uuid4()),
        user_id=new_user.id,
        recorded_at=now,
        heart_rate_bpm=new_user.baseline_hr_bpm,
        spo2_pct=new_user.baseline_spo2_pct,
        systolic_bp_mmhg=new_user.baseline_sys_bp,
        diastolic_bp_mmhg=new_user.baseline_dia_bp,
        core_temp_c=36.8,
        radiation_msv=0.32,
        sleep_score=85,
        eeg_fatigue_index=0.20,
        status_level="GREEN",
    )
    db.add(initial_reading)
    await db.commit()

    token = create_access_token(user_id=new_user.id, role=new_user.role)
    return LoginResponse(
        access_token=token,
        user=UserProfileResponse.model_validate(new_user, from_attributes=True),
    )


@router.post("/switch", response_model=LoginResponse)
async def switch_user(
    payload: SwitchUserRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    user = (
        await db.execute(select(User).where(User.id == payload.user_id))
    ).scalar_one_or_none()
    if user is None:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "USER_NOT_FOUND",
            "Astronaut not found in crew manifest.",
        )

    token = create_access_token(user_id=user.id, role=user.role)
    return LoginResponse(
        access_token=token,
        user=UserProfileResponse.model_validate(user, from_attributes=True),
    )
