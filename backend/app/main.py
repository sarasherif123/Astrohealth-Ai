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
